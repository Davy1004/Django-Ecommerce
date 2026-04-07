from django.shortcuts import render, redirect
from .models import Order
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json


@api_view(['POST'])
def checkout_api(request):
    data = request.data
    required = ['name', 'email', 'address', 'city', 'phone', 'total_amount']
    for field in required:
        if not data.get(field):
            return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)

    order = Order.objects.create(
        name=data['name'],
        email=data['email'],
        address=data['address'],
        city=data['city'],
        phone=data['phone'],
        total_amount=data['total_amount']
    )

    return Response({
        'success': True,
        'order_id': order.id,
        'message': 'Order placed successfully!'
    }, status=status.HTTP_201_CREATED)


# Legacy template views
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart_detail')

    total_price = sum(item['price'] * item['quantity'] for item in cart.values())

    if request.method == 'POST':
        Order.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            phone=request.POST.get('phone'),
            total_amount=total_price
        )
        request.session['cart'] = {}
        return redirect('order_success')

    return render(request, 'orders/checkout.html', {'cart': cart, 'total_price': total_price})


def order_success(request):
    return render(request, 'orders/success.html')
