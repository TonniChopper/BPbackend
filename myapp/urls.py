from django.urls import path
from . import views

urlpatterns = [
    path('graphs/', views.GraphListCreate.as_view(), name='graph-list'),
    path('graphs/<int:pk>/', views.GraphDetail.as_view(), name='graph-detail'),
]