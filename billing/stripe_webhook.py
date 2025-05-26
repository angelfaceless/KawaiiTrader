import os
from fastapi import APIRouter, Request, Header, HTTPException
from datetime import datetime, timezone, timedelta
import stripe
from supabase import create_client, Client as SupabaseClient
from dotenv import load_dotenv

load_dotenv()

# Load env vars
stripe.api_key = os.getenv("STRIPE_API_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase client
sb: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()


def _upsert_membership(user_id: str, plan: str, expires_at=None):
    """Create or update user subscription in Supabase"""
    print(f"📡 Upserting membership → user_id: {user_id}, plan: {plan}, expires_at: {expires_at}")
    sb.table("memberships").upsert({
        "user_id": user_id,
        "plan": plan,
        "expires_at": expires_at,
    }).execute()


@router.post("/stripe/webhook", status_code=204)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, convert_underscores=False),  # ✅ Correct header extraction
):
    print("\n--- 📥 Incoming Stripe Webhook ---")
    print("📬 All headers:", dict(request.headers))

    payload = await request.body()
    print("📦 Raw payload received:", payload.decode("utf-8"))
    print("📬 Stripe-Signature header:", stripe_signature)

    if stripe_signature is None:
        print("❌ Missing Stripe-Signature header")
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    if WEBHOOK_SECRET is None:
        print("❌ Missing WEBHOOK_SECRET from .env")
        raise HTTPException(status_code=500, detail="Missing webhook secret")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, WEBHOOK_SECRET
        )
        print(f"✅ Verified event: {event['type']} [{event['id']}]")
    except Exception as e:
        print("❌ Signature verification failed:", e)
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    if event["type"] in [
        "checkout.session.completed",
        "invoice.payment_failed",
        "customer.subscription.deleted"
    ]:
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        plan = session.get("metadata", {}).get("plan", "pro")

        print(f"📘 Event type: {event['type']}")
        print(f"👤 user_id: {user_id}, 🧾 plan: {plan}")

        if event["type"] == "checkout.session.completed":
            _upsert_membership(user_id, plan, None)
            print("✅ Upserted active subscription")

        elif event["type"] == "invoice.payment_failed":
            expires = datetime.now(timezone.utc) + timedelta(days=1)
            _upsert_membership(user_id, plan, expires)
            print("⚠️ Marked as grace-period")

        elif event["type"] == "customer.subscription.deleted":
            expires = datetime.now(timezone.utc)
            _upsert_membership(user_id, "free", expires)
            print("❌ Marked as unsubscribed")

    return ""
