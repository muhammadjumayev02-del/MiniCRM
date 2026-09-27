from django.urls import path
from . import views

urlpatterns = [
    path("", views.lead_list, name="lead-list"),
    path("leads/new/", views.lead_form, name="lead-create"),
    path("leads/<int:pk>/", views.lead_detail, name="lead-detail"),
    path("leads/<int:pk>/edit/", views.lead_form, name="lead-update"),
    path("leads/<int:pk>/status/", views.lead_status, name="lead-status"),
    path("leads/<int:pk>/delete/", views.lead_delete, name="lead-delete"),
]
