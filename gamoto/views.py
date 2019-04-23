# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required

from django.shortcuts import render

from gamoto import users


@login_required
def index(request):
    user_name = request.user.username

    passwd = users.getUser(user_name)
    print(passwd)

    return render(request, "index.html", {
        'passwd': passwd,
        'name': request.user.get_full_name()
    })


@login_required
def enroll_user(request):
    user_name = request.user.username
    passwd = users.getUser(user_name)

    return render(request, "enrollment.html", {
        'passwd': passwd
    })
