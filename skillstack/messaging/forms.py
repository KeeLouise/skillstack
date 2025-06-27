from django import forms
from django.contrib.auth.models import User
from .models import Message
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.all())
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Send Message', css_class='btn btn-primary w-100 mt-3'))