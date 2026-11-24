from django.utils import timezone
from rest_framework import serializers

from .models import Booking, Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "price"]


class BookingSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.filter(is_active=True))
    service_name = serializers.CharField(source="service.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "service", "service_name", "requested_at", "phone", "comment",
                  "status", "status_label", "created_at"]
        read_only_fields = ["id", "status", "created_at"]
        # Дубликаты также проверяются ограничением БД при одновременных запросах.
        validators = []

    def validate_requested_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Выберите будущее время.")
        return value
