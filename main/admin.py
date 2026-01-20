# main/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, Profile, Order, Notification, News


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # ---------- список объектов ----------
    list_display  = (
        "id", "title", "brand", "category",
        "price", "available", "thumb",
    )
    list_filter   = ("available", "category", "brand")
    search_fields = ("title", "brand")

    # ---------- только для формы ----------
    readonly_fields = ("thumb", "category_slug")

    # ---------- расположение блоков ----------
    fieldsets = (
        ('Основное', {'fields': ('title', 'brand', 'category', ('price', 'available'))}),
        ('Картинки', {'fields': ('img', 'big_img', 'thumb')}),
        ('Короткие описания', {  # ⚠️ шесть отдельных полей
            'fields': (('desc_ru', 'desc_uz', 'desc_en'),)
        }),
        ('Полные описания', {
            'fields': (('desc_full_ru', 'desc_full_uz', 'desc_full_en'),)
        }),
    )

    # ---------- превью картинки ----------
    def thumb(self, obj):
        """
        Показывает мини-картинку, если img – FileField.
        Если там просто строка (путь или имя), выводит её текстом,
        чтобы список товаров хотя бы открылся.
        """
        if obj.img:
            # вариант «нормального» Image/FileField
            if hasattr(obj.img, "url"):
                return format_html('<img src="{}" style="height:60px;" />', obj.img.url)

            # вариант импортированной строки
            return obj.img  # будет показан текстом

        return "—"

    thumb.short_description = "Фото"

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ("id", "user_display", "name", "surname", "phone", "address")
    search_fields = ("user__username", "name", "surname", "phone", "email", "address")

    @admin.display(description="User", ordering="user__username")
    def user_display(self, obj):
        """Показываем username или «—» для анонимов."""
        return obj.user.username if obj.user_id else "—"

class NotificationInline(admin.TabularInline):
    model = Notification
    fields = ('notif_type', 'message', 'created_at', 'is_read')
    readonly_fields = ('notif_type', 'message', 'created_at')
    extra = 0
    can_delete = False
    verbose_name = "Уведомление"
    verbose_name_plural = "Уведомления"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_customer_name',
        'get_customer_phone',
        'get_customer_address',
        'payment_method',
        'created_at',
        'all_read',
    )
    list_filter = ('payment_method',)
    search_fields = ('user__username', 'user__profile__name', 'items')
    readonly_fields = (
        'get_customer_firstname',
        'get_customer_lastname',
        'get_customer_phone',
        'get_customer_address',
        'items',
        'created_at',
    )
    fields = (
        'user',
        'payment_method',
        'get_customer_firstname',
        'get_customer_lastname',
        'get_customer_phone',
        'get_customer_address',
        'items',
        'created_at',
    )
    inlines = (NotificationInline,)

    # Имя клиента (для формы)
    def get_customer_firstname(self, obj):
        user = obj.user
        # Если авторизованный — всегда профиль
        if user and hasattr(user, "profile") and user.profile.name:
            return user.profile.name
        # Гость: ищем в первом элементе items
        items = obj.items or []
        if items and isinstance(items[0], dict):
            return items[0].get("name", "")
        return ""
    get_customer_firstname.short_description = "Имя клиента"

    # Фамилия клиента (для формы)
    def get_customer_lastname(self, obj):
        user = obj.user
        if user and hasattr(user, "profile") and user.profile.surname:
            return user.profile.surname
        items = obj.items or []
        if items and isinstance(items[0], dict):
            return items[0].get("surname", "")
        return ""
    get_customer_lastname.short_description = "Фамилия клиента"

    # Телефон клиента (для формы)
    def get_customer_phone(self, obj):
        user = obj.user
        if user and hasattr(user, "profile") and user.profile.phone:
            return user.profile.phone
        items = obj.items or []
        if items and isinstance(items[0], dict):
            return items[0].get("phone", "")
        return ""
    get_customer_phone.short_description = "Телефон клиента"

    # Адрес клиента (для формы и списка)
    def get_customer_address(self, obj):
        user = obj.user
        if user and hasattr(user, "profile") and user.profile.address:
            return user.profile.address
        items = obj.items or []
        if items and isinstance(items[0], dict):
            return items[0].get("address", "")
        return ""
    get_customer_address.short_description = "Адрес клиента"

    # Для списка заказов — ФИО или ник (корректный fallback)
    def get_customer_name(self, obj):
        user = obj.user
        if user and hasattr(user, "profile"):
            prof = user.profile
            full_name = f"{prof.name or ''} {prof.surname or ''}".strip()
            if full_name:
                return full_name
            return user.get_full_name() or user.username or "Клиент"
        # Гость: имя+фамилия в items[0], если есть
        items = obj.items or []
        if items and isinstance(items[0], dict):
            name = items[0].get("name", "")
            surname = items[0].get("surname", "")
            full_name = f"{name} {surname}".strip()
            if full_name:
                return full_name
        return "Гость"
    get_customer_name.short_description = "Клиент"

    def all_read(self, obj):
        return not obj.notifications.filter(is_read=False).exists()
    all_read.boolean = True
    all_read.short_description = 'Прочитано'

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title_ru",       # при желании можно подменять на title_en / title_uz
        "is_featured",
        "created_at",
    )
    list_filter = (
        "is_featured",
        "created_at",
    )
    search_fields = ("title_ru", "title_en", "title_uz")
    fieldsets = (
        (_("Контент"), {
            "fields": (
                ("title_ru", "title_en", "title_uz"),
                ("desc_ru", "desc_en", "desc_uz"),
            )
        }),
        (_("Изображения"), {
            "fields": (
                "is_featured",
                ("banner_bg", "large_img", "thumbnail"),
            )
        }),
        (_("Служебное"), {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at",)