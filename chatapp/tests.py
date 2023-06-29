from chatapp.models import User
from django.urls import reverse
from rest_framework import status
from django.test import TestCase, Client


class ChatAppTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('user_registration')
        self.login_url = reverse('user_login')
        self.online_users_url = reverse('online_users')
        self.start_chat_url = reverse('chat_start')
        self.send_message_url = reverse('chat_send')
        self.suggested_friends_url = reverse('suggested_friends', args=[145])

    def test_user_registration(self):
        # Test user registration with valid data
        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'email': 'test@example.com'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test user registration with invalid data
        invalid_data = {
            'username': '',
            'password': 'testpassword',
            'email': 'test@example.com'
        }
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        register = self.test_user_registration()
        # Test user login with valid credentials
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test user login with invalid credentials
        invalid_data = {
            'username': 'testuser',
            'password': 'invalidpassword'
        }
        response = self.client.post(self.login_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_online_users(self):
        register = self.test_user_registration()
        # create a online user
        online_user = User.objects.create(username='onlineuser',email='onlineuser@gmail.com',password='password',online=True)
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(self.login_url, data)
        # Test retrieving online users
        response = self.client.get(self.online_users_url, HTTP_AUTHORIZATION=f"Bearer {response.json()['token']['access']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_start_chat(self):
        register = self.test_user_registration()
        # create a online user
        online_user = User.objects.create(username='onlineuser',email='onlineuser@gmail.com',password='password',online=True)
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        login_response = self.client.post(self.login_url, data)
        # Test starting a chat with a valid recipient who is online
        data = {
            'recipient_id': 2
        }
        response = self.client.post(self.start_chat_url, data, HTTP_AUTHORIZATION=f"Bearer {login_response.json()['token']['access']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test starting a chat with a recipient who is unavailable
        invalid_data = {
            'recipient_id': 5
        }
        response = self.client.post(self.start_chat_url, invalid_data, HTTP_AUTHORIZATION=f"Bearer {login_response.json()['token']['access']}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # create a offline user
        User.objects.create(username='offlineuser',email='offlineuser@gmail.com',password='password')
        
        # Test starting a chat with a recipient who is offline
        invalid_data = {
            'recipient_id': 3
        }
        response = self.client.post(self.start_chat_url, invalid_data, HTTP_AUTHORIZATION=f"Bearer {login_response.json()['token']['access']}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_message(self):
        register = self.test_user_registration()
        # create a online user
        online_user = User.objects.create(username='onlineuser',email='onlineuser@gmail.com',password='password',online=True)
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        login_response = self.client.post(self.login_url, data)

        # Test sending a message to a valid recipient who is online
        data = {
            'recipient_id': 2,
            'message': 'Hello, recipient!'
        }
        response = self.client.post(self.send_message_url, data, HTTP_AUTHORIZATION=f"Bearer {login_response.json()['token']['access']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test sending a message to a recipient who is unavailable
        invalid_data = {
            'recipient_id': 5,
            'message': 'Hello, recipient!'
        }
        response = self.client.post(self.send_message_url, invalid_data, HTTP_AUTHORIZATION=f"Bearer {login_response.json()['token']['access']}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # create a offline user
        User.objects.create(username='offlineuser',email='offlineuser@gmail.com',password='password')

        # Test sending a message to a recipient who is offline
        invalid_data = {
            'recipient_id': 3,
            'message': 'Hello, recipient!'
        }
        response = self.client.post(self.send_message_url, invalid_data, HTTP_AUTHORIZATION=f"Bearer {login_response.json()['token']['access']}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_suggested_friends(self):
        # Test retrieving suggested friends for a valid user
        response = self.client.get(self.suggested_friends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

