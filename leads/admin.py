from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "phone", "email", "source")
    readonly_fields = ("created_at", "updated_at")
