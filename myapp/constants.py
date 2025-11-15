# myapp/constants.py
"""
Application constants for the MAPDL Simulation Backend

This module contains all configurable constants used throughout the application.
Modify these values to adjust system behavior without changing core code.
"""

# ============================================================================
# Time constants (in seconds)
# ============================================================================
SIMULATION_CACHE_TTL = 604800  # 7 days - how long to cache simulation results
OLD_SIMULATION_THRESHOLD_DAYS = 30  # Delete simulations older than this
REDIS_KEY_EXPIRY = 86400  # 24 hours - Redis key expiration
CELERY_BEAT_CLEAN_INTERVAL = 172800  # 2 days - cleanup task interval

# ============================================================================
# Celery configuration
# ============================================================================
CELERY_WORKER_MAX_TASKS = 100  # Restart worker after this many tasks
CELERY_TASK_TIME_LIMIT = 3600  # 1 hour - hard time limit for tasks
CELERY_TASK_SOFT_TIME_LIMIT = 3000  # 50 minutes - soft time limit

# ============================================================================
# API Pagination
# ============================================================================
DEFAULT_PAGE_SIZE = 10  # Default number of items per page
MAX_PAGE_SIZE = 100  # Maximum items per page

# ============================================================================
# Image generation settings
# ============================================================================
IMAGE_WINDOW_SIZE = [1920, 1080]  # Resolution for generated images [width, height]

