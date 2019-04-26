# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views

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
        'name': request.user.get_full_name()
    })


@login_required
def vpn_zip(request):
    user_name = request.user.username
    passwd = users.getUser(user_name)

    return returnFile(user_name + ".zip", "application/zip",
                      users.getVPNZIP(user_name))


@login_required
def vpn_tblk(request):
    user_name = request.user.username
    passwd = users.getUser(user_name)

    return returnFile(user_name + ".tblk", "application/zip", "test")


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
