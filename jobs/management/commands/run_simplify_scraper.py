import os

from django.core.management.base import BaseCommand

from jobscraper.scraper_process import clear_stop_flag

from jobs.models import ScraperState
from jobs.scraper import SimplifyScraper


class Command(BaseCommand):
    help = "Run Simplify scraper in this process (used by dashboard Start button)."

    def add_arguments(self, parser):
        parser.add_argument("--resume", action="store_true", help="Resume from saved keyword index")

    def handle(self, *args, **options):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        clear_stop_flag()
        state = ScraperState.get_singleton()
        state.worker_pid = os.getpid()
        state.status = ScraperState.STATUS_RUNNING
        state.save(update_fields=["worker_pid", "status"])

        self.stdout.write(self.style.SUCCESS(f"Simplify worker started PID={os.getpid()}"))

        try:
            SimplifyScraper(resume=options["resume"]).run()
        finally:
            state = ScraperState.get_singleton()
            if state.worker_pid == os.getpid():
                state.worker_pid = 0
                if state.status == ScraperState.STATUS_RUNNING:
                    state.status = ScraperState.STATUS_IDLE
                state.save(update_fields=["worker_pid", "status"])
            self.stdout.write("Simplify worker exited.")
