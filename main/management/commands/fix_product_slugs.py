from django.core.management.base import BaseCommand
from main.models import Product

class Command(BaseCommand):
    help = "Заполняет category_slug у товаров, где оно пустое"

    def handle(self, *args, **kwargs):
        qs = Product.objects.filter(category_slug="")
        for p in qs:
            p.category_slug = p.category.slug
            p.save(update_fields=["category_slug"])
        self.stdout.write(
            self.style.SUCCESS(f"Fixed {qs.count()} products")
        )
