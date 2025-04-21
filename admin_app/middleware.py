from django.conf import settings
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect



class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        excluded_paths = [reverse('user_login')]
        if request.path not in excluded_paths:
            if request.user.is_authenticated and not request.user.is_active:
                logout(request)
                messages.error(request, 'Your account has been blocked. Please contact customer service.')
                return redirect(settings.LOGIN_URL)

        response = self.get_response(request)
        return response
