from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import BoardMember


def get_board_role(user, board):
    """
    Returns the role string ('owner', 'member', 'viewer')
    for this user on this board, or None if not a member.
    This is the single source of truth for all permission checks.
    """
    try:
        membership = BoardMember.objects.get(board=board, user=user)
        return membership.role
    except BoardMember.DoesNotExist:
        return None


class IsBoardMember(BasePermission):
    """
    Grants access only to users who are members of the board.
    All roles (owner, member, viewer) pass this check.
    Used as the base permission on BoardViewSet.
    """
    message = 'You are not a member of this board.'

    def has_object_permission(self, request, view, obj):
        # obj is the Board instance
        role = get_board_role(request.user, obj)
        return role is not None


class IsBoardOwner(BasePermission):
    """
    Grants access only to the board owner.
    Used for destructive actions: delete board, manage members.
    """
    message = 'Only the board owner can perform this action.'

    def has_object_permission(self, request, view, obj):
        role = get_board_role(request.user, obj)
        return role == BoardMember.Role.OWNER


class IsBoardMemberOrReadOnly(BasePermission):
    """
    Viewers can read (GET). Members and owners can write.
    Used for lists, cards, comments.
    """
    message = 'Viewers can only read. You need member access to modify content.'

    def has_object_permission(self, request, view, obj):
        # GET, HEAD, OPTIONS are always allowed for any member
        if request.method in SAFE_METHODS:
            board = get_board_from_obj(obj)
            role = get_board_role(request.user, board)
            return role is not None

        # Write actions require member or owner role
        board = get_board_from_obj(obj)
        role = get_board_role(request.user, board)
        return role in (BoardMember.Role.OWNER, BoardMember.Role.MEMBER)


def get_board_from_obj(obj):
    """
    Traverses from any object back to its parent Board.
    Needed because has_object_permission receives the actual
    object (Card, List, Comment) not the Board.
    """
    from cards.models import Card, Comment

    if isinstance(obj, BoardMember):
        return obj.board
    if hasattr(obj, 'board'):       # List has board directly
        return obj.board
    if isinstance(obj, Card):       # Card → list → board
        return obj.list.board
    if isinstance(obj, Comment):    # Comment → card → list → board
        return obj.card.list.board
    return None