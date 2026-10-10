from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("api/register/", views.RegisterView.as_view(), name="register_api"),
    path("api/login/", views.LoginView.as_view(), name="login_api"),
    path("api/logout/", views.LogoutView.as_view(), name="logout_api"),
    path("api/me/", views.MeView.as_view(), name="me_api"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
