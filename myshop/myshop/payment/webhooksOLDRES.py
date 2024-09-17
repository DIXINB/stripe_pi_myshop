import os
import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from .tasks import payment_completed
from dotenv import load_dotenv, find_dotenv

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
                    payload,
                    sig_header,
                    os.getenv('STRIPE_WEBHOOK_SECRET')
                )
#                    settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

#    if event.type == 'checkout.session.completed':
#    if event.type == 'charge.updated':
    if event.type == 'payment_intent.succeeded':
            payment_intent=event.data.object
#        session = event.data.object
#        if session.mode == 'payment' and session.payment_status == 'paid':
            try:
#                order = Order.objects.get(id=session.client_reference_id)
                order = Order.objects.get(id=payment_intent.customer)
            except Order.DoesNotExist:
                return HttpResponse(status=404)
            # mark order as paid
            order.paid = True
            # store Stripe payment ID
#            order.stripe_id = session.payment_intent
            order.stripe_id = payment_intent.customer
            order.save()
            # launch asynchronous task
            payment_completed.delay(order.id)

    return HttpResponse(status=200)
