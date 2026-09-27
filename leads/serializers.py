from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Lead, validate_contact


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ("id", "name", "phone", "email", "source", "note", "status", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        phone = attrs.get("phone", getattr(self.instance, "phone", ""))
        email = attrs.get("email", getattr(self.instance, "email", ""))
        try:
            validate_contact(phone, email)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        return attrs
