from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise forms.ValidationError("Invalid login credentials.")
            except User.DoesNotExist:
                raise forms.ValidationError("User with this email does not exist.")

        return cleaned_data
class CustomUserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True, label="Full Name")
    email = forms.EmailField(required=True)
    company = forms.CharField(max_length=150, required=True, label="Company/Freelance Name")

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'company', 'password1', 'password2']
        help_texts = {
            'password1': None,
            'password2': None,
            'username': None,
        }
        widgets = {
            'password1': forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
            'password2': forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

        self.fields['username'].widget.attrs.update({'autocomplete': 'username'})
        self.fields['email'].widget.attrs.update({'autocomplete': 'email'})
        self.fields['full_name'].widget.attrs.update({'autocomplete': 'name'})

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('full_name', css_class='form-group col-md-6 mb-0'),
                Column('company', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
            ),
            Submit('submit', 'Register', css_class='btn btn-primary w-100 mt-3')
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['full_name']
        if commit:
            user.save()
        Profile.objects.update_or_create(user=user, defaults={'company': self.cleaned_data['company']})
        return user
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['full_name']
        if commit:
            user.save()
        Profile.objects.update_or_create(user=user, defaults={'company': self.cleaned_data['company']})
        return user

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(label='Full Name')

    class Meta:
        model = User
        fields = ['first_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Update Profile'))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise forms.ValidationError("This email address is already in use.")
        return email

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['company', 'bio', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Update Profile'))