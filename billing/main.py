from fastapi import FastAPI, Request, Header, HTTPException
from dotenv import load_dotenv
import os

app = FastAPI()

# Load environment variables
load_dotenv()

# Root route so ngrok/health checks don't 404
@app.get("/")
def ping():
    return {"message": "server online"}

# Stripe webhook
@app.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, convert_underscores=False)
):
    payload = await request.body()
    print("📦 Raw payload received:", payload.decode())
    print("📬 Stripe-Signature header:", stripe_signature)

    if stripe_signature is None:
        print("❌ Missing Stripe-Signature header")
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if webhook_secret is None:
        print("❌ STRIPE_WEBHOOK_SECRET not set in .env")
        raise HTTPException(status_code=500, detail="Webhook secret missing")

    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_API_KEY")
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret
        )
        print(f"✅ Verified event: {event['type']}")
    except Exception as e:
        print("❌ Signature verification failed:", str(e))
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    return {"status": "ok"}
