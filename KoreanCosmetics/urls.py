# KoreanCosmetics/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("main.urls")),   # ваш DRF
]

if settings.DEBUG:
    # Сначала отрабатываем static и media
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)

# В самый конец — “ловим” всё остальное, что не admin и не api
urlpatterns += [
    re_path(
        r"^(?!admin/|api/).*$",
        TemplateView.as_view(template_name="main/index.html"),
        name="spa-fallback",
    ),
]
