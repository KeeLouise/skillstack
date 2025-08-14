from django import forms
from .models import PortfolioLink

class PortfolioLinkForm(forms.ModelForm):
    class Meta:
        model  = PortfolioLink
        fields = ["title", "url", "image_file"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Link title"}),
            "url":   forms.URLInput(attrs={"placeholder": "https://example.com"}),
        }