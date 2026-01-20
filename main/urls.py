from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from .views import csrf_cookie

from .views import (
    CategoryViewSet,
    ProductViewSet,
    ProfileViewSet,
    NewsViewSet,
    api_order_create,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products',   ProductViewSet,   basename='product')
router.register(r'profile',    ProfileViewSet,   basename='profile')
router.register(r'news',         NewsViewSet,          basename='news')

urlpatterns = [
    path('', include(router.urls)),
    path('orders/', api_order_create, name='api_order_create'),
    path("csrf/", csrf_cookie)

]
