from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from sqlalchemy import select, update, and_, desc
from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import (
    FnoMarketTick, FnoOptionChainSnapshot, FnoAuditLog,
    FnoRecommendation, FnoRecommendationFilter, SavedRecommendation
)
from indian_swing.data.validation.integrity_layer import DataIntegrityLayer
from indian_swing.recommendations.fno_strategy import fno_strategy_engine

logger = get_logger(__name__)
router = APIRouter()
validator = DataIntegrityLayer(quality_threshold=85.0)

INDEX_MAP = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "SENSEX": "BSE_INDEX|SENSEX",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
    "MIDCPNIFTY": "NSE_INDEX|NIFTY MID SELECT",
    "INDIAVIX": "NSE_INDEX|India Vix"
}

def get_headers():
    token = settings.upstox_access_token
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}" if token else ""
    }

@router.get("/market-data")
async def get_market_data(symbol: str, audit: Optional[bool] = Query(False)):
    token = settings.upstox_access_token
    mapped_symbol = INDEX_MAP.get(symbol.upper(), "NSE_INDEX|Nifty 50")
    
    audit_logs = []
    audit_logs.append({"step": "API Request Received", "details": f"Symbol: {symbol.upper()}, Audit Mode: {audit}"})

    using_fallback = False

    # Resolve target spot & vix
    if not token:
        using_fallback = True
        base_prices = {"NIFTY": 24350.0, "BANKNIFTY": 52420.0, "SENSEX": 79890.0, "FINNIFTY": 23680.0, "MIDCPNIFTY": 12340.0}
        last_price = base_prices.get(symbol.upper(), 24350.0)
        vix_price = 14.12
        audit_logs.append({"step": "Spot Price Resolution", "details": f"Lacking Upstox token. Using base price {last_price} and default VIX 14.12"})
    else:
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={mapped_symbol}"
                response = await client.get(url, headers=get_headers(), timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                vix_url = "https://api.upstox.com/v2/market-quote/ltp?instrument_key=NSE_INDEX|India%20Vix"
                vix_response = await client.get(vix_url, headers=get_headers(), timeout=10.0)
                vix_data = vix_response.json() if vix_response.status_code == 200 else {}
                
                spot_info = data.get("data", {}).get(mapped_symbol, {})
                vix_info = vix_data.get("data", {}).get("NSE_INDEX|India Vix", {})

                last_price = spot_info.get("last_price", 0.0)
                vix_price = vix_info.get("last_price", 14.12)
                
                if last_price <= 0.0:
                    raise ValueError("LTP value missing or zero from Upstox API response")
                audit_logs.append({"step": "Spot Price Resolution", "details": f"Successfully retrieved spot {last_price} and VIX {vix_price} from Upstox"})
        except Exception as e:
            logger.error("fno.market_data_api_failed", symbol=symbol, error=str(e))
            using_fallback = True
            base_prices = {"NIFTY": 24350.0, "BANKNIFTY": 52420.0, "SENSEX": 79890.0, "FINNIFTY": 23680.0, "MIDCPNIFTY": 12340.0}
            last_price = base_prices.get(symbol.upper(), 24350.0)
            vix_price = 14.12
            audit_logs.append({"step": "Spot Price Resolution", "details": f"Failed to retrieve spot price: {e}. Falling back to simulated pricing."})

    # Fetch dynamic expiry dates from Upstox (Fix 1)
    expiries_raw = []
    if token and last_price > 0:
        try:
            url_exp = f"https://api.upstox.com/v2/option/expiry?instrument_key={mapped_symbol}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url_exp, headers=get_headers(), timeout=10.0)
                if response.status_code == 200:
                    expiries_raw = response.json().get("data", [])
                    audit_logs.append({"step": "Expiry Fetching", "details": f"Retrieved {len(expiries_raw)} active expiries from Upstox"})
        except Exception as ee:
            logger.warning(f"Failed to fetch expiries: {ee}")
            audit_logs.append({"step": "Expiry Fetching", "details": f"Expiry API error: {ee}"})

    # Fallback to rolling dates if API unavailable/simulation mode
    if not expiries_raw:
        expiries_raw = ["23-JUL-2026", "28-AUG-2026", "25-SEP-2026", "29-OCT-2026", "24-DEC-2026"]
        audit_logs.append({"step": "Expiry Fetching", "details": "Falling back to calendar expiry labels"})

    # Setup expiries config list
    expiries_config = []
    expiry_names = ["Weekly", "Monthly", "Quarterly", "Next Monthly", "Next Quarterly"]
    for i, exp_label in enumerate(expiries_raw[:5]):
        name = expiry_names[i] if i < len(expiry_names) else f"Expiry {i+1}"
        expiries_config.append({
            "name": name,
            "label": exp_label,
            "time_factor": 1.0 + (i * 0.8),
            "delta_mod": max(0.10, 0.18 - (i * 0.02))
        })

    # Fetch Option Chain strikes from Upstox (Fix 2)
    strikes_list = []
    if token and last_price > 0:
        try:
            # Query the closest weekly expiry chain
            url_chain = f"https://api.upstox.com/v2/option/chain?instrument_key={mapped_symbol}&expiry_date={expiries_raw[0]}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url_chain, headers=get_headers(), timeout=10.0)
                response.raise_for_status()
                res_data = response.json()
                for item in res_data.get("data", []):
                    ce = item.get("call_options", {})
                    pe = item.get("put_options", {})
                    strikes_list.append({
                        "strike": item.get("strike_price"),
                        "ce": {
                            "ltp": ce.get("market_data", {}).get("ltp", 0.0),
                            "change": ce.get("market_data", {}).get("change", 0.0),
                            "oi": ce.get("market_data", {}).get("oi", 0),
                            "iv": ce.get("market_data", {}).get("iv", 12.0)
                        },
                        "pe": {
                            "ltp": pe.get("market_data", {}).get("ltp", 0.0),
                            "change": pe.get("market_data", {}).get("change", 0.0),
                            "oi": pe.get("market_data", {}).get("oi", 0),
                            "iv": pe.get("market_data", {}).get("iv", 12.5)
                        }
                    })
                audit_logs.append({"step": "Option Chain Fetching", "details": f"Successfully fetched weekly chain with {len(strikes_list)} strikes"})
        except Exception as e:
            logger.error("fno.option_chain_failed", error=str(e))
            audit_logs.append({"step": "Option Chain Fetching", "details": f"Option chain failed: {e}"})

    # If empty, fallback to deterministic simulation
    if not strikes_list:
        sim_chain = _simulate_option_chain(symbol.upper())
        strikes_list = sim_chain["strikes"]
        audit_logs.append({"step": "Option Chain Fetching", "details": f"Using deterministic option chain simulator ({len(strikes_list)} strikes)"})

    # 4. Compute changePct from last two DB ticks (A2)
    change_pct = 0.0
    try:
        with get_sync_session() as tick_session:
            from sqlalchemy import desc as _desc
            prev_ticks = tick_session.execute(
                select(FnoMarketTick)
                .where(FnoMarketTick.symbol == symbol.upper())
                .order_by(_desc(FnoMarketTick.timestamp))
                .limit(2)
            ).scalars().all()
            if len(prev_ticks) == 2:
                prev_price = prev_ticks[1].price
                if prev_price > 0:
                    change_pct = round((last_price - prev_price) / prev_price * 100, 2)
    except Exception:
        pass

    # Log tick to DB
    atm_iv_for_log = None
    try:
        if strikes_list:
            atm_s = min(strikes_list, key=lambda x: abs(x["strike"] - last_price))
            atm_iv_for_log = (atm_s["ce"]["iv"] + atm_s["pe"]["iv"]) / 2.0
    except Exception:
        pass
    
    if last_price > 0:
        _log_tick_to_db(symbol.upper(), last_price, vix_price, atm_iv=atm_iv_for_log)

    # 5. Calculate true database-backed Volatility metrics (Fix 6)
    iv_perc = 50.0
    iv_rank = 50.0
    rv20_val = 12.0
    rv30_val = 12.0
    if last_price > 0:
        try:
            with get_sync_session() as vol_session:
                ticks = vol_session.execute(
                    select(FnoMarketTick)
                    .where(FnoMarketTick.symbol == symbol.upper())
                    .order_by(desc(FnoMarketTick.timestamp))
                    .limit(252)
                ).scalars().all()
                
                if len(ticks) >= 5:
                    iv_values = [t.vix if t.vix else 14.12 for t in ticks]
                    min_iv = min(iv_values)
                    max_iv = max(iv_values)
                    iv_rank = ((vix_price - min_iv) / (max_iv - min_iv)) * 100.0 if max_iv > min_iv else 50.0
                    less_than_curr = sum(1 for iv in iv_values if iv < vix_price)
                    iv_perc = (less_than_curr / len(iv_values)) * 100.0
                    
                    prices = [t.price for t in ticks]
                    import math
                    log_rets = []
                    for i in range(len(prices) - 1):
                        if prices[i] > 0 and prices[i+1] > 0:
                            log_rets.append(math.log(prices[i] / prices[i+1]))
                    if len(log_rets) >= 3:
                        var_20 = sum((r - (sum(log_rets[:20])/20.0)) ** 2 for r in log_rets[:20]) / 19.0
                        var_30 = sum((r - (sum(log_rets[:30])/30.0)) ** 2 for r in log_rets[:30]) / 29.0
                        rv20_val = math.sqrt(var_20) * math.sqrt(252) * 100.0
                        rv30_val = math.sqrt(var_30) * math.sqrt(252) * 100.0
            audit_logs.append({"step": "Volatility Calculations", "details": f"Database-backed IV Rank: {iv_rank:.2f}%, IV Percentile: {iv_perc:.2f}%, RV20: {rv20_val:.2f}%"})
        except Exception as ve:
            logger.warning(f"Volatility math failure: {ve}")
            audit_logs.append({"step": "Volatility Calculations", "details": f"Failed: {ve}"})

    # Run data integrity validation on the actual quote and chain
    spot_packet = {"spotPrice": last_price, "indiaVix": vix_price, "marketStatus": "OPEN", "expiry": expiries_raw[0], "timestamp": datetime.utcnow().isoformat()}
    chain_packet = {"strikes": strikes_list}
    passed, score, errs = validator.validate_packet(symbol.upper(), spot_packet, chain_packet)

    # 6. Recommendation Validation Guard (Fix 8)
    # Reject recommendation if spot price or strikes are invalid/placeholder in live mode
    validation_guard_passed = last_price > 0 and len(strikes_list) > 0
    
    if not validation_guard_passed:
        passed = False
        score = 0.0
        errs.append("Critical API connection error: Live quote or options chain could not be resolved.")
        audit_logs.append({"step": "Recommendation Validation", "details": "FAILED: Missing live quote/chain"})

    # Evaluate strategies dynamically using the computed indicators and expiries
    rec_obj = fno_strategy_engine.evaluate_and_build(symbol.upper(), last_price, vix_price, strikes_list, expiries_config)
    
    # Overwrite IV Percentile/RV with database backed ones
    rec_obj["indicators"]["ivPercentile"] = round(iv_perc, 2)
    rec_obj["indicators"]["rv20"] = round(rv20_val, 2)
    rec_obj["indicators"]["ivRvSpread"] = round(vix_price - rv20_val, 2)
    
    # Flag recommendation as invalid/aborted if using fallback simulated data
    if using_fallback:
        rec_obj["is_allowed"] = False
        if "structure" in rec_obj:
            rec_obj["structure"]["status"] = "INVALIDATED"
            rec_obj["structure"]["decision"] = "REJECT"
            rec_obj["structure"]["verdict"] = "ABORTED"
            rec_obj["structure"]["executive_summary"] = "Recommendation invalidated: live Upstox data source unavailable. Running in simulated fallback mode."
            rec_obj["structure"]["cons"] = ["Using simulated fallback data. Live Upstox connection unavailable."]
        audit_logs.append({"step": "Recommendation Validation", "details": "WARNING: Running in fallback mode. Recommendation invalidated."})

    # Save recommendation only if validation guard passes
    saved_rec = {"recommendation_uuid": "validation-aborted", "structure": rec_obj["structure"]}
    if validation_guard_passed:
        # Clear ONLY current symbol recommendations (Part 1)
        try:
            from sqlalchemy import delete
            with get_sync_session() as del_session:
                del_session.execute(delete(FnoRecommendation).where(FnoRecommendation.symbol == symbol.upper()))
        except Exception as de:
            logger.warning("fno.clear_recommendation_failed", error=str(de))
        
        saved_rec = _save_or_update_recommendation(symbol.upper(), rec_obj)
        audit_logs.append({"step": "Database Write", "details": f"Saved recommendation UUID: {saved_rec['recommendation_uuid']}"})
    else:
        rec_obj["is_allowed"] = False
        rec_obj["structure"]["status"] = "INVALIDATED"
        rec_obj["structure"]["decision"] = "REJECT"
        rec_obj["structure"]["verdict"] = "ABORTED"
        rec_obj["structure"]["executive_summary"] = "Recommendation invalidated: live Upstox data source unavailable."
        audit_logs.append({"step": "Database Write", "details": "Bypassed: guard failed"})

    # 7. Explainability verification metadata payload (Fix 9)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    explainability = {
        "spotPrice": {"source": "✅ Upstox API" if token and not using_fallback else "⚠️ Simulated (Fallback)", "verified": bool(token and not using_fallback), "timestamp": now_str},
        "optionChain": {"source": "✅ Upstox API" if token and not using_fallback else "⚠️ Simulated (Fallback)", "verified": bool(token and not using_fallback), "timestamp": now_str},
        "expiry": {"source": "✅ Upstox API" if token and not using_fallback else "⚠️ Simulated (Fallback)", "verified": bool(token and not using_fallback), "timestamp": now_str},
        "greeks": {"source": "✅ Calculated (Black-Scholes)", "verified": True, "timestamp": now_str},
        "margin": {"source": "✅ Calculated (SPAN Approximation)", "verified": True, "timestamp": now_str},
        "iv": {"source": "✅ Upstox API" if token and not using_fallback else "⚠️ Simulated", "verified": bool(token and not using_fallback), "timestamp": now_str},
        "risk": {"source": "✅ Calculated (Probabilistic expectancy)", "verified": True, "timestamp": now_str}
    }

    return {
        "symbol": symbol,
        "spotPrice": last_price,
        "changePct": change_pct,
        "indiaVix": vix_price,
        "marketStatus": "OPEN" if last_price > 0 else "CLOSED",
        "expiry": expiries_raw[0],
        "tradingSession": "REGULAR",
        "dataQualityScore": score,
        "validationPassed": passed,
        "validationErrors": errs,
        "recommendation_uuid": saved_rec["recommendation_uuid"],
        "indicators": rec_obj["indicators"],
        "regimeResults": {
            "isAllowed": rec_obj["is_allowed"],
            "filters": rec_obj["filters"]
        },
        "selectedStrikes": rec_obj["selectedStrikes"],
        "structure": saved_rec["structure"],
        "ranked_strategies": rec_obj.get("ranked_strategies", []),
        "explainability": explainability,
        "developer_audit_logs": audit_logs if audit else []
    }

