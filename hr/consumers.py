import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message

User = get_user_model()

class BaseConsumer(AsyncWebsocketConsumer):
    """
    Helper consumer with methods to set online status.
    Uses database_sync_to_async since ORM calls must be synchronous.
    """
    @database_sync_to_async
    def set_online_status(self, user, status):
        # Update Employee/HR status
        if hasattr(user, 'profile'):
            user.profile.is_online = status
            user.profile.save(update_fields=['is_online'])
        # Update Client status
        elif hasattr(user, 'client_profile'):
            user.client_profile.is_online = status
            user.client_profile.save(update_fields=['is_online'])


class OnlineStatusConsumer(BaseConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            await self.set_online_status(self.user, True)
            
            # Broadcast the online status to a global group (optional, can be refined per role if needed)
            await self.channel_layer.group_add("global_online", self.channel_name)
            await self.channel_layer.group_send(
                "global_online",
                {
                    "type": "user_status_changed",
                    "user_id": self.user.id,
                    "is_online": True
                }
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.set_online_status(self.user, False)
            await self.channel_layer.group_send(
                "global_online",
                {
                    "type": "user_status_changed",
                    "user_id": self.user.id,
                    "is_online": False
                }
            )
            await self.channel_layer.group_discard("global_online", self.channel_name)

    async def user_status_changed(self, event):
        await self.send(text_data=json.dumps({
            "type": "status_update",
            "user_id": event["user_id"],
            "is_online": event["is_online"]
        }))


class ChatConsumer(BaseConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Security check: User must belong to conversation
        is_participant = await self.check_participation(self.conversation_id, self.user)
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')

        if message.strip():
            # Save to DB
            new_msg = await self.save_message(self.user.id, self.conversation_id, message)

            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'timestamp': new_msg.timestamp.strftime('%H:%M'),
                }
            )

            # Send Notification to other participants
            participants = await self.get_other_participants(self.conversation_id, self.user.id)
            for user_id in participants:
                unread_count = await self.get_unread_count(user_id)
                await self.channel_layer.group_send(
                    f"notifications_{user_id}",
                    {
                        "type": "chat_notification",
                        "sender_name": self.user.get_full_name() or self.user.username,
                        "message_preview": message[:50] + ("..." if len(message) > 50 else ""),
                        "unread_count": unread_count,
                        "conversation_id": self.conversation_id
                    }
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def check_participation(self, conv_id, user):
        try:
            conv = Conversation.objects.get(id=conv_id)
            return conv.participants.filter(id=user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user_id, conv_id, content):
        conv = Conversation.objects.get(id=conv_id)
        user = User.objects.get(id=user_id)
        return Message.objects.create(conversation=conv, sender=user, content=content)

    @database_sync_to_async
    def get_other_participants(self, conv_id, exclude_user_id):
        conv = Conversation.objects.get(id=conv_id)
        return list(conv.participants.exclude(id=exclude_user_id).values_list('id', flat=True))

    @database_sync_to_async
    def get_unread_count(self, user_id):
        user = User.objects.get(id=user_id)
        return Message.objects.filter(conversation__participants=user, is_read=False).exclude(sender=user).count()


class NotificationConsumer(BaseConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            self.room_group_name = f"notifications_{self.user.id}"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            # Send initial unread count on connect
            unread_count = await self.get_unread_count(self.user.id)
            await self.send(text_data=json.dumps({
                "type": "unread_count_init",
                "unread_count": unread_count
            }))
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def chat_notification(self, event):
        # Fire event to the listening frontend
        await self.send(text_data=json.dumps({
            "type": "chat_notification",
            "sender_name": event["sender_name"],
            "message_preview": event["message_preview"],
            "unread_count": event["unread_count"],
            "conversation_id": event["conversation_id"]
        }))

    @database_sync_to_async
    def get_unread_count(self, user_id):
        user = User.objects.get(id=user_id)
        return Message.objects.filter(conversation__participants=user, is_read=False).exclude(sender=user).count()
