from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import services
from .forms import BookingForm
from .models import Booking, Service
from .serializers import BookingSerializer, ServiceSerializer


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]


class BookingViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related("service")

    def perform_create(self, serializer):
        serializer.instance = services.submit_booking(
            user=self.request.user, data=serializer.validated_data
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        services.cancel_booking(user=request.user, pk=booking.pk)
        booking.refresh_from_db()
        return Response(self.get_serializer(booking).data, status=status.HTTP_200_OK)


def home(request):
    bookings = (
        Booking.objects.filter(user=request.user).select_related("service")
        if request.user.is_authenticated else []
    )
    return render(request, "bookings/home.html", {
        "services": Service.objects.filter(is_active=True), "bookings": bookings,
    })


@login_required
def create_booking(request):
    form = BookingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            services.submit_booking(user=request.user, data=form.cleaned_data)
        except ValidationError:
            form.add_error(None, "Такая заявка уже существует.")
        else:
            messages.success(request, "Заявка отправлена. Время должен подтвердить администратор.")
            return redirect("home")
    return render(request, "bookings/form.html", {"form": form})


@login_required
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, user=request.user, pk=pk)
    services.cancel_booking(user=request.user, pk=booking.pk)
    return redirect("home")
