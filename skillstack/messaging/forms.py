from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Message, Conversation
from projects.models import Project
from django.core.exceptions import ValidationError

from django.forms.widgets import ClearableFileInput
class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class MultiFileField(forms.FileField):
    """A FileField that accepts multiple files and returns a list."""
    def to_python(self, data):
        # When no files are submitted, return an empty list
        if not data:
            return []
        # If the widget returned a list/tuple (multiple files), keep it as list
        if isinstance(data, (list, tuple)):
            return [f for f in data if f]
        # Single file -> wrap in a list
        return [data]

    def validate(self, data):
        # `data` is a list here
        if self.required and not data:
            raise ValidationError(self.error_messages['required'], code='required')
        # Optionally run validators on each file
        for f in data:
            for v in self.validators:
                v(f)

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.none(), label="Select Collaborator")
    conversation = forms.ModelChoiceField(
        queryset=Conversation.objects.none(),
        required=False,
        widget=forms.HiddenInput()
    )
    
    attachments = MultiFileField(
        required=False,
        widget=MultiFileInput(attrs={'multiple': True})
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body', 'importance', 'conversation', 'attachments']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            shared_projects = Project.objects.filter(Q(owner=user) | Q(collaborators=user))
            collaborators = User.objects.filter(
                Q(projects__in=shared_projects) | Q(collaborations__in=shared_projects)
            ).exclude(id=user.id).distinct()
            self.fields['recipient'].queryset = collaborators
            self.fields['recipient'].label_from_instance = lambda u: (u.get_full_name() or u.username)
            self.fields['conversation'].queryset = Conversation.objects.filter(participants=user)
        else:
            self.fields['recipient'].queryset = User.objects.none()
            self.fields['conversation'].queryset = Conversation.objects.none()

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'

    def clean_attachments(self):
        """Return a list of uploaded files (or an empty list). Avoids the
        'No file was submitted' validation error when the field is optional
        and the widget allows multiple selections.
        """
        files = self.cleaned_data.get('attachments')
        return files or []