from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from boards.models import List, BoardMember
from .models import Card, CardMember, Comment, ActivityLog
from .serializers import (
    CardSerializer, CardDetailSerializer,
    CommentSerializer, ActivityLogSerializer,
    AssignMemberSerializer
)


class CardViewSet(viewsets.ModelViewSet):
    """
    Nested under lists:
    GET  /api/boards/{board_id}/lists/{list_id}/cards/
    POST /api/boards/{board_id}/lists/{list_id}/cards/
    GET  /api/boards/{board_id}/lists/{list_id}/cards/{id}/
    etc.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(
            list__board__memberships__user=self.request.user,
            list_id=self.kwargs['list_id']
        ).select_related(
            'list__board', 'created_by'
        ).prefetch_related(
            'memberships__user', 'comments__author', 'activity_logs__actor'
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CardDetailSerializer
        return CardSerializer

    def perform_create(self, serializer):
        list_obj = get_object_or_404(
            List,
            pk=self.kwargs['list_id'],
            board__memberships__user=self.request.user
        )
        serializer.save(
            list=list_obj,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_member(self, request, **kwargs):
        """
        POST /api/.../cards/{id}/assign/
        Body: {"user_id": 3}
        """
        card = self.get_object()
        serializer = AssignMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user_id']

        # Verify user is a board member before assigning
        board = card.list.board
        if not BoardMember.objects.filter(board=board, user=user).exists():
            return Response(
                {'detail': 'User is not a member of this board.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        CardMember.objects.get_or_create(card=card, user=user)
        return Response(
            {'detail': f'{user.username} assigned to card.'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'],
            url_path='unassign/(?P<user_id>[^/.]+)')
    def unassign_member(self, request, user_id=None, **kwargs):
        """DELETE /api/.../cards/{id}/unassign/{user_id}/"""
        card = self.get_object()
        CardMember.objects.filter(card=card, user_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(viewsets.ModelViewSet):
    """
    Nested under cards:
    GET  /api/.../cards/{card_id}/comments/
    POST /api/.../cards/{card_id}/comments/
    """
    serializer_class   = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(
            card__list__board__memberships__user=self.request.user,
            card_id=self.kwargs['card_id']
        ).select_related('author')

    def perform_create(self, serializer):
        card = get_object_or_404(
            Card,
            pk=self.kwargs['card_id'],
            list__board__memberships__user=self.request.user
        )
        serializer.save(card=card, author=self.request.user)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/.../cards/{card_id}/activity/
    Read only — activity is created by signals, not the client.
    """
    serializer_class   = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ActivityLog.objects.filter(
            card__list__board__memberships__user=self.request.user,
            card_id=self.kwargs['card_id']
        ).select_related('actor')