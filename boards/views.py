from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Board, BoardMember, List
from .serializers import BoardSerializer, BoardDetailSerializer, BoardMemberSerializer, AddMemberSerializer, ListSerializer

User = get_user_model()

class BoardViewSet(viewsets.ModelViewSet):
    """
    list     → GET  /api/boards/
    create   → POST /api/boards/
    retrieve → GET  /api/boards/{id}/
    update   → PUT  /api/boards/{id}/
    destroy  → DELETE /api/boards/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Users only see boards where they have a membership.
        This covers both boards they own and boards they were invited to.
        """
        return Board.objects.filter(members__user=self.request.user).select_related('owner').prefetch_related('memberships__user', 'lists')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BoardDetailSerializer
        return BoardSerializer
    
    def perform_create(self, serializer):
        """
        When a board is created:
        1. Set owner to the logged-in user
        2. Automatically create an OWNER membership for them
        """
        board = serializer.save(owner=self.request.user)
        BoardMember.objects.create(
            board=board,
            user=self.request.user,
            role=BoardMember.Role.OWNER
        )

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        """
        POST /api/boards/{id}/add_member/
        Body: {"user_id": 3, "role": "member"}
        Only the board owner can add members.
        """
        board =self.get_object()

        #Only owner can add members
        membership = get_object_or_404(BoardMember, board=board, user=request.user)
        if membership.role != BoardMember.Role.OWNER:
            return Response({"detail": "Only the board owner can add members."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user_id']
        role = serializer.validated_data['role']

        #prevent adding the owner again
        if user == request.user:
            return Response({"detail": "Owner is already a member."}, status=status.HTTP_400_BAD_REQUEST)
        
        # update_or_create - if membership exists update role, else create it
        member, created = BoardMember.objects.update_or_create(
            board=board,
            user=user,
            defaults={'role': role}
        )
        return Response(BoardMemberSerializer(member).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], url_path='remove_member/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        """
        DELETE /api/boards/{id}/remove_member/{user_id}/
        Only the board owner can remove members.
        """
        board = self.get_object()

        # Only owner can remove members
        membership = get_object_or_404(BoardMember, board=board, user=request.user)
        if membership.role != BoardMember.Role.OWNER:
            return Response({"detail": "Only the board owner can remove members."}, status=status.HTTP_403_FORBIDDEN)

        target = get_object_or_404(User, pk=user_id)
        if target == request.user:
            return Response({"detail": "Owner cannot remove themselves."}, status=status.HTTP_400_BAD_REQUEST)
        
        BoardMember.objects.filter(board=board, user=target).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ListViewSet(viewsets.ModelViewSet):
    """
    Nested under boards:
    GET  /api/boards/{board_id}/lists/
    POST /api/boards/{board_id}/lists/
    GET  /api/boards/{board_id}/lists/{id}/
    etc.
    """
    serializer_class = ListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Only return lists for boards the user is a member of.
        board_id comes from the nested URL.
        """
        return List.objects.filter(board_memberships__user=self.request.user, 
                                   board_id=self.kwargs['board_id']
                                   ).select_related('board')
    
    def perform_create(self, serializer):
        board = get_object_or_404(Board, pk=self.kwargs['board_id'], memberships__user=self.request.user)
        serializer.save(board=board)
