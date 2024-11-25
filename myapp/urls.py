from django.urls import path
from . import views

urlpatterns = [
    path('trigger-task/<int:graph_id>/', views.TriggerTask.as_view(), name='trigger-task'),
    path('graphs/', views.GraphListCreate.as_view(), name='graph-list'),
    path('graphs/<int:pk>/', views.GraphDetail.as_view(), name='graph-detail'),
]