from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <h1>SEMIS - AI Art Packs</h1>
    <p>Buy 100 Expansion Credits for $20</p>
    <form action="/create-checkout" method="post">
      <button type="submit">Buy Now - $20</button>
    </form>
    """

@app.post("/create-checkout")
async def create_checkout():
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': '100 AI Art Credits'},
                'unit_amount': 2000,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://your-vercel-url.vercel.app/success',
        cancel_url='https://your-vercel-url.vercel.app/',
        metadata={'credits': '100'}
    )
    return RedirectResponse(session.url, status_code=303)

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, os.getenv("STRIPE_WEBHOOK_SECRET"))
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            print("✅ Payment received! Credits:", session.metadata.credits)
            # Here you would queue Celery or update Redis wallet
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/success", response_class=HTMLResponse)
async def success():
    return "<h1>Payment successful! Credits added. Check your dashboard.</h1>"
