# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist

from gamoto import users, openvpn


def returnFile(name, content_type, data):
    response = HttpResponse(data, content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename="%s"' % name
    return response


@login_required
def index(request):
    user_name = request.user.username

    passwd = users.getUser(user_name)

    vpn = openvpn.getClient(user_name)

    return render(request, "index.html", {
        'passwd': passwd,
        'vpn': vpn,
        'admin': request.user.is_superuser,
        'name': request.user.get_full_name(),
        'sbactive': 'index'
    })


@login_required
def vpn_zip(request):
    user_name = request.user.username
    passwd = users.getUser(user_name)

    return returnFile(user_name + ".zip", "application/zip",
                      users.getVPNZIP(user_name))


@login_required
def reset_2fa(request):
    user_name = request.user.username
    codes, authurl = users.configureTOTP(user_name)

    return render(request, "enroll.html", {
        'name': request.user.get_full_name(),
        'authurl': authurl,
        'codes': codes,
        'reset': True
    })


@login_required
def enroll_user(request):
    user_name = request.user.username
    passwd = users.getUser(user_name)

    if passwd:
        return redirect('index')

    users.createUser(user_name)
    users.createVPN(user_name)
    codes, authurl = users.configureTOTP(user_name)

    return render(request, "enroll.html", {
        'name': request.user.get_full_name(),
        'authurl': authurl,
        'codes': codes
    })


@user_passes_test(lambda u: u.is_superuser)
def admin_endpoints(request):
    return render(request, "admin_endpoints.html", {
        'sbactive': 'endpoints'
    })


@user_passes_test(lambda u: u.is_superuser)
def admin_users(request):
    all_users = []
    for user in User.objects.all():
        user_name = user.username
        try:
            social = user.social_auth.get()
        except ObjectDoesNotExist as err:
            continue

        groups = user.groups.all()
        passwd = users.getUser(user_name)

        enrolled = False
        if passwd:
            enrolled = True

        vpn = openvpn.getClient(user_name)

        all_users.append({
            'username': user_name,
            'name': user.get_full_name(),
            'email': user.email,
            'provider': social.provider,
            'last_login': user.last_login,
            'enrolled': enrolled,
            'vpn': vpn,
        })

    all_users.sort(key=lambda x: x['username'])

    return render(request, "admin_users.html", {
        'sbactive': 'users',
        'users': all_users
    })
