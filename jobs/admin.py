from django.contrib import admin

from .models import Job, ScraperState


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "keyword", "posted_time", "created_at")
    search_fields = ("title", "company", "keyword", "apply_url")
    list_filter = ("keyword", "source")


@admin.register(ScraperState)
class ScraperStateAdmin(admin.ModelAdmin):
    list_display = (
        "status",
        "current_keyword",
        "current_page",
        "keyword_index",
        "jobs_saved",
        "jobs_skipped",
        "updated_at",
    )
