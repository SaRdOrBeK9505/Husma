from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.hudud.urls')),
    path('api/', include('apps.makler.urls')),
    path('api/', include('apps.ariza.urls')),
    path('api/', include('apps.review.urls')),
    # path('api/', include('apps.kvartira.urls')),  # Hozircha ishlatilmaydi
    path('api/', include('apps.settings.urls')),
    path('api/', include('apps.obuna.urls')),

    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)