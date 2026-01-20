from rest_framework import serializers
from .models import Category, Profile, News

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ('id', 'name', 'slug')


from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    # локализованные поля
    desc      = serializers.SerializerMethodField()
    descFull  = serializers.SerializerMethodField()

    # ► big_img будет вычисляться из существующего поля image_big
    #   (переименуйте source, если у вас другое имя, либо
    #   оставьте метод get_big_img, чтобы построить URL вручную).
    big_img = serializers.ImageField(read_only=True)

    category  = serializers.SlugRelatedField(
        read_only=True,
        slug_field='slug'
    )

    class Meta:
        model  = Product
        fields = (
            "id", "title", "brand", "category",
            "price", "available",
            "img",          # оригинал / превью
            "big_img",      # «большая» версия
            "desc", "descFull",
        )

    # ────────────── вспомогательные методы ──────────────
    def get_desc(self, obj):
        """Короткое описание на всех языках"""
        return {
            'ru': obj.desc_ru,
            'uz': obj.desc_uz,
            'en': obj.desc_en,
        }

    def get_descFull(self, obj):
        """Полное описание – только на текущем языке запроса"""
        lang = self.context['request'].LANGUAGE_CODE   # 'ru', 'uz', 'en'
        return getattr(obj, f'desc_full_{lang}', '')


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Profile
        fields = (
            "name", "surname", "email", "phone",
            "birth_day", "birth_month", "birth_year", "gender",
        )



class NewsSerializer(serializers.ModelSerializer):
    # вычисляемые поля
    title          = serializers.SerializerMethodField()
    desc           = serializers.SerializerMethodField()
    banner_bg_url  = serializers.ImageField(source="banner_bg", read_only=True)
    large_img_url  = serializers.ImageField(source="large_img", read_only=True)
    photo_card     = serializers.ImageField(source="thumbnail", read_only=True)

    class Meta:
        model  = News
        fields = [
            "id",
            "title",
            "desc",
            "banner_bg_url",
            "large_img_url",
            "photo_card",
            "is_featured",
        ]

    def get_title(self, obj):
        # вытягиваем текущий язык из request
        request = self.context.get("request", None)
        lang    = getattr(request, "LANGUAGE_CODE", "")
        if lang.startswith("uz"):
            return obj.title_uz or obj.title_ru
        if lang.startswith("en"):
            return obj.title_en or obj.title_ru
        return obj.title_ru

    def get_desc(self, obj):
        request = self.context.get("request", None)
        lang    = getattr(request, "LANGUAGE_CODE", "")
        if lang.startswith("uz"):
            return obj.desc_uz or obj.desc_ru
        if lang.startswith("en"):
            return obj.desc_en or obj.desc_ru
        return obj.desc_ru
