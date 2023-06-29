from rest_framework import serializers
from chatapp.models import User, Message
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        username = data.get('username', None)
        password = data.get('password', None)

        if password is None:
            raise serializers.ValidationError(
                'A password is required to log in.'
            )
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password was not found.'
            )
        if not user.is_active:
            raise serializers.ValidationError(
                'This user has been deactivated.'
            )
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'online', 'first_name', 'last_name')

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('sender', 'receiver', 'content', 'timestamp')