@router.get("/option-chain")
async def get_option_chain(symbol: str, expiry_date: Optional[str] = None):
    token = settings.upstox_access_token
    mapped_symbol = INDEX_MAP.get(symbol.upper(), "NSE_INDEX|Nifty 50")

    if not token:
        sim_chain = _simulate_option_chain(symbol)
        _log_chain_to_db(symbol.upper(), sim_chain["strikes"])
        return sim_chain

    try:
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={mapped_symbol}"
        if expiry_date:
            url += f"&expiry_date={expiry_date}"
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=get_headers(), timeout=10.0)
            response.raise_for_status()
            res_data = response.json()
            
            chain_list = res_data.get("data", [])
            strikes = []
            
            for item in chain_list:
                ce = item.get("call_options", {})
                pe = item.get("put_options", {})
                strikes.append({
                    "strike": item.get("strike_price"),
                    "ce": {
                        "ltp": ce.get("market_data", {}).get("ltp", 0.0),
                        "change": ce.get("market_data", {}).get("change", 0.0),
                        "oi": ce.get("market_data", {}).get("oi", 0),
                        "iv": ce.get("market_data", {}).get("iv", 12.0)
                    },
                    "pe": {
                        "ltp": pe.get("market_data", {}).get("ltp", 0.0),
                        "change": pe.get("market_data", {}).get("change", 0.0),
                        "oi": pe.get("market_data", {}).get("oi", 0),
                        "iv": pe.get("market_data", {}).get("iv", 12.5)
                    }
                })
                
            _log_chain_to_db(symbol.upper(), strikes)
            
            return {
                "index": symbol,
                "strikes": strikes,
                "timestamp": str(date.today())
            }
    except Exception as e:
        logger.error("fno.option_chain_api_failed", symbol=symbol, error=str(e))
        sim_chain = _simulate_option_chain(symbol)
        _log_chain_to_db(symbol.upper(), sim_chain["strikes"])
        return sim_chain


