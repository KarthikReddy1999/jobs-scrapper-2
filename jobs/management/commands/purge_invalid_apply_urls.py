from django.core.management.base import BaseCommand
from jobscraper.apply_urls import is_blocked_apply_host

from jobs.models import Job


class Command(BaseCommand):
    help = "Delete Simplify jobs whose apply_url is LinkedIn or other blocked job boards only."

    def handle(self, *args, **options):
        removed = 0
        for job in Job.objects.iterator():
            url = job.apply_url or ""
            if is_blocked_apply_host(url):
                title, short = job.title, url[:80]
                job.delete()
                removed += 1
                self.stdout.write(f"Removed: {title} -> {short}")
        self.stdout.write(self.style.SUCCESS(f"Deleted {removed} invalid apply URLs"))
