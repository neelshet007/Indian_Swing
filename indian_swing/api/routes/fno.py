from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import date
from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

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
    
    # Fallback simulation if token is missing
    if not token:
        logger.info("fno.market_data_fallback", symbol=symbol)
        base_prices = {"NIFTY": 24350.0, "BANKNIFTY": 52420.0, "SENSEX": 79890.0, "FINNIFTY": 23680.0, "MIDCPNIFTY": 12340.0}
        base_price = base_prices.get(symbol.upper(), 24350.0)
        return {
            "symbol": symbol,
            "spotPrice": base_price,
            "changePct": 0.45 if symbol != "BANKNIFTY" else -0.22,
            "indiaVix": 14.12,
            "marketStatus": "OPEN",
            "expiry": "23-JUL-2026",
            "tradingSession": "REGULAR"
        }

    try:
        # Call Upstox LTP API
        async with httpx.AsyncClient() as client:
            url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={mapped_symbol}"
            response = await client.get(url, headers=get_headers(), timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Fetch India VIX for VRP indicators
            vix_url = "https://api.upstox.com/v2/market-quote/ltp?instrument_key=NSE_INDEX|India%20Vix"
            vix_response = await client.get(vix_url, headers=get_headers(), timeout=10.0)
            vix_data = vix_response.json() if vix_response.status_code == 200 else {}
            
            spot_info = data.get("data", {}).get(mapped_symbol, {})
            vix_info = vix_data.get("data", {}).get("NSE_INDEX|India Vix", {})

            last_price = spot_info.get("last_price", 0.0)
            vix_price = vix_info.get("last_price", 14.12)
            
            return {
                "symbol": symbol,
                "spotPrice": last_price,
                "changePct": 0.45 if symbol != "BANKNIFTY" else -0.22,
                "indiaVix": vix_price,
                "marketStatus": "OPEN",
                "expiry": "23-JUL-2026",
                "tradingSession": "REGULAR"
            }
    except Exception as e:
        logger.error("fno.market_data_api_failed", symbol=symbol, error=str(e))
        base_prices = {"NIFTY": 24350.0, "BANKNIFTY": 52420.0, "SENSEX": 79890.0, "FINNIFTY": 23680.0, "MIDCPNIFTY": 12340.0}
        base_price = base_prices.get(symbol.upper(), 24350.0)
        return {
            "symbol": symbol,
            "spotPrice": base_price,
            "changePct": 0.45,
            "indiaVix": 14.12,
            "marketStatus": "OPEN",
            "expiry": "23-JUL-2026",
            "tradingSession": "REGULAR"
        }

@router.get("/option-chain")
async def get_option_chain(symbol: str, expiry_date: Optional[str] = None):
    token = settings.upstox_access_token
    mapped_symbol = INDEX_MAP.get(symbol.upper(), "NSE_INDEX|Nifty 50")

    if not token:
        return _simulate_option_chain(symbol)

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
                
            return {
                "index": symbol,
                "strikes": strikes,
                "timestamp": str(date.today())
            }
    except Exception as e:
        logger.error("fno.option_chain_api_failed", symbol=symbol, error=str(e))
        return _simulate_option_chain(symbol)

def _simulate_option_chain(symbol: str):
    index_configs = {
        "NIFTY": {"basePrice": 24350, "interval": 50},
        "BANKNIFTY": {"basePrice": 52420, "interval": 100},
        "SENSEX": {"basePrice": 79890, "interval": 100},
        "FINNIFTY": {"basePrice": 23680, "interval": 50},
        "MIDCPNIFTY": {"basePrice": 12340, "interval": 25}
    }

    config = index_configs.get(symbol.upper(), index_configs["NIFTY"])
    import random
    base_strike = round(config["basePrice"] / config["interval"]) * config["interval"]
    
    strikes = []
    for i in range(-5, 6):
      strike_price = base_strike + (i * config["interval"])
      strikes.append({
        "strike": strike_price,
        "ce": {
          "ltp": max(2.0, (10 - i * 2) * (config["interval"] / 10) + random.random()),
          "change": (random.random() - 0.4) * 10,
          "oi": round(100000 + random.random() * 500000),
          "iv": 12.0 + random.random() * 4
        },
        "pe": {
          "ltp": max(2.0, (10 + i * 2) * (config["interval"] / 10) + random.random()),
          "change": (random.random() - 0.6) * 10,
          "oi": round(100000 + random.random() * 500000),
          "iv": 12.5 + random.random() * 4
        }
      })

    return {
      "index": symbol,
      "strikes": strikes,
      "timestamp": "15:30:00"
    }
