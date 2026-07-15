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
from .permissions import IsCardBoardMember, IsCommentAuthorOrBoardOwner


class CardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCardBoardMember]

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
        # Viewers cannot create cards
        membership = get_object_or_404(
            BoardMember,
            board=list_obj.board,
            user=self.request.user
        )
        if membership.role == BoardMember.Role.VIEWER:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Viewers cannot create cards.')

        serializer.save(
            list=list_obj,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        # Attach request.user to instance so the signal can access it
        instance = serializer.instance
        instance._updated_by = self.request.user
        serializer.save()

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_member(self, request, **kwargs):
        card = self.get_object()
        serializer = AssignMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user_id']
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
        card = self.get_object()
        CardMember.objects.filter(card=card, user_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthorOrBoardOwner]

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
    serializer_class   = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ActivityLog.objects.filter(
            card__list__board__memberships__user=self.request.user,
            card_id=self.kwargs['card_id']
        ).select_related('actor')