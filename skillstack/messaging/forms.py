from django import forms
from django.contrib.auth.models import User
from .models import Message
from projects.models import Project
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.db.models import Q

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.none(), label="Select Collaborator")

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body', 'importance']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        from projects.models import Project
        from django.db.models import Q

        owned_projects = Project.objects.filter(owner=user)
        collaborator_projects = Project.objects.filter(collaborators=user)

        collaborators = User.objects.filter(
            Q(projects__in=owned_projects) | Q(collaborations__in=collaborator_projects)
        ).exclude(id=user.id).distinct()

        self.fields['recipient'].queryset = collaborators

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Send Message', css_class='btn btn-primary w-100 mt-3'))