import os
import asyncio
import json
import random
import time
from databento import Live
from databento.common.error import BentoError
from databento_dbn import TradeMsg
from aiohttp import web, WSMsgType

API_KEY = os.getenv("DATABENTO_API_KEY")
DEFAULT_SYMBOL = "ES.FUT"
clients = set()

# Used to track last trade
last_trade_time = 0

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    clients.add(ws)
    print(f"Client connected. Total clients: {len(clients)}")
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT and msg.data == "ping":
                await ws.send_str("pong")
            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
    finally:
        clients.remove(ws)
        print(f"Client disconnected. Total clients: {len(clients)}")
    return ws

async def broadcast_tick_data(record):
    global last_trade_time
    last_trade_time = time.time()

    data = {
        "time": record["time"],
        "price": record["price"],
        "size": record["size"]
    }
    print("[SEND]", data)
    payload = json.dumps(data)
    await asyncio.gather(*[ws.send_str(payload) for ws in clients])

async def stream_ticks_from_databento(symbol: str):
    print(f"📡 Starting Databento live stream for {symbol}")
    live = Live(key=API_KEY)

    await live.subscribe(
        dataset="GLBX.MDP3",
        schema="trades",
        stype_in="parent",
        symbols=symbol
    )

    async for record in live:
        print("[RECORD]", record)
        if isinstance(record, TradeMsg):
            tick_data = {
                "time": record.ts_event / 1e9,
                "price": record.price / 1e4,
                "size": record.size
            }
            print("[TICK]", tick_data)
            if clients:
                await broadcast_tick_data(tick_data)

async def tick_timeout_watchdog(app, seconds=10):
    global last_trade_time
    last_trade_time = time.time()
    while True:
        await asyncio.sleep(seconds)
        if time.time() - last_trade_time > seconds:
            print(f"⚠️ No ticks received in {seconds}s. Switching to mock mode.")
            app["mock"] = asyncio.create_task(mock_stream_loop())
            app["stream"].cancel()
            break

async def mock_stream_loop():
    print("🤖 Mock mode enabled. Streaming fake ticks.")
    while True:
        if clients:
            now = time.time()
            price = round(5000 + random.uniform(-5, 5), 2)
            tick = {
                "time": now,
                "price": price,
                "size": random.randint(1, 10)
            }
            await broadcast_tick_data(tick)
        await asyncio.sleep(1)

def run_live_feed(host="0.0.0.0", port=8765, symbol=DEFAULT_SYMBOL):
    app = web.Application()
    app.add_routes([web.get("/ws", ws_handler)])

    async def on_start(app):
        print("🧠 Launching live stream and watchdog...")
        app["stream"] = asyncio.create_task(stream_ticks_from_databento(symbol))
        app["watchdog"] = asyncio.create_task(tick_timeout_watchdog(app))

    async def on_cleanup(app):
        for key in ["stream", "mock", "watchdog"]:
            if key in app:
                app[key].cancel()
                try:
                    await app[key]
                except asyncio.CancelledError:
                    print(f"✔️ {key} cancelled.")

    app.on_startup.append(on_start)
    app.on_cleanup.append(on_cleanup)

    print(f"🚀 WebSocket server on {host}:{port} for {symbol}")
    web.run_app(app, host=host, port=port)

if __name__ == "__main__":
    print("Running live_feed.py directly…")
    sym = input(f"Symbol (default {DEFAULT_SYMBOL}): ") or DEFAULT_SYMBOL
    run_live_feed(symbol=sym)
