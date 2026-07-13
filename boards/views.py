from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Board, BoardMember, List
from .serializers import (
    BoardSerializer, BoardDetailSerializer,
    BoardMemberSerializer, AddMemberSerializer,
    ListSerializer
)
from .permissions import IsBoardMember, IsBoardOwner, IsBoardMemberOrReadOnly

User = get_user_model()


class BoardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Board.objects.filter(
            memberships__user=self.request.user
        ).select_related('owner').prefetch_related('memberships__user', 'lists')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BoardDetailSerializer
        return BoardSerializer

    def get_permissions(self):
        """
        Return different permission classes depending on the action.
        This is the key pattern — one ViewSet, multiple permission levels.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only owners can edit or delete a board
            return [permissions.IsAuthenticated(), IsBoardOwner()]
        if self.action in ['retrieve', 'list']:
            # Any member can view
            return [permissions.IsAuthenticated(), IsBoardMember()]
        # create — just needs to be authenticated
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
        BoardMember.objects.create(
            board=board,
            user=self.request.user,
            role=BoardMember.Role.OWNER
        )

    @action(detail=True, methods=['post'], url_path='add_member')
    def add_member(self, request, pk=None):
        board = self.get_object()

        # Permission check — only owner can add members
        role = BoardMember.objects.filter(
            board=board, user=request.user
        ).values_list('role', flat=True).first()

        if role != BoardMember.Role.OWNER:
            return Response(
                {'detail': 'Only the board owner can add members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user_id']
        role_to_assign = serializer.validated_data['role']

        if user == request.user:
            return Response(
                {'detail': 'Owner is already a member.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        member, created = BoardMember.objects.update_or_create(
            board=board,
            user=user,
            defaults={'role': role_to_assign}
        )
        return Response(
            BoardMemberSerializer(member).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=True, methods=['delete'],
            url_path='remove_member/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        board = self.get_object()

        role = BoardMember.objects.filter(
            board=board, user=request.user
        ).values_list('role', flat=True).first()

        if role != BoardMember.Role.OWNER:
            return Response(
                {'detail': 'Only the board owner can remove members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target = get_object_or_404(User, pk=user_id)
        if target == request.user:
            return Response(
                {'detail': 'Owner cannot remove themselves.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        BoardMember.objects.filter(board=board, user=target).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return List.objects.filter(
            board__memberships__user=self.request.user,
            board_id=self.kwargs['board_id']
        ).select_related('board')

    def get_serializer_class(self):
        return ListSerializer

    def get_permissions(self):
        """
        Viewers can read lists but cannot create, edit, or delete them.
        Only members and owners can modify lists.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated(), IsBoardMemberOrReadOnly()]
        # create, update, destroy — member or owner only
        return [permissions.IsAuthenticated(), IsBoardMemberOrReadOnly()]

    def perform_create(self, serializer):
        board = get_object_or_404(
            Board,
            pk=self.kwargs['board_id'],
            memberships__user=self.request.user
        )
        # Viewers cannot create lists
        role = get_object_or_404(
            BoardMember,
            board=board,
            user=self.request.user
        ).role
        if role == BoardMember.Role.VIEWER:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Viewers cannot create lists.')
        serializer.save(board=board)