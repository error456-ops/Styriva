from django.core.management.base import BaseCommand

from jobs.worker import Worker


class Command(BaseCommand):
    help = "Starts the STYRIVA background worker."

    def handle(self, *args, **options):
        worker = Worker()
        worker.start()