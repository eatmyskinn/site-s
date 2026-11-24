from django.contrib import admin

from .models import Booking, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "service", "requested_at", "status"]
    list_filter = ["status", "service"]
    search_fields = ["user__username"]
    readonly_fields = ["user", "service", "requested_at", "phone", "comment", "created_at"]
    list_select_related = ["user", "service"]

    def has_add_permission(self, request):
        return False
