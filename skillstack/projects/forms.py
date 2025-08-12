from django import forms
from django.core.exceptions import ValidationError
from .models import Project

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class InviteCollaboratorForm(forms.Form):
    email = forms.EmailField(
        label="Collaborator's Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter collaborator email'
        })
    )

class ProjectForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    attachments = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"multiple": True, "class": "form-control"})
    )
    invite_emails = forms.CharField(
        required=False,
        label="Invite Collaborators (comma-separated emails)",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. John@example.com, Rob@example.com'})
    )

    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'status', 'category', 'invite_emails']

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")

        if start and end and end < start:
            self.add_error('end_date', "End date cannot be earlier than start date.")
        return cleaned

class ProjectAttachmentUploadForm(forms.Form):
    files = forms.FileField(
        widget=MultiFileInput(attrs={"multiple": True, "class": "form-control"}),
        required=False,
    )
