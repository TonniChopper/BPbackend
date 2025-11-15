# ANSYS MAPDL Simulation Backend

---

## 📋 Project Description

Backend system for managing and executing Finite Element Method (FEM) simulations using ANSYS MAPDL. Provides a comprehensive REST API for creating, managing, and retrieving results of stress-strain analysis simulations for beams with holes.

Note on authorship and provenance:  
This project is fully functional and was written by the author as part of a Bachelor's thesis at the Slovak University of Technology in Bratislava.

### Core Features

- ✅ **REST API** for simulation management
- ✅ **JWT Authentication** for user security
- ✅ **Asynchronous Processing** via Celery task queue
- ✅ **Smart Caching** of identical simulation results in Redis
- ✅ **Automatic Visualization** generation (mesh, stress, deformation)
- ✅ **Multi-user Support** (authenticated and anonymous users)
- ✅ **Health Monitoring** endpoint for system status
- ✅ **Statistics Dashboard** for user analytics
- ✅ **Batch Operations** for managing multiple simulations
- ✅ **Automatic Cleanup** of old simulations

---

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 5.1 |
| API | Django REST Framework | 3.14.0 |
| Authentication | SimpleJWT | 5.3.0 |
| Database | SQLite | (dev) |
| Task Queue | Celery | 5.3.4 |
| Message Broker | Redis Cloud | 7.x |
| Scientific Computing | PyMAPDL | 0.68.0 |
| Data Processing | NumPy | 1.26.0 |
| Visualization | Matplotlib | 3.8.0 |
| Testing | pytest | 8.3.3 |

### Project Structure

```
backend/
├── backend/                          # Django project core
│   ├── settings.py                  # Application configuration
│   ├── urls.py                      # Main URL routing
│   ├── celery.py                    # Celery configuration
│   ├── wsgi.py                      # WSGI entry point
│   └── asgi.py                      # ASGI entry point
│
├── myapp/                           # Main application
│   ├── models.py                   # Data models (Simulation, SimulationResult)
│   ├── admin.py                    # Django Admin configuration
│   ├── tests.py                    # Unit tests
│   ├── constants.py                # Application constants
│   │
│   ├── api/                        # REST API
│   │   ├── views.py               # API endpoints
│   │   ├── serializers.py         # DRF serializers
│   │   └── urls.py                # API routes
│   │
│   ├── services/                   # Business logic layer
│   │   ├── simulation_service.py  # Simulation management
│   │   ├── mapdl_handler.py       # ANSYS MAPDL integration
│   │   └── simulation_cache_service.py  # Result caching
│   │
│   ├── tasks/                      # Celery tasks
│   │   ├── simulation_task.py     # Async simulation execution
│   │   └── maintenance_tasks.py   # Cleanup and maintenance
│   │
│   └── utils/                      # Utilities
│       ├── image_capture.py       # Image generation
│       └── result_processor.py    # Result processing
│
├── media/                          # Uploaded and generated files
│   └── simulation_results/        # Simulation outputs
│
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
└── db.sqlite3                      # SQLite database
```

### System Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │────────▶│   Django     │────────▶│   SQLite    │
│   (React)   │  HTTP   │   REST API   │         │  Database   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              │ Dispatch Tasks
                              ▼
                        ┌──────────────┐         ┌─────────────┐
                        │    Celery    │────────▶│    Redis    │
                        │   Workers    │  Store  │   Broker    │
                        └──────────────┘         └─────────────┘
                              │
                              │ Execute
                              ▼
                        ┌──────────────┐
                        │    ANSYS     │
                        │    MAPDL     │
                        └──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Redis (cloud or local)
- ANSYS MAPDL (optional for running simulations)

### Installation Steps

1. **Clone the repository:**

```bash
git clone <repository-url>
cd backend
```

2. **Create virtual environment:**

```bash
# Windows
python -m venv bpvenv
bpvenv\Scripts\activate

# Linux/Mac
python3 -m venv bpvenv
source bpvenv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**

Create `.env` file based on `.env.example`:

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis Configuration
REDIS_HOST=your-redis-host
REDIS_PORT=17145
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

# CORS Configuration
CORS_ALLOW_ALL=False
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

5. **Run database migrations:**

```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser:**

