import jwt
import json
from django.conf import settings
from chatapp.models import User, Message
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer


# @database_sync_to_async
# def get_user_from_token(token):
#     try:
#         decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#         user_id = decoded_token["user_id"]
#         return User.objects.get(id=user_id)
#     except (jwt.DecodeError, User.DoesNotExist):
#         return None

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
#         token = self.scope["query_string"].decode("utf-8").replace("token=", "")
#         self.sender = await get_user_from_token(token)
#         if self.sender:
#             self.receiver = await self.get_receiver()

#             if self.sender.online and self.receiver.online:
#                 await self.channel_layer.group_add(
#                     f'chat_{self.receiver_id}',
#                     self.channel_name
#                 )
#                 await self.accept()
#             else:
#                 await self.close()
#         else:
#             await self.close()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             f'chat_{self.receiver_id}',
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data['message']
#         await self.save_message(message)
#         await self.channel_layer.group_send(
#             f'chat_{self.receiver_id}',
#             {
#                 'type': 'chat_message',
#                 'message': message,
#                 'sender_id': self.sender.id,
#                 'receiver_id': self.receiver_id,
#             }
#         )

#     async def chat_message(self, event):
#         message = event['message']
#         sender_id = event['sender_id']
#         receiver_id = event['receiver_id']
#         await self.send(text_data=json.dumps({
#             'message': message,
#             'sender_id': sender_id,
#             'receiver_id': receiver_id,
#         }))

#     async def get_receiver(self):
#         try:
#             receiver = await self.get_user(self.receiver_id)
#             print("🚀🚀🚀🚀🚀🚀 ~ file: consumers.py:76 ~ receiver:", receiver)
#             return receiver
#         except User.DoesNotExist:
#             return None

#     @database_sync_to_async
#     def get_user(self, user_id):
#         try:
#             return User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return None

#     @database_sync_to_async
#     def save_message(self, message):
#         Message.objects.create(
#             sender=self.sender,
#             receiver=self.receiver,
#             content=message,
#         )



class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = User.objects.get(id=self.user_id)
        self.room_group_name = f'chat_{self.user_id}'

        # Join the chat room
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave the chat room
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        recipient_id = data['recipient_id']

        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            # Return an error if recipient does not exist
            self.send(text_data=json.dumps({
                'error': 'Recipient does not exist.'
            }))
            return

        if recipient.online:
            # Send the message to the recipient
            async_to_sync(self.channel_layer.group_send)(
                f'chat_{recipient_id}',
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user_id,
                }
            )
            # Return a success message
            self.send(text_data=json.dumps({
                'success': 'Message sent successfully.'
            }))
        else:
            # Return an error if recipient is offline
            self.send(text_data=json.dumps({
                'error': 'Recipient is offline.'
            }))

    def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']

        # Send the received message to the recipient
        self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
        }))