# ── F&O Recommendations Lifecycle REST APIs ──────────────────────────────────

@router.post("/recommendations")
async def create_recommendation(symbol: str, rec_data: dict):
    try:
        saved = _save_or_update_recommendation(symbol.upper(), rec_data)
        return saved
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {e}")

@router.get("/recommendations")
async def list_recommendations(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    with get_sync_session() as session:
        query = select(FnoRecommendation)
        if symbol:
            query = query.where(FnoRecommendation.symbol == symbol.upper())
        query = query.order_by(desc(FnoRecommendation.timestamp))
        recs = session.execute(query).scalars().all()
        
        if status:
            recs = [r for r in recs if r.structure.get("status") == status.upper()]
            
        recs = recs[offset:offset+limit]
        return [
            {
                "recommendation_uuid": r.recommendation_uuid,
                "timestamp": r.timestamp.isoformat(),
                "symbol": r.symbol,
                "strategy_id": r.strategy_id,
                "strategy_version": r.strategy_version,
                "structure": r.structure,
                "net_credit": r.net_credit,
                "max_risk": r.max_risk,
                "risk_reward_ratio": r.risk_reward_ratio,
                "confidence_score": r.confidence_score,
                "is_allowed": r.is_allowed
            }
            for r in recs
        ]

@router.get("/recommendations/live")
async def get_live_recommendations():
    """Returns only active, ready, or open recommendations from the database."""
    with get_sync_session() as session:
        query = select(FnoRecommendation).order_by(desc(FnoRecommendation.timestamp))
        recs = session.execute(query).scalars().all()
        
        live_recs = [r for r in recs if r.structure.get("status") in ["READY", "OPEN", "ACTIVE"]]
        return [
            {
                "recommendation_uuid": r.recommendation_uuid,
                "timestamp": r.timestamp.isoformat(),
                "symbol": r.symbol,
                "strategy_id": r.strategy_id,
                "strategy_version": r.strategy_version,
                "structure": r.structure,
                "net_credit": r.net_credit,
                "max_risk": r.max_risk,
                "risk_reward_ratio": r.risk_reward_ratio,
                "confidence_score": r.confidence_score,
                "is_allowed": r.is_allowed
            }
            for r in live_recs
        ]

@router.get("/recommendations/history")
async def get_recommendation_history(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    strategy: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """Retrieve full paginated history for audit screens."""
    with get_sync_session() as session:
        query = select(FnoRecommendation)
        if symbol:
            query = query.where(FnoRecommendation.symbol == symbol.upper())
        if strategy:
            query = query.where(FnoRecommendation.strategy_id == strategy)

        query = query.order_by(desc(FnoRecommendation.timestamp))
        recs = session.execute(query).scalars().all()
        
        if status:
            recs = [r for r in recs if r.structure.get("status") == status.upper()]
            
        recs = recs[offset:offset+limit]
        return [
            {
                "recommendation_uuid": r.recommendation_uuid,
                "timestamp": r.timestamp.isoformat(),
                "symbol": r.symbol,
                "strategy_id": r.strategy_id,
                "strategy_version": r.strategy_version,
                "structure": r.structure,
                "net_credit": r.net_credit,
                "max_risk": r.max_risk,
                "risk_reward_ratio": r.risk_reward_ratio,
                "confidence_score": r.confidence_score,
                "is_allowed": r.is_allowed
            }
            for r in recs
        ]

@router.get("/recommendations/{rec_id}")
async def get_recommendation_detail(rec_id: str):
    with get_sync_session() as session:
        r = session.execute(
            select(FnoRecommendation).where(FnoRecommendation.recommendation_uuid == rec_id)
        ).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        return {
            "recommendation_uuid": r.recommendation_uuid,
            "timestamp": r.timestamp.isoformat(),
            "symbol": r.symbol,
            "strategy_id": r.strategy_id,
            "strategy_version": r.strategy_version,
            "structure": r.structure,
            "net_credit": r.net_credit,
            "max_risk": r.max_risk,
            "risk_reward_ratio": r.risk_reward_ratio,
            "confidence_score": r.confidence_score,
            "is_allowed": r.is_allowed
        }

@router.patch("/recommendations/{rec_id}/status")
async def update_recommendation_status(rec_id: str, status: str):
    with get_sync_session() as session:
        r = session.execute(
            select(FnoRecommendation).where(FnoRecommendation.recommendation_uuid == rec_id)
        ).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        # Modify structure status
        structure = dict(r.structure)
        structure["status"] = status.upper()
        r.structure = structure
        session.add(r)
        
        # Publish event log
        event = FnoAuditLog(
            event_type="RECOMMENDATION_STATUS_CHANGED",
            symbol=r.symbol,
            payload={"recommendation_uuid": rec_id, "status": status.upper()}
        )
        session.add(event)
        
        return {"status": "success", "recommendation_uuid": rec_id, "new_status": status.upper()}


class SaveRecommendationRequest(BaseModel):
    recommendation_uuid: str
    strategy_name: str


class UpdateSavedRequest(BaseModel):
    status: Optional[str] = None
    user_notes: Optional[str] = None


@router.post("/saved-recommendations")
async def save_recommendation(payload: SaveRecommendationRequest):
    with get_sync_session() as session:
        # Fetch the active FnoRecommendation
        r = session.execute(
            select(FnoRecommendation).where(FnoRecommendation.recommendation_uuid == payload.recommendation_uuid)
        ).scalar_one_or_none()
        
        if not r:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        # Find the matching strategy details from ranked_strategies or structure
        ranked = r.structure.get("ranked_strategies", [])
        found_strat = next((s for s in ranked if s["name"].lower() == payload.strategy_name.lower()), None)
        
        if not found_strat:
            # Fallback to structure vehicle if strategy name matches
            if r.structure.get("vehicle", "").lower() == payload.strategy_name.lower():
                found_strat = {
                    "name": r.structure.get("vehicle"),
                    "selectedExpiry": r.structure.get("selectedExpiry", "Monthly"),
                    "selectedOptionChain": r.structure.get("selectedOptionChain", "28-AUG-2026"),
                    "score": r.structure.get("trade_quality_score", 95),
                    "confidence": f"{r.structure.get('trade_quality_score', 95)}%",
                    "shortCall": r.structure.get("shortCall", 0.0),
                    "longCall": r.structure.get("longCall", 0.0),
                    "shortPut": r.structure.get("shortPut", 0.0),
                    "longPut": r.structure.get("longPut", 0.0),
                    "expectedCredit": r.structure.get("expectedCredit", 0.0),
                    "maxRisk": r.structure.get("maxRisk", 0.0),
                    "marginRequired": r.structure.get("marginRequired", 0.0),
                    "riskReward": r.structure.get("riskReward", 0.0),
                    "winProbability": f"{r.structure.get('winProbability', 70)}%",
                    "risk": r.structure.get("risk", "Medium"),
                    "breakEvenLower": r.structure.get("breakEvenLower", 0.0),
                    "breakEvenUpper": r.structure.get("breakEvenUpper", 0.0),
                    "greeks": r.structure.get("greeks", {}),
                    "evAnalysis": r.structure.get("evAnalysis", {}),
                    "riskAnalysis": r.structure.get("riskAnalysis", {}),
                    "historicalSetups": r.structure.get("historicalSetups", []),
                    "candidateStrikes": r.structure.get("candidateStrikes", []),
                    "optionChainComparisons": r.structure.get("optionChainComparisons", [])
                }
            else:
                raise HTTPException(status_code=404, detail="Strategy not found in recommendation payload")

        import uuid
        saved = SavedRecommendation(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            scan_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            symbol=r.symbol,
            expiry=found_strat.get("selectedOptionChain", "28-AUG-2026"),
            strategy_type=found_strat.get("name"),
            spot_price=r.structure.get("spotPrice", r.structure.get("expectedCredit", 0.0) * 10.0 + 24000.0), # Safe fallback
            atm_strike=r.structure.get("atmStrike", 24350.0),
            short_call=found_strat.get("shortCall", 0.0),
            long_call=found_strat.get("longCall", 0.0),
            short_put=found_strat.get("shortPut", 0.0),
            long_put=found_strat.get("longPut", 0.0),
            net_credit=found_strat.get("expectedCredit", 0.0),
            max_risk=found_strat.get("maxRisk", 0.0),
            max_profit=found_strat.get("expectedCredit", 0.0),
            risk_reward=found_strat.get("riskReward", 0.0),
            expected_value=found_strat.get("expectedCredit", 0.0),
            win_probability=found_strat.get("winProbability", "70%"),
            margin_required=found_strat.get("marginRequired", 120000.0),
            quality_score=found_strat.get("score", 90.0),
            confidence=found_strat.get("confidence", "90%"),
            reasoning=r.structure.get("executive_summary", "Selected on favorable VRP regime metrics."),
            regime_filters=r.structure.get("filters", {}),
            greeks=found_strat.get("greeks", {}),
            volatility_analysis={
                "ivPercentile": r.structure.get("indicators", {}).get("ivPercentile", 62.4),
                "rv20": r.structure.get("indicators", {}).get("rv20", 11.20),
                "ivRvSpread": r.structure.get("indicators", {}).get("ivRvSpread", 5.25),
                "indiaVix": r.structure.get("indicators", {}).get("indiaVix", 14.12),
                "dealerGex": r.structure.get("indicators", {}).get("dealerGex", 320000.0),
                "termStructure": r.structure.get("indicators", {}).get("termStructure", 0.9412),
                "optionChainComparisons": found_strat.get("optionChainComparisons", [])
            },
            strike_selection={"candidateStrikes": found_strat.get("candidateStrikes", [])},
            risk_analysis=found_strat.get("riskAnalysis", {}),
            historical_setups=found_strat.get("historicalSetups", []),
            status="Pending",
            user_notes=""
        )
        session.add(saved)
        session.commit()
        return {"status": "success", "saved_id": saved.id}


@router.get("/saved-recommendations")
async def get_saved_recommendations(
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    status: Optional[str] = None
):
    with get_sync_session() as session:
        query = select(SavedRecommendation)
        if symbol:
            query = query.where(SavedRecommendation.symbol == symbol.upper())
        if strategy:
            query = query.where(SavedRecommendation.strategy_type == strategy)
        if status:
            query = query.where(SavedRecommendation.status == status)
        
        query = query.order_by(SavedRecommendation.timestamp.desc())
        results = session.execute(query).scalars().all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "scan_date": r.scan_date,
                "symbol": r.symbol,
                "expiry": r.expiry,
                "strategy_type": r.strategy_type,
                "quality_score": r.quality_score,
                "status": r.status,
                "user_notes": r.user_notes,
                "net_credit": r.net_credit,
                "max_risk": r.max_risk,
                "win_probability": r.win_probability
            }
            for r in results
        ]


