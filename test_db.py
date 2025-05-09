import asyncio
import os
import logging
from databento import Live
from databento_dbn import TradeMsg
from dotenv import load_dotenv

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Load .env
load_dotenv()
API_KEY = os.getenv("DATABENTO_API_KEY")

async def test_databento_stream():
    if not API_KEY:
        print("❌ Missing API key. Check your .env file.")
        return

    print("🔑 Using API Key:", API_KEY[:10] + "..." + API_KEY[-4:])
    print("📡 Connecting to Databento live feed...")

    live = Live(key=API_KEY)

    # ❗ No await here
    live.subscribe(
        dataset="GLBX.MDP3",
        schema="trades",
        stype_in="parent",
        symbols="ES.FUT",
    )

    print("✅ Subscribed to ES.FUT (GLBX.MDP3, trades). Waiting for ticks...")

    async for record in live:
        if isinstance(record, TradeMsg):
            print("✅ Tick received:")
            print(f"  Time (ns): {record.ts_event}")
            print(f"  Px: {record.price / 1e4}")
            print(f"  Sz: {record.size}")
            break  # Stop after first tick

if __name__ == "__main__":
    asyncio.run(test_databento_stream())
