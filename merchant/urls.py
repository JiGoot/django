from django.urls import path
from merchant.views import (
    Merchant__DashboardView,  
    Merchant__LoginView,
    Merchant__LogoutView,
)

urlpatterns = [
    # 🔐 Login
    path('auth/login/', Merchant__LoginView.as_view(), name='login'), 
    path('auth/logout/', Merchant__LogoutView.as_view(), name='logout'),
    # 
    path('', Merchant__DashboardView.as_view(), name='dashboard'),
]
