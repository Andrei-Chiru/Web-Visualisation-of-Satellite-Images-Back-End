from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from api.serializers import UserSerializer
from unittest.mock import patch, MagicMock

LOCAL_TESTING = False

# Serializer Tests
class UserSerializerTest(TestCase):
    def test_create_user_with_valid_data(self):
        data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.username, 'newuser')

    def test_create_user_with_invalid_data(self):
        data = {
            'username': '',
            'password': 'newpass123'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertEqual(User.objects.count(), 0)


# View Tests
class ServeImageViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('builtins.open', new_callable=MagicMock)
    def test_serve_image_success(self, mock_open):
        # Mock the behavior of open
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.get(reverse('serve_image'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/webp')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_serve_image_file_not_found(self, mock_open):
        response = self.client.get(reverse('serve_image'))
        self.assertEqual(response.status_code, 404)


class CreateUserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_with_valid_data(self):
        data = {'username': 'newuser', 'password': 'newpass'}
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_with_invalid_data(self):
        data = {'username': '', 'password': 'newpass'}
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_create_user_with_existing_username(self):
        User.objects.create_user(username='newuser', password='newpass')
        data = {'username': 'newuser', 'password': 'anotherpass'}
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 1)

