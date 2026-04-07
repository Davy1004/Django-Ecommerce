from django.shortcuts import render, get_object_or_404
from .models import Product, Category
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def product_list_api(request):
    category_slug = request.GET.get('category')
    search = request.GET.get('search', '')

    products = Product.objects.all()
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search:
        products = products.filter(name__icontains=search)

    data = [{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'price': float(p.price),
        'stock': p.stock,
        'description': p.description,
        'image': request.build_absolute_uri(p.image.url) if p.image else None,
        'category': {'id': p.category.id, 'name': p.category.name, 'slug': p.category.slug}
    } for p in products]

    return Response(data)


@api_view(['GET'])
def product_detail_api(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return Response({
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'price': float(product.price),
        'stock': product.stock,
        'description': product.description,
        'image': request.build_absolute_uri(product.image.url) if product.image else None,
        'category': {'id': product.category.id, 'name': product.category.name, 'slug': product.category.slug}
    })


@api_view(['GET'])
def category_list_api(request):
    categories = Category.objects.all()
    return Response([{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories])


@api_view(['GET'])
def category_detail_api(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return Response({
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'products': [{
            'id': p.id, 'name': p.name, 'slug': p.slug,
            'price': float(p.price), 'stock': p.stock,
            'image': request.build_absolute_uri(p.image.url) if p.image else None,
        } for p in products]
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'products/product_detail.html', {'product': product})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'products/category_detail.html', {'category': category, 'products': products})
