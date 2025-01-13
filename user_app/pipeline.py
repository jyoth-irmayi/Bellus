from django.contrib.auth import login
from django.shortcuts import redirect
from .models import UserDetails
from social_core.exceptions import AuthAlreadyAssociated


def create_user(strategy, details, backend, request, user=None, *args, **kwargs):
    fields = {
        'email': details.get('email'),
        'firstname': details.get('firstname'),
        'lastname': details.get('lastname'),
    }

    if not fields['email']:
        return

    # Check if the user exists in the UserDetails model
    existing_user = UserDetails.objects.filter(email=fields['email']).first()
    if existing_user:
        # Try to authenticate if the account is already linked
        try:
            login(request, existing_user, backend='social_core.backends.google.GoogleOAuth2')
            return redirect('homepage')
        except AuthAlreadyAssociated:
            # If account is already associated, just log the user in and redirect
            login(request, existing_user, backend='social_core.backends.google.GoogleOAuth2')
            return redirect('homepage')

    # If the user does not exist, create a new user
    user = UserDetails(
        email=fields['email'],
        firstname=fields['firstname'],
        lastname=fields['lastname'],
    )
    user.set_unusable_password()
    user.save()

    # Log in the newly created user
    login(request, user, backend='social_core.backends.google.GoogleOAuth2')
    return redirect('homepage')
