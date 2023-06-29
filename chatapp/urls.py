from django.urls import path
from chatapp.views import (
    UserRegistrationView,
    OnlineUsersView,
    MessageListView,
    LoginAPIView,
    StartChatAPIView,
    SendChatAPIView,
    SuggestedFriendsView
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user_registration'),
    path('login/', LoginAPIView.as_view(), name='user_login'),
    path('online-users/', OnlineUsersView.as_view(), name='online_users'),
    path('messages/<int:receiver_id>/', MessageListView.as_view(), name='message_list'),
    path('chat/start/', StartChatAPIView.as_view(), name='chat_start'),
    path('chat/send/', SendChatAPIView.as_view(), name='chat_send'),
    path('suggested-friends/<int:user_id>/', SuggestedFriendsView.as_view(), name='suggested_friends'),
]
