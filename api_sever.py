"""Stripe webhook receiver for P.H.U.C.S Plus. Deploy separately from Streamlit.
Example: uvicorn api_server:app --host 0.0.0.0 --port 8000
"""
import os
from datetime import datetime, timezone
import requests
from fastapi import FastAPI, Request, HTTPException
import stripe

app = FastAPI(title="P.H.U.C.S billing webhook")

@app.get('/health')
def health():
    return {"status": "ok"}

@app.post('/stripe/webhook')
async def stripe_webhook(request: Request):
    secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    api_key = os.getenv('STRIPE_SECRET_KEY', '')
    if not secret or not api_key:
        raise HTTPException(status_code=503, detail='Stripe webhook is not configured')
    stripe.api_key = api_key
    payload = await request.body()
    signature = request.headers.get('stripe-signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, signature, secret)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Invalid webhook: {exc}')

    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    if not supabase_url or not service_key:
        raise HTTPException(status_code=503, detail='Supabase server credentials are not configured')

    event_type = event['type']
    obj = event['data']['object']
    relevant = event_type in ('checkout.session.completed', 'customer.subscription.updated', 'customer.subscription.deleted')
    if relevant:
        metadata = obj.get('metadata') or {}
        user_id = metadata.get('phucs_user_id') or obj.get('client_reference_id')
        subscription_id = obj.get('subscription') if event_type == 'checkout.session.completed' else obj.get('id')
        customer_id = obj.get('customer')
        status = 'active' if event_type == 'checkout.session.completed' else obj.get('status', 'inactive')
        period_end = obj.get('current_period_end')
        # For checkout completion, retrieve subscription so its actual status/period are verified.
        if event_type == 'checkout.session.completed' and subscription_id:
            try:
                sub = stripe.Subscription.retrieve(subscription_id)
                status = sub.get('status', status)
                period_end = sub.get('current_period_end', period_end)
                metadata = sub.get('metadata') or metadata
                user_id = metadata.get('phucs_user_id') or user_id
            except Exception:
                pass
        if not user_id:
            # Ignore unrelated Stripe events that do not belong to a P.H.U.C.S user.
            return {'received': True, 'ignored': True}
        row = {
            'user_id': str(user_id), 'stripe_customer_id': str(customer_id or ''),
            'stripe_subscription_id': str(subscription_id or ''), 'status': str(status),
            'current_period_end': datetime.fromtimestamp(period_end, timezone.utc).isoformat() if period_end else None,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        response = requests.post(
            f'{supabase_url}/rest/v1/subscriptions?on_conflict=user_id',
            headers={'apikey': service_key, 'Authorization': f'Bearer {service_key}',
                     'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates,return=minimal'},
            json=row, timeout=20)
        if not response.ok:
            raise HTTPException(status_code=502, detail='Could not update subscription status in Supabase')
    return {'received': True}
