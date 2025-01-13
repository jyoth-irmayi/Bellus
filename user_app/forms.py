from django import forms
from .models import UserDetails
from django.contrib.auth.hashers import check_password
from .models import Address


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        try:
            user = UserDetails.objects.get(email=email)
        except UserDetails.DoesNotExist:
            raise forms.ValidationError("Invalid email or password.")

        if not check_password(password, user.password):
            raise forms.ValidationError("Invalid email or password.")

        # if not user.is_blocked:
        #     raise forms.ValidationError("Your account is blocked. Please contact support.")

        cleaned_data['user'] = user  # Add the user instance to cleaned_data for access in views
        return cleaned_data


# class UserProfileForm(forms.ModelForm):
#     class Meta:
#         model = UserProfile
#         fields = ['full_name', 'email', 'phone_number', 'gender']
#         widgets = {
#             'full_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#             'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
#             'gender': forms.Select(attrs={'class': 'form-control'}),
#         }
