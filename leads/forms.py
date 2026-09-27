from django import forms
from .models import Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ("name", "phone", "email", "source", "status", "note")
        widgets = {"note": forms.Textarea(attrs={"rows": 5}), "phone": forms.TextInput(attrs={"type": "tel"})}
        help_texts = {"phone": "Telefon yoki emaildan kamida bittasini kiriting."}


class StatusForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ("status",)
