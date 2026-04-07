from django.shortcuts import render
from products.models import Category, Product
# Create your views here.


def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    context = {
        'categories': categories,
        'products': products
    }
    return render(request, 'core/home.html', context)
