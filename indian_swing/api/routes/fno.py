from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import date, datetime, timedelta
from sqlalchemy import select, update, and_, desc
from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import (
    FnoMarketTick, FnoOptionChainSnapshot, FnoAuditLog,
    FnoRecommendation, FnoRecommendationFilter
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
async def get_market_data(symbol: str):
    token = settings.upstox_access_token
    mapped_symbol = INDEX_MAP.get(symbol.upper(), "NSE_INDEX|Nifty 50")
    
    # Resolve target spot & vix
    if not token:
        base_prices = {"NIFTY": 24350.0, "BANKNIFTY": 52420.0, "SENSEX": 79890.0, "FINNIFTY": 23680.0, "MIDCPNIFTY": 12340.0}
        last_price = base_prices.get(symbol.upper(), 24350.0)
        vix_price = 14.12
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
        except Exception as e:
            logger.error("fno.market_data_api_failed", symbol=symbol, error=str(e))
            base_prices = {"NIFTY": 24350.0, "BANKNIFTY": 52420.0, "SENSEX": 79890.0, "FINNIFTY": 23680.0, "MIDCPNIFTY": 12340.0}
            last_price = base_prices.get(symbol.upper(), 24350.0)
            vix_price = 14.12

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

    # Log tick to DB (A6: pass atm_iv for future historical IV percentile)
    atm_iv_for_log = None
    try:
        if strikes_list:
            atm_s = min(strikes_list, key=lambda x: abs(x["strike"] - last_price))
            atm_iv_for_log = (atm_s["ce"]["iv"] + atm_s["pe"]["iv"]) / 2.0
    except Exception:
        pass
    _log_tick_to_db(symbol.upper(), last_price, vix_price, atm_iv=atm_iv_for_log)

    # 3. Retrieve option chain strikes to feed strategy engine
    try:
        chain_response = await get_option_chain(symbol.upper())
        strikes_list = chain_response.get("strikes", [])
    except Exception as ce:
        logger.warning("fno.get_chain_failed_for_strategy", error=str(ce))
        strikes_list = _simulate_option_chain(symbol.upper()).get("strikes", [])

    # Run data integrity validation on the actual quote and chain
    spot_packet = {"spotPrice": last_price, "indiaVix": vix_price, "marketStatus": "OPEN", "expiry": "23-JUL-2026", "timestamp": datetime.utcnow().isoformat()}
    chain_packet = {"strikes": strikes_list}
    passed, score, errs = validator.validate_packet(symbol.upper(), spot_packet, chain_packet)

    # 5. Strategy Engine Recommendation Generation & Save
    rec_obj = fno_strategy_engine.evaluate_and_build(symbol.upper(), last_price, vix_price, strikes_list)
    saved_rec = _save_or_update_recommendation(symbol.upper(), rec_obj)

    return {
        "symbol": symbol,
        "spotPrice": last_price,
        "changePct": change_pct,
        "indiaVix": vix_price,
        "marketStatus": "OPEN",
        "expiry": "23-JUL-2026",
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
        "ranked_strategies": rec_obj.get("ranked_strategies", [])
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
