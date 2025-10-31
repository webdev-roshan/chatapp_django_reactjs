from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import (
    UserSerializer,
    UserListSerializer,
    ConversationSerializer,
    MessageSerializer,
    CreateMessageSerializer,
)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]


class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related("participants")

    def create(self, request, *args, **kwargs):
        participants_data = request.data.get("participants", [])

        if len(participants_data) != 2:
            return Response(
                {"error": "A conversation needs exactly two participants"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(request.user.id) not in map(str, participants_data):
            return Response(
                {"error": "You are not a participant of this conversation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        users = User.objects.filter(id__in=participants_data)
        if users.count() != 2:
            return Response(
                {"error": "A conversation needs exactly two valid participants"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_conversation = (
            Conversation.objects.filter(participants__id=participants_data[0])
            .filter(participants__id=participants_data[1])
            .distinct()
        )

        if existing_conversation.exists():
            return Response(
                {"error": "A conversation already exists between these participants"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = Conversation.objects.create()
        conversation.participants.set(users)

        serializer = self.get_serializer(conversation, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation = self.get_conversation()
        return conversation.messages.order_by("timestamp")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateMessageSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        conversation = self.get_conversation()
        serializer.save(sender=self.request.user, conversation=conversation)

    def get_conversation(self):
        conversation_id = self.kwargs["conversation_id"]
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if self.request.user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant of this conversation")
        return conversation


class MessageRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation = self.get_conversation()
        return conversation.messages.all()

    def perform_destroy(self, instance):
        if instance.sender != self.request.user:
            raise PermissionDenied("You are not the sender of this message")
        instance.delete()

    def get_conversation(self):
        conversation_id = self.kwargs["conversation_id"]
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if self.request.user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant of this conversation")
        return conversation
