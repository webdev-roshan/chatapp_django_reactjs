from django.db import models
from django.contrib.auth.models import User
from django.db.models import Prefetch


class ConversationManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch("participants", queryset=User.objects.only("id", "username"))
            )
        )


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ConversationManager()

    def __str__(self):
        participants_names = " ,".join(
            user.username for user in self.participants.all()
        )
        return f"Conversation with {participants_names}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Messaeges from {self.sender.username} in {self.content[:20]}"
