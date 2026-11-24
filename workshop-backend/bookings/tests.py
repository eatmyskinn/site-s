from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Booking, Service


class BookingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("customer", password="test-pass-42")
        cls.other = get_user_model().objects.create_user("other", password="test-pass-43")
        cls.service = Service.objects.create(name="Смена шин", price="2000")
        cls.inactive = Service.objects.create(name="Архив", price="100", is_active=False)
        cls.when = timezone.now().replace(second=0, microsecond=0) + timedelta(days=1)
        cls.token = Token.objects.create(user=cls.user)

    def setUp(self):
        self.api = APIClient()
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def payload(self, **overrides):
        return {
            "service": self.service.pk, "requested_at": self.when.isoformat(),
            "phone": "+7 900 123-45-67", "comment": "Легковой автомобиль", **overrides,
        }

    def booking(self, **overrides):
        return Booking.objects.create(
            user=overrides.pop("user", self.user), service=self.service,
            requested_at=self.when, phone="+79001234567", **overrides,
        )

    def test_services_are_public_and_hide_inactive(self):
        response = APIClient().get("/api/services/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data["results"]], [self.service.pk])

    def test_anonymous_cannot_read_or_create_bookings(self):
        client = APIClient()
        self.assertEqual(client.get("/api/bookings/").status_code, 401)
        self.assertEqual(client.post("/api/bookings/", self.payload(), format="json").status_code, 401)

    def test_create_assigns_owner_and_initial_status(self):
        response = self.api.post("/api/bookings/", self.payload(user=self.other.pk, status="confirmed"), format="json")
        self.assertEqual(response.status_code, 201)
        booking = Booking.objects.get(pk=response.data["id"])
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.status, Booking.Status.NEW)

    def test_invalid_fields_do_not_create_booking(self):
        for data in [
            self.payload(requested_at=(timezone.now() - timedelta(days=1)).isoformat()),
            self.payload(service=self.inactive.pk),
            self.payload(service=999999),
            self.payload(phone="wrong"),
            self.payload(comment="x" * 501),
            self.payload(requested_at="not a date"),
        ]:
            with self.subTest(data=data):
                self.assertEqual(self.api.post("/api/bookings/", data, format="json").status_code, 400)
        self.assertEqual(Booking.objects.count(), 0)

    def test_malformed_json_is_bad_request(self):
        response = self.api.post("/api/bookings/", '{"service":', content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_duplicate_returns_validation_error(self):
        self.assertEqual(self.api.post("/api/bookings/", self.payload(), format="json").status_code, 201)
        self.assertEqual(self.api.post("/api/bookings/", self.payload(), format="json").status_code, 400)
        self.assertEqual(Booking.objects.count(), 1)

    def test_database_rejects_duplicate_without_api(self):
        self.booking()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.booking()

    def test_database_rejects_negative_price(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Service.objects.create(name="Неверная цена", price="-1")

    def test_list_contains_only_own_bookings(self):
        mine = self.booking()
        self.booking(user=self.other)
        response = self.api.get("/api/bookings/")
        self.assertEqual([item["id"] for item in response.data["results"]], [mine.pk])

    def test_cannot_read_or_cancel_another_users_booking(self):
        other = self.booking(user=self.other)
        self.assertEqual(self.api.get(f"/api/bookings/{other.pk}/").status_code, 404)
        self.assertEqual(self.api.post(f"/api/bookings/{other.pk}/cancel/").status_code, 404)
        other.refresh_from_db()
        self.assertEqual(other.status, Booking.Status.NEW)

    def test_cancel_is_repeatable_and_allows_new_request(self):
        booking = self.booking(status=Booking.Status.CONFIRMED)
        for _ in range(2):
            self.assertEqual(self.api.post(f"/api/bookings/{booking.pk}/cancel/").status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertEqual(self.api.post("/api/bookings/", self.payload(), format="json").status_code, 201)

    def test_patch_and_delete_are_not_allowed(self):
        booking = self.booking()
        self.assertEqual(self.api.patch(f"/api/bookings/{booking.pk}/", {"status": "confirmed"}, format="json").status_code, 405)
        self.assertEqual(self.api.delete(f"/api/bookings/{booking.pk}/").status_code, 405)

    def test_home_and_login_render(self):
        self.assertContains(self.client.get("/"), "Запись", status_code=200)
        self.assertEqual(self.client.get("/login/").status_code, 200)

    def test_session_form_creates_booking(self):
        self.client.force_login(self.user)
        response = self.client.post("/bookings/new/", {
            "service": self.service.pk,
            "requested_at": timezone.localtime(self.when).strftime("%Y-%m-%dT%H:%M"),
            "phone": "+79001234567",
        })
        self.assertRedirects(response, "/")
        self.assertEqual(Booking.objects.get().user, self.user)

    def test_html_rejects_duplicate(self):
        self.booking()
        self.client.force_login(self.user)
        response = self.client.post("/bookings/new/", {
            "service": self.service.pk,
            "requested_at": timezone.localtime(self.when).strftime("%Y-%m-%dT%H:%M"),
            "phone": "+79001234567",
        })
        self.assertContains(response, "Такая заявка уже существует.")
        self.assertEqual(Booking.objects.count(), 1)

    def test_html_cannot_cancel_others_booking(self):
        booking = self.booking(user=self.other)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(f"/bookings/{booking.pk}/cancel/").status_code, 404)

    def test_session_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post("/bookings/new/", {}).status_code, 403)
        self.assertEqual(client.post("/api/bookings/", self.payload(), content_type="application/json").status_code, 403)

    def test_get_cannot_cancel(self):
        booking = self.booking()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f"/bookings/{booking.pk}/cancel/").status_code, 405)
        self.assertEqual(self.api.get(f"/api/bookings/{booking.pk}/cancel/").status_code, 405)

    def test_comment_is_escaped(self):
        self.booking(comment="<script>alert(1)</script>")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_seed_is_repeatable(self):
        from django.core.management import call_command

        call_command("seed_services")
        count = Service.objects.count()
        call_command("seed_services")
        self.assertEqual(Service.objects.count(), count)
