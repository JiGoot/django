from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from core import settings

from core.rabbitmq.broker import publisher

from django.contrib.auth.forms import PasswordResetForm


# views.py
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from .tasks import send_password_reset_email



class User__PasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'auth/password_reset/reset.html'
    email_template_name = 'auth/password_reset/email/verify_link.html'
    html_email_template_name = 'auth/password_reset/email/verify_link.html'
    from_email = f"JiGoot <{settings.EMAIL_HOST_USER}>"
    subject_template_name = 'auth/password_reset/email/subject.txt'
    success_url = reverse_lazy('password_reset_done')
    success_message = "Un lien de réinitialisation a été envoyé à votre adresse e-mail."

    def form_valid(self, form: PasswordResetForm):
        user_email = form.cleaned_data["email"]
        # Prepare context
        context = {
            'domain': self.request.get_host(),
            'site_name': self.get_context_data().get('site_name', 'JiGoot'),
            'protocol': 'https' if self.request.is_secure() else 'http',
        }
        # Queue the async task
        publisher.publish(send_password_reset_email, user_email, context)
        return super().form_valid(form)



from django.contrib.auth.views import PasswordResetConfirmView

class User__PasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'auth/password_reset/confirm.html'