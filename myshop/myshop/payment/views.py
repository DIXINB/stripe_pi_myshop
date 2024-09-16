from decimal import Decimal
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, reverse,\
                             get_object_or_404
from orders.models import Order
from orders.models import OrderItem
import json
import os
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv, find_dotenv
from django.http.response import JsonResponse

# create the Stripe instance
load_dotenv(find_dotenv())

stripe.api_version = os.getenv('STRIPE_API_VERSION')

@csrf_exempt
def createpayment(request):
  order_id=request.session.get('order_id', None)
  ordr = get_object_or_404(Order, id=order_id)
  s=ordr.get_total_cost()

  sc=int(s*100)
  crt=OrderItem.objects.filter(order_id=order_id)

  stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

  if request.method=="POST":
      
      data = json.loads(request.body)
      # Create a PaymentIntent with the order amount and currency
      intent = stripe.PaymentIntent.create(
        amount=sc,
        description=order_id,
        currency=data['currency'],
        metadata={'integration_check': 'accept_a_payment'},
        )
      try:
        print('clientSecret:', intent.client_secret)
        return JsonResponse({'publishableKey':os.getenv('STRIPE_PUBLISHABLE_KEY'), 'clientSecret': intent.client_secret})
      except Exception as e:
        return JsonResponse({'error':str(e)},status= 403)
  return render(request,"payment/checkout.html", {"crt":crt, "total":s})


def payment_completed(request):
    return render(request, 'payment/completed.html')
     

def payment_canceled(request):
    return render(request, 'payment/canceled.html')
