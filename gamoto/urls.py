"""gamoto URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings

from gamoto import views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='login.html',
            extra_context={'oauth': settings.GOOGLE_AUTH}
        ),
        name="login"
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.index, name="index"),
    path('enroll', views.enroll_user, name="enroll"),
    path('reset_2fa', views.reset_2fa, name="reset_2fa"),
    path('vpn_zip', views.vpn_zip, name="vpn_zip"),
    path('vpn_tblk', views.vpn_tblk, name="vpn_tblk")
]
