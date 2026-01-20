from rest_framework import viewsets, permissions, status, filters
from .models import Product, Category, Profile, Order, Notification, News
from .serializers import ProductSerializer, CategorySerializer, ProfileSerializer, NewsSerializer
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ /api/categories/  """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'  # /api/categories/<slug>/


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/products/                         ― все доступные
    /api/products/?category=hair-care      ― по slug категории
    /api/products/?brand=Perioe            ― по бренду
    /api/products/?ordering=price          ― сортировка (price / title)
    """
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(available=True)

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'category__slug': ['exact'],
        'brand': ['exact', 'icontains'],
    }
    ordering_fields = ['id', 'price', 'title']
    ordering = ['id']

    # обязательно передаём request в сериалайзер → полные URL картинок
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class ProfileViewSet(viewsets.ModelViewSet):
    """
    Для авторизованных – как обычно.
    Для анонимов – один профиль, привязанный к session_key.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]  # контролим в коде

    # ---------- helpers -------------------------------------------------
    def _session_profile(self):
        """Вернуть Profile или None, привязанный к сессии анонима."""
        pk = self.request.session.get("profile_id")
        if pk:
            try:
                return Profile.objects.get(pk=pk, user__isnull=True)
            except Profile.DoesNotExist:
                # если профиль удалили – чистим сессию
                self.request.session.pop("profile_id", None)
        return None

    # ---------- queryset ------------------------------------------------
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Profile.objects.filter(user=user)
        sess_prof = self._session_profile()
        return Profile.objects.filter(pk=sess_prof.pk) if sess_prof else Profile.objects.none()

    # ---------- create / update ----------------------------------------
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user = request.user

        # ---- авторизованный пользователь --------------------------------
        if user.is_authenticated:
            instance, _ = Profile.objects.get_or_create(user=user)
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # ---- анонимный пользователь -------------------------------------
        instance = self._session_profile()
        if instance:
            # обновляем существующий аноним-профиль
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # создаём новый профиль без user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save(user=None)
        # запоминаем pk в сессии, чтобы этот же аноним мог получить/обновить
        self.request.session["profile_id"] = profile.pk
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        raise ValidationError({"detail": "Deleting profile via API is disabled"})


@csrf_exempt
@require_http_methods(["POST"])
def api_order_create(request):
    """
    Принимает JSON с корзиной, способом оплаты и ДАННЫМИ КЛИЕНТА (может прийти из профиля или формы).
    Создаёт Order. Уведомление генерируется в signals.post_save.
    """
    payload = json.loads(request.body)
    items = payload.get("items", [])
    payment_method = payload.get("payment_method")

    # Получаем параметры из тела запроса (если есть)
    customer_name = payload.get("customer_name", "")
    customer_surname = payload.get("customer_surname", "")
    customer_phone = payload.get("customer_phone", "")
    customer_address = payload.get("customer_address", "")

    # Если юзер авторизован и профиль заполнен — взять данные из профиля (если не передано в payload)
    user = request.user if request.user.is_authenticated else None
    if user and hasattr(user, "profile"):
        prof = user.profile
        customer_name = customer_name or getattr(prof, "name", "")
        customer_surname = customer_surname or getattr(prof, "surname", "")
        customer_phone = customer_phone or getattr(prof, "phone", "")
        customer_address = customer_address or getattr(prof, "address", "")

    order = Order.objects.create(
        user=user,
        items=items,
        payment_method=payment_method,
        customer_name=customer_name,
        customer_surname=customer_surname,
        customer_phone=customer_phone,
        customer_address=customer_address
    )

    # не создаём здесь Notification — это делает сигнал post_save
    return JsonResponse({"id": order.id}, status=201)

@login_required
@require_http_methods(["GET"])
def api_notifications_list(request):
    """
    Отдаёт все уведомления по заказам данного пользователя.
    """
    qs = Notification.objects.filter(order__user=request.user)
    data = [
        {
            "id": n.id,
            "message": n.message,
            "created_at": n.created_at.isoformat(),
            "is_read": n.is_read,
        }
        for n in qs
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["POST"])
def api_notification_mark_read(request, pk):
    """
    Пометить конкретное уведомление как прочитанное.
    """
    try:
        n = Notification.objects.get(pk=pk, order__user=request.user)
    except Notification.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    n.is_read = True
    n.save(update_fields=["is_read"])
    return JsonResponse({"status": "ok"})


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для новостей: GET /api/news/ и GET /api/news/{id}/
    """
    queryset = News.objects.order_by("-is_featured", "-created_at")
    serializer_class = NewsSerializer


@ensure_csrf_cookie
def csrf_cookie(request):
    return JsonResponse({'detail': 'CSRF cookie set'})



