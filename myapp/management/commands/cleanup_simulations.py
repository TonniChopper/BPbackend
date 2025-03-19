import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import Simulation

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up simulations older than two days.'

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(days=2)
        old_simulations = Simulation.objects.filter(created_at__lt=threshold)
        count = old_simulations.count()
        for sim in old_simulations:
            try:
                sim.delete()
            except Exception as e:
                logger.error(f"Error deleting simulation {sim.pk}: {e}", exc_info=True)
        self.stdout.write(f'Cleaned up {count} out-of-date simulations.')