import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from myapp.models import Graph

@pytest.mark.django_db

@pytest.mark.django_db
def test_create_graph():
    client = APIClient()
    url = reverse('graph-list')
    data = {
        "pressure": 100,
        "temperature": 200
    }
    response = client.post(url, data, format='json')
    print(response.data)  # Add this line to see the response content
    assert response.status_code == 201
    assert Graph.objects.count() == 1
    graph = Graph.objects.first()
    assert graph.pressure == 100
    assert graph.temperature == 200
    assert graph.image.name.endswith('.png')

@pytest.mark.django_db
def test_graph_detail():
    graph = Graph.objects.create(pressure=100, temperature=200, image='simulations/result.png')
    client = APIClient()
    url = reverse('graph-detail', args=[graph.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.data['pressure'] == 100
    assert response.data['temperature'] == 200
    assert response.data['image'].endswith('simulations/result.png')