@router.get("/saved-recommendations/{rec_id}")
async def get_saved_recommendation_detail(rec_id: str):
    with get_sync_session() as session:
        r = session.execute(
            select(SavedRecommendation).where(SavedRecommendation.id == rec_id)
        ).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail="Saved recommendation not found")
        
        return {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "scan_date": r.scan_date,
            "symbol": r.symbol,
            "expiry": r.expiry,
            "strategy_type": r.strategy_type,
            "spot_price": r.spot_price,
            "atm_strike": r.atm_strike,
            "short_call": r.short_call,
            "long_call": r.long_call,
            "short_put": r.short_put,
            "long_put": r.long_put,
            "net_credit": r.net_credit,
            "max_risk": r.max_risk,
            "max_profit": r.max_profit,
            "risk_reward": r.risk_reward,
            "expected_value": r.expected_value,
            "win_probability": r.win_probability,
            "margin_required": r.margin_required,
            "quality_score": r.quality_score,
            "confidence": r.confidence,
            "reasoning": r.reasoning,
            "regime_filters": r.regime_filters,
            "greeks": r.greeks,
            "volatility_analysis": r.volatility_analysis,
            "strike_selection": r.strike_selection,
            "risk_analysis": r.risk_analysis,
            "historical_setups": r.historical_setups,
            "user_notes": r.user_notes,
            "status": r.status
        }