```bash
python manage.py createsuperuser
```

7. **Start the services:**

```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: Celery worker
celery -A backend worker -l info

# Terminal 3: Celery beat (scheduled tasks)
celery -A backend beat -l info
```

---

## 📡 API Reference

### Base URL

```
http://localhost:8000/myapp/
```

### System Endpoints

#### Health Check

Check system status and service health.

```http
GET /myapp/health/
```

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "timestamp": "2025-11-16T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - All services healthy
- `503 Service Unavailable` - One or more services down

---

### Authentication Endpoints

#### Register User

```http
POST /myapp/user/registration/
Content-Type: application/json

{
  "username": "newuser",
  "password": "password123"
}
```

#### Get Access Token

```http
POST /myapp/token/
Content-Type: application/json

{
  "username": "newuser",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

- **Access token** expires in 30 minutes
- **Refresh token** expires in 1 day

#### Refresh Token

```http
POST /myapp/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Simulation Endpoints

#### List Simulations

Get paginated list of user's simulations.

```http
GET /myapp/simulations/
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int) - Page number (default: 1)
- `page_size` (int) - Items per page (default: 10, max: 100)

#### Create Simulation

Submit a new simulation job.

```http
POST /myapp/simulations/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Test Beam Simulation",
  "parameters": {
    "e": 210000000000.0,
    "nu": 0.3,
    "length": 5.0,
    "width": 2.5,
    "depth": 0.1,
    "radius": 0.5,
    "num": 3,
    "element_size": 0.125,
    "pressure": 1000.0
  }
}
```

**Simulation Parameters:**

| Parameter | Type | Unit | Description | Constraints |
|-----------|------|------|-------------|-------------|
| `e` | float | Pa | Young's modulus | > 0 |
| `nu` | float | - | Poisson's ratio | 0 ≤ nu < 0.5 |
| `length` | float | m | Beam length | > 0 |
| `width` | float | m | Beam width | > 0 |
| `depth` | float | m | Beam depth | > 0 |
| `radius` | float | m | Hole radius | > 0, < width/2 |
| `num` | int | - | Number of holes | ≥ 1 |
| `element_size` | float | m | Mesh element size | > 0 |
| `pressure` | float | Pa | Applied pressure | any |

**Response (202 Accepted):**
```json
{
  "id": 1,
  "title": "Test Beam Simulation",
  "status": "PENDING",
  "task_id": "abc123-def456",
  "message": "Simulation queued successfully"
}
```

#### Get Simulation Status

```http
GET /myapp/simulations/{id}/status/
Authorization: Bearer <access_token>
```

**Response (COMPLETED):**
```json
{
  "id": 1,
  "title": "Test Beam Simulation",
  "status": "COMPLETED",
  "created_at": "2025-11-16T10:00:00Z",
  "completed_at": "2025-11-16T10:05:30Z",
  "result_summary": {
    "max_displacement": 0.00015,
    "min_displacement": 0.0,
    "avg_displacement": 0.000075,
    "max_stress": 45000000.0,
    "min_stress": 0.0,
    "avg_stress": 22500000.0,
    "node_count": 12345,
    "element_count": 8901
  },
  "mesh_image_url": "http://localhost:8000/media/...",
  "stress_image_url": "http://localhost:8000/media/...",
  "deformation_image_url": "http://localhost:8000/media/..."
}
```

**Possible Status Values:**
- `PENDING` - Queued, waiting to start
- `RUNNING` - Currently executing
- `COMPLETED` - Successfully finished
- `FAILED` - Execution failed

#### Download Results

```http
GET /myapp/simulations/{id}/download/{file_type}/
Authorization: Bearer <access_token>
```

**Available file types:**
- `result` - Complete results text file (.txt)
- `mesh` - Mesh visualization image (.png)
- `stress` - Stress distribution image (.png)
- `deformation` - Deformation visualization image (.png)
- `summary` - Summary statistics JSON file (.json)

#### Cancel Simulation

```http
POST /myapp/simulations/{id}/cancel/
Authorization: Bearer <access_token>
```

#### Resume Simulation

```http
POST /myapp/simulations/{id}/resume/
Authorization: Bearer <access_token>
```

#### Delete Simulation

```http
DELETE /myapp/simulations/{id}/delete/
Authorization: Bearer <access_token>
```

---

### Statistics & Batch Operations

#### Get User Statistics

Get comprehensive statistics about user's simulations.

```http
GET /myapp/statistics/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "total_simulations": 42,
  "by_status": {
    "COMPLETED": 35,
    "FAILED": 5,
    "PENDING": 1,
    "RUNNING": 1
  },
  "average_completion_time_seconds": 320.5,
  "recent_simulations_7_days": 8
}
```

#### Batch Delete Simulations

Delete multiple simulations in one request.

```http
POST /myapp/simulations/batch-delete/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "simulation_ids": [1, 2, 3, 4, 5]
}
```

**Response:**
```json
{
  "detail": "Successfully deleted 5 simulation(s)",
  "deleted_count": 5
}
```

---

## 🗄️ Data Models

### Simulation Model

```python
class Simulation(models.Model):
    """Represents a MAPDL simulation job"""
    
    title = CharField(max_length=255)
    user = ForeignKey(User)
    status = CharField(choices=STATUS_CHOICES)
    parameters = JSONField()
    parameters_hash = CharField(max_length=128)  # SHA-256
    created_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True)
