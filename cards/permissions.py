from rest_framework.permissions import BasePermission, SAFE_METHODS
from boards.models import BoardMember
from boards.permissions import get_board_role, get_board_from_obj


class IsCardBoardMember(BasePermission):
    """
    Any board member can view cards.
    Only members and owners can create/edit/delete.
    """
    message = 'You do not have permission to perform this action on this card.'

    def has_object_permission(self, request, view, obj):
        board = get_board_from_obj(obj)
        if board is None:
            return False

        role = get_board_role(request.user, board)

        if request.method in SAFE_METHODS:
            return role is not None  # any member can read

        return role in (BoardMember.Role.OWNER, BoardMember.Role.MEMBER)


class IsCommentAuthorOrBoardOwner(BasePermission):
    """
    Only the comment author or board owner can edit/delete a comment.
    Any board member can read comments.
    """
    message = 'You can only edit or delete your own comments.'

    def has_object_permission(self, request, view, obj):
        # obj is a Comment instance
        board = get_board_from_obj(obj)
        role = get_board_role(request.user, board)

        if role is None:
            return False  # not a board member at all

        if request.method in SAFE_METHODS:
            return True  # any member can read

        # Edit/delete: must be author or board owner
        is_author = obj.author == request.user
        is_owner  = role == BoardMember.Role.OWNER
        return is_author or is_owner