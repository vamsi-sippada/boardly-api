from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def health(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('', health),
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/boards/', include('boards.urls')),
    path('api/boards/<int:board_id>/lists/<int:list_id>/cards/', include('cards.urls')),
    path('api/notifications/', include('notifications.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)