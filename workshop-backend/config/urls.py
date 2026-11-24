from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from bookings import views

router = DefaultRouter()
router.register("services", views.ServiceViewSet, basename="service")
router.register("bookings", views.BookingViewSet, basename="booking")
urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("bookings/new/", views.create_booking, name="create-booking"),
    path("bookings/<int:pk>/cancel/", views.cancel_booking, name="cancel-booking"),
    path("api/", include(router.urls)),
    path("admin/", admin.site.urls),
]