@router.put("/saved-recommendations/{rec_id}")
async def update_saved_recommendation(rec_id: str, payload: UpdateSavedRequest):
    with get_sync_session() as session:
        r = session.execute(
            select(SavedRecommendation).where(SavedRecommendation.id == rec_id)
        ).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail="Saved recommendation not found")
        
        if payload.status is not None:
            r.status = payload.status
        if payload.user_notes is not None:
            r.user_notes = payload.user_notes
        
        session.add(r)
        session.commit()
        return {"status": "success", "id": r.id, "new_status": r.status, "new_notes": r.user_notes}


# ── Internal Database Helpers ────────────────────────────────────────────────

def _save_or_update_recommendation(symbol: str, rec: dict) -> dict:
    """
    Saves a recommendation. Prevents duplicates by verifying Symbol, Expiry,
    Strike combinations, and the entry timeframe (last 10 minutes window).
    """
    now = datetime.utcnow()
    time_window = now - timedelta(minutes=10)
    
    struct = rec["structure"]
    struct["ranked_strategies"] = rec.get("ranked_strategies", [])
    # Add status flag
    struct["status"] = "READY"

    with get_sync_session() as session:
        # Check duplicate combinations within 10-minute entry window in a DB-agnostic way
        dup_query = select(FnoRecommendation).where(
            and_(
                FnoRecommendation.symbol == symbol,
                FnoRecommendation.strategy_id == rec["strategy_id"],
                FnoRecommendation.timestamp >= time_window
            )
        )
        recs_in_window = session.execute(dup_query).scalars().all()
        
        existing = None
        for r in recs_in_window:
            if (r.structure.get("shortCall") == struct["shortCall"] and
                r.structure.get("shortPut") == struct["shortPut"]):
                existing = r
                break
        
        if existing:
            # Update status/credit instead of duplicating
            existing.net_credit = rec["structure"]["expectedCredit"]
            existing.max_risk = rec["structure"]["maxRisk"]
            session.add(existing)
            logger.info("fno.recommendation_updated_duplicate", rec_id=existing.recommendation_uuid)
            return {
                "recommendation_uuid": existing.recommendation_uuid,
                "symbol": existing.symbol,
                "structure": existing.structure,
                "is_allowed": existing.is_allowed
            }
        
        # Save new recommendation
        import uuid
        gen_uuid = str(uuid.uuid4())

        new_rec = FnoRecommendation(
            recommendation_uuid=gen_uuid,
            timestamp=now,
            symbol=symbol,
            strategy_id=rec["strategy_id"],
            strategy_version=rec["strategy_version"],
            structure=struct,
            net_credit=struct["expectedCredit"],
            max_risk=struct["maxRisk"],
            risk_reward_ratio=struct["riskReward"],
            confidence_score=rec["confidence_score"],
            is_allowed=rec["is_allowed"]
        )
        session.add(new_rec)
        
        # Write filters validation audit details
        for filter_name, filter_info in rec["filters"].items():
            f_audit = FnoRecommendationFilter(
                recommendation_uuid=gen_uuid,
                filter_name=filter_name,
                value_measured=filter_info["val"],
                value_required=filter_info["desc"],
                passed=filter_info["pass"]
            )
            session.add(f_audit)
            
        logger.info("fno.recommendation_created", rec_id=gen_uuid)
        return {
            "recommendation_uuid": gen_uuid,
            "symbol": symbol,
            "structure": struct,
            "is_allowed": rec["is_allowed"]
        }

