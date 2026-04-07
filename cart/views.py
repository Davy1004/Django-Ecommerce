from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': 1,
            'image': product.image.url
        }

    request.session['cart'] = cart
    return redirect('cart_detail')


def cart_detail(request):
    cart = request.session.get('cart', {})

    total_price = 0
    for item in cart.values():
        total_price += item['price'] * item['quantity']

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'total_price': total_price
    })


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]

    request.session['cart'] = cart
    return redirect('cart_detail')


def increase_quantity(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1

    request.session['cart'] = cart
    return redirect('cart_detail')


def decrease_quantity(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] -= 1

        if cart[str(product_id)]['quantity'] <= 0:
            del cart[str(product_id)]

    request.session['cart'] = cart
    return redirect('cart_detail')
