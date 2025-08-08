from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Message
from projects.models import Project

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.none(), label="Select Collaborator")

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body', 'importance']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Projects I can see (owner or collaborator) - KR 08/08/2025
        shared_projects = Project.objects.filter(
            Q(owner=user) | Q(collaborators=user)
        )

        # Anyone else attached to those projects (owners or collaborators), not me - KR 08/08/2025
        collaborators = User.objects.filter(
            Q(projects__in=shared_projects) |  # owners of those projects - KR 08/08/2025
            Q(collaborations__in=shared_projects)  # collaborators on those projects - KR 08/08/2025
        ).exclude(id=user.id).distinct()

        self.fields['recipient'].queryset = collaborators
        self.fields['recipient'].label_from_instance = (
            lambda u: u.get_full_name() or u.username
        )

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Send Message', css_class='btn btn-primary w-100 mt-3'))