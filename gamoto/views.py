# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect

from gamoto import users


@login_required
def index(request):
    user_name = request.user.username

    passwd = users.getUser(user_name)

    return render(request, "index.html", {
        'passwd': passwd,
        'name': request.user.get_full_name()
    })


@login_required
def enroll_user(request):
    user_name = request.user.username
    passwd = users.getUser(user_name)
    if not passwd:
        users.createUser(user_name)

    return redirect('index')