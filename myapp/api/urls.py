from django.urls import path
from myapp.api import views

urlpatterns = [
    # Health check
    path('health/', views.HealthCheckView.as_view(), name='health-check'),

    # Simulations
    path('simulations/', views.SimulationListCreateView.as_view(), name='simulation-list-create'),
    path('simulations/<int:pk>/', views.SimulationDetailView.as_view(), name='simulation-detail'),
    path('simulations/<int:pk>/resume/', views.SimulationResumeView.as_view(), name='simulation-resume'),
    path('simulations/<int:pk>/download/<str:file_type>/', views.SimulationDownloadView.as_view(),name='simulation-download'),
    path('simulations/<int:pk>/cancel/', views.CancelSimulationView.as_view(), name='simulation-cancel'),
    path('simulations/<int:pk>/status/', views.SimulationStatusView.as_view(), name='simulation-status'),
    path('simulations/<int:pk>/delete/', views.DeleteSimulationView.as_view(), name='simulation-delete'),

    # Batch operations
    path('simulations/batch-delete/', views.BatchDeleteSimulationsView.as_view(), name='simulation-batch-delete'),

    # Statistics
    path('statistics/', views.SimulationStatisticsView.as_view(), name='simulation-statistics'),
]