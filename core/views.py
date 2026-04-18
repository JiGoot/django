from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request, 'website/index.html')


def consignment_console(request):
    return render(request, 'consignment/index.html')


def guidelines_terms(request):
    return redirect("https://github.com/JiGoot/terms/blob/main/fr/guidelines.md")


def customer_terms(request):
    return redirect("https://github.com/JiGoot/terms/blob/main/fr/customer-terms.md")


def kitchen_terms(request):
    return redirect("https://github.com/JiGoot/terms/blob/main/fr/kitchen-terms.md")


def privacy_policies(request):
    return redirect("https://github.com/JiGoot/terms/blob/main/fr/privacy-policy.md")

