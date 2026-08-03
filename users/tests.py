from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

User = get_user_model()


class AuthTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url    = '/api/auth/login/'
        self.profile_url  = '/api/auth/profile/'

    def test_register_success(self):
        """A new user can register with valid credentials."""
        data = {
            'username': 'alice',
            'email':    'alice@test.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['username'], 'alice')
        # Password must never appear in response
        self.assertNotIn('password', response.data)

    def test_register_missing_password(self):
        """Registration fails without a password."""
        data = {'username': 'alice', 'email': 'alice@test.com'}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_duplicate_username(self):
        """Registration fails if username already exists."""
        User.objects.create_user(username='alice', password='testpass123')
        data = {'username': 'alice', 'password': 'testpass123'}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Registered user can log in and receives access and refresh tokens."""
        User.objects.create_user(username='alice', password='testpass123')
        data = {'username': 'alice', 'password': 'testpass123'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        """Login fails with incorrect password."""
        User.objects.create_user(username='alice', password='testpass123')
        data = {'username': 'alice', 'password': 'wrongpassword'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_requires_auth(self):
        """Profile endpoint returns 401 for unauthenticated requests."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_own_data(self):
        """Authenticated user gets their own profile data."""
        alice = User.objects.create_user(
            username='alice',
            email='alice@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=alice)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'alice')
        self.assertEqual(response.data['email'], 'alice@test.com')