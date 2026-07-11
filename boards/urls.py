from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BoardViewSet, ListViewSet

router = DefaultRouter()
router.register('', BoardViewSet, basename='board')

list_router = DefaultRouter()
list_router.register('', ListViewSet, basename='list')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:board_id>/lists/', include(list_router.urls)),
]