# messaging/forms.py
from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from crispy_forms.helper import FormHelper
from .models import Message, Conversation
from projects.models import Project
from django.forms.widgets import ClearableFileInput

class MultipleClearableFileInput(ClearableFileInput):
    allow_multiple_selected = True

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.none(), label="Select Collaborator")
    conversation = forms.ModelChoiceField(queryset=Conversation.objects.none(), required=False, widget=forms.HiddenInput())
    attachments = forms.FileField(required=False, widget=MultipleClearableFileInput(attrs={"multiple": True}))

    class Meta:
        model = Message
        fields = ["recipient", "subject", "body", "importance", "conversation", "attachments"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            shared = Project.objects.filter(Q(owner=user) | Q(collaborators=user))
            collabs = User.objects.filter(Q(projects__in=shared) | Q(collaborations__in=shared))\
                                  .exclude(id=user.id).distinct()
            self.fields["recipient"].queryset = collabs
            self.fields["recipient"].label_from_instance = lambda u: (u.get_full_name() or u.username)
            self.fields["conversation"].queryset = Conversation.objects.filter(participants=user)
        else:
            self.fields["recipient"].queryset = User.objects.none()
            self.fields["conversation"].queryset = Conversation.objects.none()

        self.helper = FormHelper()
        self.helper.form_tag = False 