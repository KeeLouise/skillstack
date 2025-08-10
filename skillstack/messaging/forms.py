from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import Message, Conversation
from projects.models import Project


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Select Collaborator"
    )

    conversation = forms.ModelChoiceField(
        queryset=Conversation.objects.none(),
        required=False,
        widget=forms.HiddenInput()
    )

    attachments = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={'multiple': True}),
        help_text="You can select multiple files."
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body', 'importance', 'conversation', 'attachments']
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': 'Subject (optional)'}),
            'body': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Write your message...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            shared_projects = Project.objects.filter(
                Q(owner=user) | Q(collaborators=user)
            )

            collaborators = User.objects.filter(
                Q(projects__in=shared_projects) |
                Q(collaborations__in=shared_projects)
            ).exclude(id=user.id).distinct()

            self.fields['recipient'].queryset = collaborators
            self.fields['recipient'].label_from_instance = lambda u: (u.get_full_name() or u.username)
            self.fields['conversation'].queryset = Conversation.objects.filter(participants=user)
        else:
            self.fields['recipient'].queryset = User.objects.none()
            self.fields['conversation'].queryset = Conversation.objects.none()

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Send Message', css_class='btn btn-primary w-100 mt-3'))

    def clean_recipient(self):
        recipient = self.cleaned_data['recipient']
        request_user = getattr(self, 'user', None)
        return recipient

    def clean_attachments(self):
        """
        Optional: validate each uploaded file (size/extension/MIME).
        """
        files = self.files.getlist('attachments')
        max_mb = 25
        allowed_exts = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif'}

        for f in files:
            if f.size > max_mb * 1024 * 1024:
                raise forms.ValidationError(f"'{getattr(f, 'name', 'file')}' is larger than {max_mb} MB.")
            name = getattr(f, 'name', '')
            ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
            if ext and ext not in allowed_exts:
                raise forms.ValidationError(f"'{name}' has a disallowed file type.")
        return files