from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import AnonRateThrottle
from .models import Lead
from .serializers import LeadSerializer


class LoginThrottle(AnonRateThrottle):
    rate = "10/min"


class TokenLoginView(ObtainAuthToken):
    throttle_classes = [LoginThrottle]


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "phone", "email", "source"]

    def get_queryset(self):
        queryset = Lead.objects.all()
        # Filters apply to lists only; detail URLs always identify the same lead.
        if self.action == "list":
            status = self.request.query_params.get("status", "")
            if status:
                if status not in Lead.Status.values:
                    raise ValidationError({"status": "Status: New, Contacted, Qualified, Won yoki Lost bo‘lishi kerak."})
                queryset = queryset.filter(status=status)
        return queryset

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset) if self.action == "list" else queryset
