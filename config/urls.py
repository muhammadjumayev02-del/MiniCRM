from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from leads.api import LeadViewSet, TokenLoginView

router = DefaultRouter()
router.register("leads", LeadViewSet, basename="api-lead")
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/auth/token/", TokenLoginView.as_view(), name="api-token"),
    path("api/auth/", include("rest_framework.urls")),
    path("api/", include(router.urls)),
]
