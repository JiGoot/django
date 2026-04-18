from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model

from core import settings
from user.models import User


def send_password_reset_email(email:str, context: dict):
    '''
    The password reset token depend is tidht to the uer id, current password and timstamp.
    So the reset token becomes invalid, if the user poswword change, 
    or if the timstamp is more than [PASSWORD_RESET_TIMEOUT] old
    '''
    UserModel = get_user_model()
    try:
        user:User = UserModel.objects.get(email=email)
        context.update({
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'user': user,
        })

        subject = render_to_string('auth/password_reset/email/subject.txt', context).strip()
        message = render_to_string('auth/password_reset/email/verify_link.html', context)

        send_mail(
            subject,
            '', 
            f"JiGoot <{settings.EMAIL_HOST_USER}>",
            [user.email],
            html_message=message,
            fail_silently=False,
        )
        return True
    except UserModel.DoesNotExist:
        return False
