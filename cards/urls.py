from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CardViewSet, CommentViewSet, ActivityLogViewSet

card_router = DefaultRouter()
card_router.register('', CardViewSet, basename='card')

comment_router = DefaultRouter()
comment_router.register('', CommentViewSet, basename='comment')

activity_router = DefaultRouter()
activity_router.register('', ActivityLogViewSet, basename='activity')

urlpatterns = [
    path('', include(card_router.urls)),
    path('<int:card_id>/comments/',  include(comment_router.urls)),
    path('<int:card_id>/activity/',  include(activity_router.urls)),
]