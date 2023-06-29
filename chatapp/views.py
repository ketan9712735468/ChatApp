import json
from chatapp.models import User, Message
from asgiref.sync import async_to_sync
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from channels.layers import get_channel_layer
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserSerializer, LoginSerializer, UserProfileSerializer, MessageSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class UserRegistrationView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def perform_create(self, serializer):
        password = make_password(self.request.data.get('password'))
        serializer.save(password=password)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(username=serializer.validated_data['username']).first()
        data = {
            "user":{
                "username":user.username,
                "email":user.email
            },
            "token":get_tokens_for_user(user)
        }

        return Response(data, status=status.HTTP_200_OK)


class OnlineUsersView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return User.objects.filter(online=True)


class MessageListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer

    def get_queryset(self):
        sender = self.request.user
        receiver_id = self.kwargs.get('receiver_id')
        return Message.objects.filter(sender=sender, receiver_id=receiver_id)


class StartChatAPIView(APIView):
    def post(self, request):
        recipient_id = request.data.get('recipient_id')
        try:
            user = User.objects.filter(id=recipient_id).first()
            if user.online:
                return Response({'message': 'Chat started successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Recipient is offline or unavailable'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"message":"User not found"}, status=status.HTTP_404_NOT_FOUND)


class SendChatAPIView(APIView):
    def post(self, request):
        sender_id = request.user.id
        recipient_id = request.data.get('recipient_id')
        message_content = request.data.get('message')

        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return Response({'message': 'User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        if receiver.online:
            message = Message(sender=sender, receiver=receiver, content=message_content)
            message.save()

            # Send the message through the WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{recipient_id}',
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender_id': sender_id,
                }
            )
            return Response({'success': 'Message sent successfully.'}, status=200)
        else:
            return Response({'error': 'Recipient is offline.'}, status=status.HTTP_400_BAD_REQUEST)


class SuggestedFriendsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, user_id):
        f = open('static/users.json')
        all_users = json.load(f)
        _user = [user for user in all_users['users'] if user["id"] == user_id][0]
        recommended_friends = self.get_recommended_friends(_user, all_users['users'])
        return Response(recommended_friends)

    def get_recommended_friends(self, user, all_users):
        # Calculate similarity scores between the user and all other users
        similarity_scores = []
        for other_user in all_users:
            if user != other_user['id']:
                score = self.calculate_similarity_score(user, other_user)
                similarity_scores.append((other_user, score))

        # Sort the users based on similar scores in descending order
        similarity_scores.sort(key=lambda x: x[1], reverse=True)

        # Return the top 5 users with the highest similarity scores as recommended friends
        recommended_friends = [user for user, _ in similarity_scores[1:6]]
        return recommended_friends

    def calculate_similarity_score(self, user1, user2):
        # Calculate the similarity score between two users based on their interests and age
        interest_score = self.calculate_interest_score(user1['interests'], user2['interests'])
        age_score = self.calculate_age_score(user1['age'], user2['age'])

        # Calculate the overall similarity score as a weighted average
        overall_score = (0.6 * interest_score) + (0.4 * age_score)
        return overall_score

    def calculate_interest_score(self, interests1, interests2):
        # Calculate the similarity score based on common interests between two users
        common_interests = set(interests1.keys()) & set(interests2.keys())
        total_score = sum(min(interests1[interest], interests2[interest]) for interest in common_interests)
        return total_score

    def calculate_age_score(self, age1, age2):
        # Calculate the similarity score based on the difference in ages
        age_difference = abs(age1 - age2)
        age_score = max(100 - age_difference, 0)
        return age_score
