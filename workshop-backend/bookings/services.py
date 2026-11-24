import logging

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from .models import Booking

logger = logging.getLogger(__name__)


def submit_booking(*, user, data):
    try:
        with transaction.atomic():
            booking = Booking.objects.create(user=user, **data)
    except IntegrityError:
        if Booking.objects.filter(
            user=user, service=data["service"], requested_at=data["requested_at"],
            status__in=[Booking.Status.NEW, Booking.Status.CONFIRMED],
        ).exists():
            raise ValidationError({"detail": "Такая заявка уже существует."})
        raise
    logger.info("Booking created id=%s user_id=%s", booking.pk, user.pk)
    return booking


def cancel_booking(*, user, pk):
    # UPDATE не перезаписывает остальные поля и безопасен при повторной отмене.
    changed = Booking.objects.filter(pk=pk, user=user).exclude(
        status=Booking.Status.CANCELLED
    ).update(status=Booking.Status.CANCELLED)
    if changed:
        logger.info("Booking cancelled id=%s user_id=%s", pk, user.pk)
