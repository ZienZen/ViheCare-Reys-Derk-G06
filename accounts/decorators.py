from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import ensure_profile


def role_required(role):
    """Allow only logged-in users with the given role; others go to their own dashboard."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            profile = ensure_profile(request.user)
            if profile.role != role:
                messages.error(request, "You don't have access to that page.")
                return redirect('dashboard:home')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
