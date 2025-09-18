from django.conf import settings
from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        remember = self.request.POST.get('remember_me') == 'on'
        # If unchecked, expire at browser close; if checked, use default age
        self.request.session.set_expiry(0 if not remember else settings.SESSION_COOKIE_AGE)
        return response
