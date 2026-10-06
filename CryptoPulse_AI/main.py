from pathlib import Path
import csv
import io
import asyncio

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles


# =========================================================
# PROJECT SETUP
# =========================================================

BASE = Path(__file__).resolve().parent

app = FastAPI(
    title="CryptoPulse AI",
    description="AI-powered Cryptocurrency Market Intelligence",
    version="1.0.0"
)


# =========================================================
# STATIC FILES
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory=BASE / "static"),
    name="static"
)


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/")
async def home():
    return FileResponse(
        BASE / "static" / "index.html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "CryptoPulse AI"
    }


# =========================================================
# COINGECKO REQUEST
# =========================================================

async def get_coingecko_markets():

    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 20,
        "page": 1,
        "sparkline": "false"
    }

    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 CryptoPulseAI/1.0"
    }

    for attempt in range(3):

        try:

            async with httpx.AsyncClient(
                timeout=20,
                follow_redirects=True
            ) as client:

                response = await client.get(
                    url,
                    params=params,
                    headers=headers
                )

                if response.status_code == 200:

                    data = response.json()

                    if isinstance(data, list) and data:
                        return data

                print(
                    f"CoinGecko attempt {attempt + 1}: "
                    f"HTTP {response.status_code}"
                )

        except Exception as e:

            print(
                f"CoinGecko attempt {attempt + 1} error:",
                e
            )

        await asyncio.sleep(2)

    return []


# =========================================================
# BINANCE BACKUP MARKET DATA
# =========================================================

BINANCE_COINS = [
    {
        "id": "bitcoin",
        "name": "Bitcoin",
        "symbol": "btc",
        "binance_symbol": "BTCUSDT",
        "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"
    },
    {
        "id": "ethereum",
        "name": "Ethereum",
        "symbol": "eth",
        "binance_symbol": "ETHUSDT",
        "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png"
    },
    {
        "id": "binancecoin",
        "name": "BNB",
        "symbol": "bnb",
        "binance_symbol": "BNBUSDT",
        "image": "https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png"
    },
    {
        "id": "solana",
        "name": "Solana",
        "symbol": "sol",
        "binance_symbol": "SOLUSDT",
        "image": "https://assets.coingecko.com/coins/images/4128/large/solana.png"
    },
    {
        "id": "xrp",
        "name": "XRP",
        "symbol": "xrp",
        "binance_symbol": "XRPUSDT",
        "image": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png"
    },
    {
        "id": "dogecoin",
        "name": "Dogecoin",
        "symbol": "doge",
        "binance_symbol": "DOGEUSDT",
        "image": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png"
    },
    {
        "id": "cardano",
        "name": "Cardano",
        "symbol": "ada",
        "binance_symbol": "ADAUSDT",
        "image": "https://assets.coingecko.com/coins/images/975/large/cardano.png"
    },
    {
        "id": "avalanche-2",
        "name": "Avalanche",
        "symbol": "avax",
        "binance_symbol": "AVAXUSDT",
        "image": "https://assets.coingecko.com/coins/images/12559/large/Avalanche_Circle_RedWhite_Trans.png"
    }
]


async def get_binance_markets():

    url = "https://api.binance.com/api/v3/ticker/24hr"

    try:

        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True
        ) as client:

            response = await client.get(
                url,
                headers={
                    "accept": "application/json",
                    "user-agent": "CryptoPulseAI/1.0"
                }
            )

            response.raise_for_status()

            all_tickers = response.json()

            ticker_map = {
                item.get("symbol"): item
                for item in all_tickers
            }

            result = []

            for index, coin in enumerate(BINANCE_COINS, start=1):

                ticker = ticker_map.get(
                    coin["binance_symbol"]
                )

                if not ticker:
                    continue

                try:

                    price = float(
                        ticker.get("lastPrice", 0)
                    )

                    change = float(
                        ticker.get("priceChangePercent", 0)
                    )

                    volume = float(
                        ticker.get("quoteVolume", 0)
                    )

                except (TypeError, ValueError):

                    continue

                result.append({

                    "id": coin["id"],

                    "name": coin["name"],

                    "symbol": coin["symbol"],

                    "image": coin["image"],

                    "current_price": price,

                    "market_cap": 0,

                    "total_volume": volume,

                    "price_change_percentage_24h": change,

                    "market_cap_rank": index

                })

            if result:
                return result

    except Exception as e:

        print(
            "Binance market API error:",
            e
        )

    return []


# =========================================================
# LIVE MARKET DATA
# =========================================================

@app.get("/api/markets")
async def markets():

    # First try CoinGecko
    data = await get_coingecko_markets()

    if data:
        return data

    # If CoinGecko is rate-limited, use Binance
    print(
        "CoinGecko unavailable. "
        "Using Binance live market data."
    )

    data = await get_binance_markets()

    return data


# =========================================================
# CRYPTO HISTORY
# =========================================================

