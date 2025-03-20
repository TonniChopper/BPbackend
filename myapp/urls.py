from django.urls import path
from . import views

urlpatterns = [
    path('simulations/', views.SimulationListCreateView.as_view(), name='simulation-list-create'),
    path('simulations/<int:pk>/', views.SimulationDetailView.as_view(), name='simulation-detail'),
    path('simulations/<int:pk>/resume/', views.SimulationResumeView.as_view(), name='simulation-resume'),
    path('simulations/<int:pk>/download/', views.SimulationDownloadView.as_view(), name='simulation-download'),
    path('simulations/<int:pk>/status/', views.SimulationStatusView.as_view(), name='simulation-status'),
]