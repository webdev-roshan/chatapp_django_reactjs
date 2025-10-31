from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_list_or_404
from .models import *
from .serializers import *
from rest_framework.exceptions import PermissionDenied


