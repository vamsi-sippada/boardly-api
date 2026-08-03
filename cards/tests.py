from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from boards.models import Board, BoardMember
from boards.models import List
from .models import Card, ActivityLog
from notifications.models import Notification

User = get_user_model()


class CardTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.alice = User.objects.create_user(
            username='alice', password='testpass123'
        )
        self.bob = User.objects.create_user(
            username='bob', password='testpass123'
        )
        self.viewer = User.objects.create_user(
            username='viewer_user', password='testpass123'
        )

        # Create board as alice
        self.client.force_authenticate(user=self.alice)
        board_response = self.client.post('/api/boards/', {
            'title': 'Test Board',
            'visibility': 'private'
        })
        self.board_id = board_response.data['id']

        # Add bob as member, viewer as viewer
        self.client.post(f'/api/boards/{self.board_id}/add_member/', {
            'user_id': self.bob.id, 'role': 'member'
        })
        self.client.post(f'/api/boards/{self.board_id}/add_member/', {
            'user_id': self.viewer.id, 'role': 'viewer'
        })

        # Create a list
        list_response = self.client.post(
            f'/api/boards/{self.board_id}/lists/',
            {'title': 'To Do', 'position': 0}
        )
        self.list_id = list_response.data['id']
        self.cards_url = f'/api/boards/{self.board_id}/lists/{self.list_id}/cards/'

    def test_member_can_create_card(self):
        """Board members can create cards."""
        self.client.force_authenticate(user=self.bob)
        response = self.client.post(self.cards_url, {
            'title': 'Fix bug',
            'priority': 'high',
            'status': 'todo',
            'position': 0
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Fix bug')

    def test_viewer_cannot_create_card(self):
        """Viewers cannot create cards."""
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post(self.cards_url, {
            'title': 'Fix bug',
            'priority': 'high',
            'status': 'todo',
            'position': 0
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_card_creation_creates_activity_log(self):
        """Creating a card automatically creates an ActivityLog entry."""
        self.client.force_authenticate(user=self.alice)
        self.client.post(self.cards_url, {
            'title': 'Signal test card',
            'priority': 'medium',
            'status': 'todo',
            'position': 0
        })
        # Signal should have created an activity log
        self.assertTrue(
            ActivityLog.objects.filter(
                verb__contains='Signal test card'
            ).exists()
        )

    def test_card_creation_notifies_board_members(self):
        """Creating a card sends notifications to other board members."""
        initial_count = Notification.objects.count()
        self.client.force_authenticate(user=self.alice)
        self.client.post(self.cards_url, {
            'title': 'Notify test card',
            'priority': 'low',
            'status': 'todo',
            'position': 0
        })
        # Bob and viewer should have been notified (not alice — she's excluded)
        self.assertGreater(Notification.objects.count(), initial_count)

    def test_owner_can_delete_card(self):
        """Board owner can delete any card."""
        self.client.force_authenticate(user=self.alice)
        create_response = self.client.post(self.cards_url, {
            'title': 'To delete',
            'priority': 'low',
            'status': 'todo',
            'position': 0
        })
        card_id = create_response.data['id']
        delete_response = self.client.delete(
            f'{self.cards_url}{card_id}/'
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Card.objects.filter(id=card_id).exists())

    def test_viewer_cannot_delete_card(self):
        """Viewers cannot delete cards."""
        self.client.force_authenticate(user=self.alice)
        create_response = self.client.post(self.cards_url, {
            'title': 'Protected card',
            'priority': 'low',
            'status': 'todo',
            'position': 0
        })
        card_id = create_response.data['id']

        self.client.force_authenticate(user=self.viewer)
        delete_response = self.client.delete(
            f'{self.cards_url}{card_id}/'
        )
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)