# main/filters.py
from django_filters import rest_framework as filters
from .models import Product


class ProductFilter(filters.FilterSet):
    # ?category=hair-care
    category = filters.CharFilter(field_name="category__slug", lookup_expr="exact")

    class Meta:
        model  = Product
        fields = ("category", "brand", "available")