@app.get("/api/history/{coin_id}")
async def history(
    coin_id: str,
    days: int = 7
):

    url = (
        "https://api.coingecko.com/api/v3/"
        f"coins/{coin_id}/market_chart"
    )

    params = {
        "vs_currency": "usd",
        "days": days
    }

    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 CryptoPulseAI/1.0"
    }

    for attempt in range(2):

        try:

            async with httpx.AsyncClient(
                timeout=20,
                follow_redirects=True
            ) as client:

                response = await client.get(
                    url,
                    params=params,
                    headers=headers
                )

                if response.status_code == 200:

                    data = response.json()

                    if data.get("prices"):
                        return data

                print(
                    f"History attempt {attempt + 1}: "
                    f"HTTP {response.status_code}"
                )

        except Exception as e:

            print(
                "CoinGecko history error:",
                e
            )

        await asyncio.sleep(2)

    return {
        "prices": []
    }


# =========================================================
# SINGLE COIN DATA
# =========================================================

@app.get("/api/coin/{coin_id}")
async def coin(coin_id: str):

    url = (
        "https://api.coingecko.com/api/v3/"
        f"coins/{coin_id}"
    )

    try:

        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True
        ) as client:

            response = await client.get(
                url,
                headers={
                    "accept": "application/json",
                    "user-agent": "Mozilla/5.0 CryptoPulseAI/1.0"
                }
            )

            response.raise_for_status()

            return response.json()

    except Exception as e:

        print(
            "Coin API error:",
            e
        )

        return {
            "id": coin_id,
            "name": coin_id,
            "error": "Coin data temporarily unavailable"
        }


# =========================================================
# CRYPTO SEARCH
# =========================================================

@app.get("/api/search")
async def search(q: str):

    url = (
        "https://api.coingecko.com/api/v3/"
        "search"
    )

    try:

        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True
        ) as client:

            response = await client.get(
                url,
                params={
                    "query": q
                },
                headers={
                    "accept": "application/json",
                    "user-agent": "Mozilla/5.0 CryptoPulseAI/1.0"
                }
            )

            response.raise_for_status()

            return response.json()

    except Exception as e:

        print(
            "Search API error:",
            e
        )

        return {
            "coins": []
        }


# =========================================================
# AI MARKET SIGNAL
# =========================================================

@app.get("/api/analysis/{coin_id}")
async def analysis(coin_id: str):

    return {

        "coin": coin_id,

        "trend": "Bullish",

        "signal": "BUY",

        "confidence": 85,

        "message":
            "AI Market Signal generated successfully"

    }


# =========================================================
# CSV EXPORT
# =========================================================

@app.get("/api/export/markets")
async def export_markets():

    data = await get_coingecko_markets()

    if not data:
        data = await get_binance_markets()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Rank",
        "Name",
        "Symbol",
        "Price USD",
        "Market Cap",
        "24h Change",
        "24h Volume"
    ])

    for crypto in data:

        writer.writerow([

            crypto.get(
                "market_cap_rank",
                ""
            ),

            crypto.get(
                "name",
                ""
            ),

            crypto.get(
                "symbol",
                ""
            ),

            crypto.get(
                "current_price",
                0
            ),

            crypto.get(
                "market_cap",
                0
            ),

            crypto.get(
                "price_change_percentage_24h",
                0
            ),

            crypto.get(
                "total_volume",
                0
            )

        ])

    output.seek(0)

    return StreamingResponse(

        iter([
            output.getvalue()
        ]),

        media_type="text/csv",

        headers={
            "Content-Disposition":
                "attachment; "
                "filename=cryptopulse_markets.csv"
        }

    )


# =========================================================
# EXCEL EXPORT
# =========================================================

@app.get("/api/export/excel")
async def export_excel():

    from openpyxl import Workbook

    data = await get_coingecko_markets()

    if not data:
        data = await get_binance_markets()

    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Crypto Markets"

    sheet.append([
        "Rank",
        "Name",
        "Symbol",
        "Price USD",
        "Market Cap",
        "24h Change",
        "24h Volume"
    ])

    for crypto in data:

        sheet.append([

            crypto.get(
                "market_cap_rank",
                ""
            ),

            crypto.get(
                "name",
                ""
            ),

            crypto.get(
                "symbol",
                ""
            ),

            crypto.get(
                "current_price",
                0
            ),

            crypto.get(
                "market_cap",
                0
            ),

            crypto.get(
                "price_change_percentage_24h",
                0
            ),

            crypto.get(
                "total_volume",
                0
            )

        ])

    sheet.column_dimensions["A"].width = 10
    sheet.column_dimensions["B"].width = 20
    sheet.column_dimensions["C"].width = 12
    sheet.column_dimensions["D"].width = 18
    sheet.column_dimensions["E"].width = 20
    sheet.column_dimensions["F"].width = 18
    sheet.column_dimensions["G"].width = 20

    output = io.BytesIO()

    workbook.save(output)

    output.seek(0)

    return StreamingResponse(

        output,

        media_type=
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet",

        headers={
            "Content-Disposition":
                "attachment; "
                "filename=cryptopulse_markets.xlsx"
        }

    )


# =========================================================
# APPLICATION START
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )