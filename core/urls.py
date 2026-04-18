from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from core import views
from django.urls import path
from core.views import customer_terms, guidelines_terms, kitchen_terms, privacy_policies
from user.views import User__PasswordResetConfirmView, User__PasswordResetView
from django.contrib.auth import views as auth_views



urlpatterns = [
    path("", views.home, name="home"),
    # path('auth/login/', auth_views.LoginView.as_view(template_name='auth/login.html', success_url='login'), name='login'),
    path("auth/logout/", auth_views.LogoutView.as_view(template_name="auth/logout.html"), name="logout"),
    path("auth/password-reset/", User__PasswordResetView.as_view(), name="password_reset"),
    path(
        "auth/password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset/done.html"),
        name="password_reset_done",
    ),
    path(
        "auth/reset/<uidb64>/<token>/", User__PasswordResetConfirmView.as_view(), name="password_reset_confirm"
    ),
    path(
        "auth/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset/complete.html"),
        name="password_reset_complete",
    ),
    path("legal/customer-terms/", customer_terms, name="customer-terms"),
    path("legal/kitchen-terms/", kitchen_terms, name="kitchen-terms"),
    path("legal/community-guidelines/", guidelines_terms, name="guidelines"),
    path("legal/privacy-policy/", privacy_policies, name="privacy-policy"),
]
# if settings.DEV:
#     urlpatterns.append(path('silk/', include('silk.urls', namespace='silk')))
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()

# +static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# admin.site.index_title = 'Features area'                 # default: "Site administration"
# admin.site.site_title = 'HTML title from adminsitration' # default: "Django site admin"
# NOTE; Adding [static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)] allow to access to media file with the REST API
# for instance http://127.0.0.1:8000/media/kitchen/img/IMG_3920.JPG
