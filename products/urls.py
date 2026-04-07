from django.urls import path
from . import views

urlpatterns = [
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('api/products/', views.product_list_api, name='product_list_api'),
    path('api/products/<slug:slug>/', views.product_detail_api, name='product_detail_api'),
    path('api/categories/', views.category_list_api, name='category_list_api'),
    path('api/categories/<slug:slug>/', views.category_detail_api, name='category_detail_api'),
]
