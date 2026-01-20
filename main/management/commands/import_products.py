# main/management/commands/import_products.py
import json, pathlib
from django.core.management.base import BaseCommand
from main.models import Category, Product

class Command(BaseCommand):
    help = 'Импорт из products.json'

    def handle(self, *args, **kwargs):
        data = json.loads(pathlib.Path('products.json').read_text(encoding='utf-8'))
        added, updated = 0, 0

        for raw in data:
            cat, _ = Category.objects.get_or_create(
                slug=raw['category'],
                defaults={'name': raw['category']}
            )

            p, created = Product.objects.update_or_create(
                title=raw['title'],
                defaults={
                    'brand'        : raw['brand'],
                    'category'     : cat,
                    'price'        : raw['price'],
                    'available'    : raw.get('available', True),
                    'img'          : f"product/{raw['img']}.png",
                    'big_img'      : f"product/{raw['bigImg']}.png",  # <-- имя поля в модели
                    'desc_ru'      : raw['desc']['ru'],
                    'desc_uz'      : raw['desc']['uz'],
                    'desc_en'      : raw['desc']['en'],
                    'desc_full_ru' : raw['descFull']['ru'],
                    'desc_full_uz' : raw['descFull']['uz'],
                    'desc_full_en' : raw['descFull']['en'],
                }
            )
            added += created
            updated += (not created)

        self.stdout.write(self.style.SUCCESS(f'✅ added={added}, updated={updated}'))
