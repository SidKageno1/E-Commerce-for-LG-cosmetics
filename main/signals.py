# main/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Order, Notification

User = get_user_model()

@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """
    При создании заказа собираем расширенный текст уведомления
    и сохраняем запись в Notification.
    """
    if not created:
        return

    user = instance.user
    profile = getattr(user, "profile", None) if user else None

    # Имя и фамилия
    if user:
        if profile and (profile.name or profile.surname):
            first_name = profile.name or ""
            last_name  = profile.surname or ""
        else:
            # fallback к стандартным полям User
            first_name = getattr(user, "first_name", "") or getattr(user, "username", "Гость")
            last_name  = getattr(user, "last_name", "")
        # Почта
        email = (getattr(profile, "email", "") if profile and getattr(profile, "email", "") else getattr(user, "email", "")) or ""
        # Телефон
        phone = (getattr(profile, "phone", "") if profile and getattr(profile, "phone", "") else getattr(user, "phone", "")) or ""
    else:
        # Анонимный заказ
        first_name = "Гость"
        last_name  = ""
        email = ""
        phone = ""

    # Способ оплаты
    payment_display = instance.get_payment_method_display()

    # Сколько всего штук?
    total_items = sum(item.get("quantity", 0) for item in instance.items)

    # Собираем текст по строчкам
    lines = [
        f"Новый заказ #{instance.id}",
        f"Пользователь: {first_name} {last_name}",
        f"Email: {email}",
        f"Телефон: {phone}",
        f"Оплата: {payment_display}",
        f"Всего товаров: {total_items}",
        "Состав заказа:"
    ]

    # Добавляем каждую позицию
    for item in instance.items:
        title    = item.get("title", "—")
        qty      = item.get("quantity", 0)
        price    = item.get("price", 0)
        subtotal = price * qty
        lines.append(f"  • {title} × {qty} — {subtotal} UZS")

    # Финальный текст
    message = "\n".join(lines)

    # Сохраняем уведомление
    Notification.objects.create(
        notif_type="order",
        order=instance,
        message=message
    )
