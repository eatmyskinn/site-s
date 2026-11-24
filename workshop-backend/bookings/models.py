from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

phone_validator = RegexValidator(
    r"^\+?[0-9 ()-]{7,25}$", "Укажите телефон: от 7 до 25 символов, цифры, +, скобки, пробел или дефис."
)


class Service(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    price = models.DecimalField("Цена от", max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField("Доступна для записи", default=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.CheckConstraint(condition=Q(price__gte=0), name="service_price_nonnegative")]

    def __str__(self):
        return self.name


class Booking(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Ожидает согласования"
        CONFIRMED = "confirmed", "Подтверждена"
        CANCELLED = "cancelled", "Отменена"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="bookings")
    requested_at = models.DateTimeField("Желаемое время")
    phone = models.CharField("Телефон", max_length=25, validators=[phone_validator])
    comment = models.CharField("Комментарий", max_length=500, blank=True)
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["user", "-created_at"], name="booking_user_created_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "service", "requested_at"],
                condition=Q(status__in=["new", "confirmed"]),
                name="unique_active_booking",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["new", "confirmed", "cancelled"]),
                name="booking_valid_status",
            ),
        ]

    def __str__(self):
        return f"Заявка #{self.pk}: {self.service}"
