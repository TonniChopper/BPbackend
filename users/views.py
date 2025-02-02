from django.shortcuts import render
from rest_framework import generics
from .models import User
from .serializers import UserSerializer

# Create your views here.
# Create your views here.

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