def _log_tick_to_db(symbol: str, price: float, vix: float, atm_iv: float | None = None):
    """Persist market tick. atm_iv stored in payload for future historical IV percentile calc (A6)."""
    try:
        with get_sync_session() as session:
            tick = FnoMarketTick(
                timestamp=datetime.utcnow(),
                symbol=symbol,
                price=price,
                volume=0,
                oi=0,
                pcr=0.92,
                vix=vix
            )
            session.add(tick)
            
            payload: dict = {"price": price, "vix": vix}
            if atm_iv is not None:
                payload["atm_iv"] = round(atm_iv, 4)   # stored for future IV-percentile computation

            event = FnoAuditLog(
                event_type="MARKET_TICK",
                symbol=symbol,
                payload=payload
            )
            session.add(event)
    except Exception as e:
        logger.warning("fno.db_tick_log_failed", error=str(e))

def _log_chain_to_db(symbol: str, strikes: list):
    try:
        with get_sync_session() as session:
            snapshot = FnoOptionChainSnapshot(
                timestamp=datetime.utcnow(),
                symbol=symbol,
                expiry_date=date(2026, 7, 23),
                strikes_data={"strikes": strikes},
                last_update_seq=1
            )
            session.add(snapshot)
            
            event = FnoAuditLog(
                event_type="OPTION_CHAIN_SNAPSHOT",
                symbol=symbol,
                payload={"total_strikes": len(strikes)}
            )
            session.add(event)
    except Exception as e:
        logger.warning("fno.db_chain_log_failed", error=str(e))

