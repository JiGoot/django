import logging
from merchant.models.merchant import Merchant

from user.models import User
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django_hosts.resolvers import reverse


logger = logging.getLogger(__name__) 


class Merchant__LoginView(LoginView):
    template_name = 'merchant/auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse('dashboard', host='merchant')

    def form_valid(self, form):
        try:
            if form.get_user().merchant:
                return super().form_valid(form)  # This will use our get_success_url()
        except Merchant.DoesNotExist:
            messages.error(self.request, "Vous n'avez pas de profil vendeur.")
            return self.render_to_response(
                self.get_context_data(form=form)
            )


class Merchant__LogoutView(LogoutView):
    template_name = 'merchant/auth/logout.html'           # your custom template


class Merchant__DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'merchant/index.html' 

    def get_login_url(self):
        return reverse('login', host='merchant')

    def dispatch(self, request, *args, **kwargs):
        try:
            user:User =request.user
            merchant:Merchant = user.merchant # Check if user has a merchant profile
            if user.is_active and merchant.is_active:
                return super().dispatch(request, *args, **kwargs)
            else:
                return render(request, 'merchant/auth/not_active.html', status=403)
        except Merchant.DoesNotExist:
            return render(request, 'merchant/auth/not_a_merchant.html', status=403)
        except:
            return super().dispatch(request, *args, **kwargs)
