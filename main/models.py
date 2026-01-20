# main/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)  # nullable → False\

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')

    def save(self, *args, **kwargs):
        # если slug не задали руками ― строим из name
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=200)
    price = models.PositiveIntegerField()

    # картинки
    img = models.ImageField(
        _("Мини-фото"),
        upload_to="products/",
        blank=True,
        null=True
    )
    big_img = models.ImageField(
        _("Большая картинка"),
        upload_to="products/big/",
        blank=True,
        null=True
    )

    # краткие описания
    desc_ru = models.TextField(_("Краткое описание (RU)"), blank=True)
    desc_uz = models.TextField(_("Краткое описание (UZ)"), blank=True)
    desc_en = models.TextField(_("Краткое описание (EN)"), blank=True)

    # полные описания
    desc_full_ru = models.TextField(_("Полное описание (RU)"), blank=True)
    desc_full_uz = models.TextField(_("Полное описание (UZ)"), blank=True)
    desc_full_en = models.TextField(_("Полное описание (EN)"), blank=True)

    brand = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products"
    )
    category_slug = models.SlugField(
        _("Дублирующий slug категории"),
        blank=True,
        editable=False
    )

    available = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')

    def save(self, *args, **kwargs):
        # поддерживаем синхронизацию с категорией
        if self.category:
            self.category_slug = self.category.slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        null=True,
        blank=True
    )

    # новые названия
    name = models.CharField("Имя", max_length=150, blank=True)
    surname = models.CharField("Фамилия", max_length=150, blank=True)

    email = models.EmailField("E-mail", blank=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    address = models.CharField("Адрес", max_length=300, blank=True, default="")

    birth_day = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_month = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)

    M, F, X = "M", "F", "X"
    GENDER_CHOICES = ((M, "M"), (F, "F"), (X, "X"))
    gender = models.CharField(
        "Пол",
        max_length=1,
        choices=GENDER_CHOICES,
        default=X,  # ← чтоб миграция не ругалась
        blank=True,
    )

    class Meta:
        verbose_name = _('Профиль')
        verbose_name_plural = _('Профили')

    def __str__(self):
        """Аккуратно работаем и с авторизованными, и с анонимами."""
        if self.user_id:  # есть пользователь
            return f"{self.user.username} profile"
        return f"Anon profile #{self.pk}"


class Order(models.Model):
    PAYMENT_CHOICES = [
        ("cash", "Наличными"),
        ("payme", "Payme"),
        ("click", "Click"),
        ("apelsin", "Apelsin"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True
    )
    items = models.JSONField(
        help_text="Список объектов {id, title, price, quantity}"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # --- Новые поля для хранения данных из модального окна/профиля ---
    customer_name = models.CharField("Имя клиента", max_length=100, blank=True)
    customer_surname = models.CharField("Фамилия клиента", max_length=100, blank=True)
    customer_phone = models.CharField("Телефон клиента", max_length=32, blank=True)
    customer_address = models.CharField("Адрес клиента", max_length=255, blank=True)

    def __str__(self):
        return f"Заказ #{self.id} от {self.customer_name or self.user or 'Аноним'}"
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
class Notification(models.Model):
    TYPE_CHOICES = [
        ("order", "Новый заказ"),
    ]

    notif_type = models.CharField(
        "Тип уведомления",
        max_length=20,
        choices=TYPE_CHOICES,
        default="order"
    )
    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Заказ"
    )
    message = models.TextField("Текст уведомления")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    is_read = models.BooleanField("Прочитано", default=False)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_notif_type_display()}] #{self.order.id} — {self.created_at:%d.%m.%Y %H:%M}"


class News(models.Model):
    # Заголовки на трёх языках
    title_ru = models.CharField(_("Заголовок (RU)"), max_length=200, blank=True, default="")
    title_en = models.CharField(_("Заголовок (EN)"), max_length=200, blank=True, default="")
    title_uz = models.CharField(_("Заголовок (UZ)"), max_length=200, blank=True, default="")

    desc_ru = models.TextField(_("Описание (RU)"), blank=True, default="")
    desc_en = models.TextField(_("Описание (EN)"), blank=True, default="")
    desc_uz = models.TextField(_("Описание (UZ)"), blank=True, default="")

    # Изображения
    banner_bg = models.ImageField(_("Фон баннера"), upload_to="news/banners/", blank=True, null=True)
    large_img = models.ImageField(_("Большая картинка"), upload_to="news/large/", blank=True, null=True)
    thumbnail = models.ImageField(_("Миниатюра"), upload_to="news/thumbs/", blank=True, null=True)

    # Главная новость
    is_featured = models.BooleanField(_("Главная новость"), default=False)

    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)

    class Meta:
        verbose_name = _("Новость")
        verbose_name_plural = _("Новости")
        ordering = ["-is_featured", "-created_at"]

    def __str__(self):
        # Всегда возвращаем непустую строку
        return self.title_ru or self.title_en or self.title_uz or f"Новость #{self.pk}"
