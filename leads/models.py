from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def validate_contact(phone, email):
    if not (phone.strip() or email.strip()):
        raise ValidationError("Telefon yoki emaildan kamida bittasini kiriting.")


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = "New", "New"
        CONTACTED = "Contacted", "Contacted"
        QUALIFIED = "Qualified", "Qualified"
        WON = "Won", "Won"
        LOST = "Lost", "Lost"

    name = models.CharField("Ism", max_length=150)
    phone = models.CharField("Telefon", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    source = models.CharField("Manba", max_length=100, blank=True)
    note = models.TextField("Izoh", blank=True)
    status = models.CharField("Status", max_length=10, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.CheckConstraint(condition=~Q(phone="") | ~Q(email=""), name="lead_has_contact"),
            models.CheckConstraint(condition=Q(status__in=["New", "Contacted", "Qualified", "Won", "Lost"]), name="lead_valid_status"),
        ]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        self.phone = self.phone.strip()
        self.email = self.email.strip()
        if not self.name:
            raise ValidationError({"name": "Ismni kiriting."})
        validate_contact(self.phone, self.email)

    def __str__(self):
        return self.name