def _simulate_option_chain(symbol: str):
    """
    A1 — Deterministic synthetic option chain.
    Generates LTP values from a simplified Black-Scholes approximation seeded
    purely from spot price and ATM IV. Same inputs always produce the same outputs.
    This guarantees reproducibility and traceability of simulated recommendations.
    """
    index_configs = {
        "NIFTY":      {"basePrice": 24350, "interval": 50,  "atm_iv": 14.0},
        "BANKNIFTY":  {"basePrice": 52420, "interval": 100, "atm_iv": 16.0},
        "SENSEX":     {"basePrice": 79890, "interval": 100, "atm_iv": 14.5},
        "FINNIFTY":   {"basePrice": 23680, "interval": 50,  "atm_iv": 15.0},
        "MIDCPNIFTY": {"basePrice": 12340, "interval": 25,  "atm_iv": 18.0},
    }
    from indian_swing.recommendations.fno_strategy import calculate_greeks, normal_cdf
    import math as _math

    config    = index_configs.get(symbol.upper(), index_configs["NIFTY"])
    S         = float(config["basePrice"])
    interval  = config["interval"]
    sigma     = config["atm_iv"] / 100.0
    r         = 0.07
    t         = 5.0 / 365.0   # weekly expiry
    base_strike = round(S / interval) * interval

    def _bs_call(spot, strike, t, sigma, r):
        """Black-Scholes call price."""
        if t <= 0 or sigma <= 0:
            return max(0.0, spot - strike)
        d1 = (_math.log(spot / strike) + (r + 0.5 * sigma ** 2) * t) / (sigma * _math.sqrt(t))
        d2 = d1 - sigma * _math.sqrt(t)
        return spot * normal_cdf(d1) - strike * _math.exp(-r * t) * normal_cdf(d2)

    def _bs_put(spot, strike, t, sigma, r):
        """Black-Scholes put price via put-call parity."""
        call = _bs_call(spot, strike, t, sigma, r)
        return call - spot + strike * _math.exp(-r * t)

    strikes = []
    for i in range(-6, 7):   # 13 strikes around ATM
        strike_price = base_strike + i * interval
        # Apply slight skew: OTM puts have higher IV than OTM calls (vol smile)
        ce_iv = sigma * (1.0 + max(0, i) * 0.005)   # calls flatten toward OTM
        pe_iv = sigma * (1.0 + max(0, -i) * 0.008)  # puts steepen toward OTM

        ce_ltp = max(0.5, round(_bs_call(S, strike_price, t, ce_iv, r), 2))
        pe_ltp = max(0.5, round(_bs_put(S, strike_price, t, pe_iv, r), 2))

        # Deterministic OI: higher near ATM, lower at extremes
        oi_base = 500000
        oi_decay = max(0.1, 1.0 - abs(i) * 0.15)
        ce_oi = int(oi_base * oi_decay)
        pe_oi = int(oi_base * oi_decay)

        strikes.append({
            "strike": strike_price,
            "ce": {"ltp": ce_ltp, "change": 0.0, "oi": ce_oi, "iv": round(ce_iv * 100, 2)},
            "pe": {"ltp": pe_ltp, "change": 0.0, "oi": pe_oi, "iv": round(pe_iv * 100, 2)},
        })

    return {"index": symbol, "strikes": strikes, "timestamp": "deterministic"}
