from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )

    invite_emails = forms.CharField(
        required=False,
        label="Invite Collaborators (comma-separated emails)",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. John@example.com, Rob@example.com'})
    )
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'status', 'category']
