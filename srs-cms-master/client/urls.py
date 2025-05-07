"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from client.views import home, deaths_home, deaths_edit
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('__reload__/', include('django_browser_reload.urls')),
    path('', home, name='home'),

    path('login/', LoginView.as_view(template_name='client/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_reset/',
         auth_views.PasswordResetView.as_view(template_name='client/password_reset_form.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='client/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='client/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='client/password_reset_complete.html'),
         name='password_reset_complete'),

    path('deaths/', deaths_home, name='deaths_home'),
    path('deaths/edit/<int:id>/', deaths_edit, name='deaths_edit'),
]
