from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Board, BoardMember

User = get_user_model()


class BoardTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        # Create two users
        self.alice = User.objects.create_user(
            username='alice', password='testpass123'
        )
        self.bob = User.objects.create_user(
            username='bob', password='testpass123'
        )
        self.charlie = User.objects.create_user(
            username='charlie', password='testpass123'
        )

        # Alice creates a board — she becomes OWNER automatically
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/boards/', {
            'title': 'Alice Board',
            'visibility': 'private'
        })
        self.board_id = response.data['id']

        # Add Bob as MEMBER
        self.client.post(f'/api/boards/{self.board_id}/add_member/', {
            'user_id': self.bob.id,
            'role': 'member'
        })

        # Add Charlie as VIEWER
        self.client.post(f'/api/boards/{self.board_id}/add_member/', {
            'user_id': self.charlie.id,
            'role': 'viewer'
        })

    # ── Visibility tests ──────────────────────────────────────────────────────

    def test_owner_can_see_board(self):
        """Board owner can retrieve board detail."""
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(f'/api/boards/{self.board_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Alice Board')

    def test_member_can_see_board(self):
        """Board member can retrieve board detail."""
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/boards/{self.board_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_can_see_board(self):
        """Viewer can retrieve board detail."""
        self.client.force_authenticate(user=self.charlie)
        response = self.client.get(f'/api/boards/{self.board_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_member_cannot_see_board(self):
        """User with no membership gets 404 — board doesn't exist for them."""
        outsider = User.objects.create_user(
            username='outsider', password='testpass123'
        )
        self.client.force_authenticate(user=outsider)
        response = self.client.get(f'/api/boards/{self.board_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── Delete permission tests ───────────────────────────────────────────────

    def test_owner_can_delete_board(self):
        """Only the board owner can delete the board."""
        self.client.force_authenticate(user=self.alice)
        response = self.client.delete(f'/api/boards/{self.board_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_member_cannot_delete_board(self):
        """Members cannot delete the board."""
        self.client.force_authenticate(user=self.bob)
        response = self.client.delete(f'/api/boards/{self.board_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_delete_board(self):
        """Viewers cannot delete the board."""
        self.client.force_authenticate(user=self.charlie)
        response = self.client.delete(f'/api/boards/{self.board_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Member management tests ───────────────────────────────────────────────

    def test_owner_can_add_member(self):
        """Owner can add a new member to the board."""
        new_user = User.objects.create_user(
            username='newuser', password='testpass123'
        )
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            f'/api/boards/{self.board_id}/add_member/',
            {'user_id': new_user.id, 'role': 'member'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            BoardMember.objects.filter(
                board_id=self.board_id, user=new_user
            ).exists()
        )

    def test_member_cannot_add_member(self):
        """Members cannot add other members."""
        new_user = User.objects.create_user(
            username='newuser', password='testpass123'
        )
        self.client.force_authenticate(user=self.bob)
        response = self.client.post(
            f'/api/boards/{self.board_id}/add_member/',
            {'user_id': new_user.id, 'role': 'member'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_creation_creates_owner_membership(self):
        """Creating a board automatically creates an OWNER membership."""
        self.client.force_authenticate(user=self.alice)
        membership = BoardMember.objects.get(
            board_id=self.board_id, user=self.alice
        )
        self.assertEqual(membership.role, BoardMember.Role.OWNER)