```

**Status Choices:**
- `PENDING` - Waiting in queue
- `RUNNING` - Currently executing
- `COMPLETED` - Successfully finished
- `FAILED` - Execution failed

### SimulationResult Model

```python
class SimulationResult(models.Model):
    """Stores simulation results and visualizations"""
    
    simulation = OneToOneField(Simulation)
    result_file = FileField()
    mesh_image = ImageField()
    stress_image = ImageField()
    deformation_image = ImageField()
    summary = JSONField()
    created_at = DateTimeField(auto_now_add=True)
```

**Summary JSON Structure:**
```json
{
  "max_displacement": 0.00015,
  "min_displacement": 0.0,
  "avg_displacement": 0.000075,
  "max_stress": 45000000.0,
  "min_stress": 0.0,
  "avg_stress": 22500000.0,
  "node_count": 12345,
  "element_count": 8901,
  "has_mesh_image": true,
  "has_stress_image": true,
  "has_deformation_image": true
}
```

---

## ⚙️ Configuration

### Environment Variables

All sensitive configuration should be in `.env` file:

```env
# Django Core
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Redis
REDIS_HOST=your-redis-host
REDIS_PORT=17145
REDIS_PASSWORD=your-password
REDIS_DB=0

# CORS
CORS_ALLOW_ALL=False
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Application Constants

Adjust system behavior by modifying `myapp/constants.py`:

```python
# Time constants (seconds)
SIMULATION_CACHE_TTL = 604800  # 7 days
OLD_SIMULATION_THRESHOLD_DAYS = 30
REDIS_KEY_EXPIRY = 86400  # 24 hours
CELERY_BEAT_CLEAN_INTERVAL = 172800  # 2 days

# Celery settings
CELERY_WORKER_MAX_TASKS = 100
CELERY_TASK_TIME_LIMIT = 3600  # 1 hour
CELERY_TASK_SOFT_TIME_LIMIT = 3000  # 50 minutes

# API settings
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Image generation
IMAGE_WINDOW_SIZE = [1920, 1080]
```

---

## 🔄 Asynchronous Tasks (Celery)

### Background Tasks

#### run_simulation_task_with_redis

Executes ANSYS MAPDL simulation asynchronously.

**Process:**
1. Updates status in Redis → "RUNNING"
2. Launches MAPDL simulation
3. Processes results and generates images
4. Caches result for future reuse
5. Updates status → "COMPLETED" or "FAILED"

#### clean_old_simulations

Periodic cleanup task for old simulations.

**Schedule:** Every 2 days  
**Action:** Deletes simulations older than 30 days

### Monitoring

**Redis Keys:**
- `simulation_task_id:{id}` - Celery task ID
- `simulation_status:{id}` - Current task status
- `simulation_cache:{hash}` - Cached results

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=myapp --cov-report=html

# Run specific test file
pytest myapp/tests.py

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Structure

```python
# myapp/tests.py

class MAPDLHandlerTests(TestCase):
    """Tests for MAPDL integration"""
