from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Message, Conversation
from projects.models import Project

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.none(), label="Select Collaborator")
    # Keep conversation hidden, but bind it via the form so you can use form.save(commit=False)
    conversation = forms.ModelChoiceField(
        queryset=Conversation.objects.none(),
        required=False,
        widget=forms.HiddenInput()
        attachments = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"multiple": True}))
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body', 'importance', 'conversation']  # include conversation if you want form to bind it

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if not user:
            self.fields['recipient'].queryset = User.objects.none()
            self.fields['conversation'].queryset = Conversation.objects.none()
        else:
            shared_projects = Project.objects.filter(Q(owner=user) | Q(collaborators=user))

            collaborators = User.objects.filter(
                Q(projects__in=shared_projects) | Q(collaborations__in=shared_projects)
            ).exclude(id=user.id).distinct()

            self.fields['recipient'].queryset = collaborators
            self.fields['recipient'].label_from_instance = lambda u: (u.get_full_name() or u.username)

            # Limit conversation choices to threads the current user participates in - KR 09/08/2025
            self.fields['conversation'].queryset = Conversation.objects.filter(participants=user)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Send Message', css_class='btn btn-primary w-100 mt-3'))

    def clean_recipient(self):
        """Make sure you can’t message yourself and recipient is in your shared projects set."""
        recipient = self.cleaned_data['recipient']
        if self.initial.get('current_user_id') and recipient.id == self.initial['current_user_id']:
            raise forms.ValidationError("You can’t send a message to yourself.")
        return recipient