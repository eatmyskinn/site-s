from django import forms
from django.utils import timezone

from .models import Booking, Service


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["service", "requested_at", "phone", "comment"]
        widgets = {
            "requested_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True)

    def clean_requested_at(self):
        value = self.cleaned_data["requested_at"]
        if value <= timezone.now():
            raise forms.ValidationError("Выберите будущее время.")
        return value
