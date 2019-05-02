# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist

from gamoto import users, openvpn, forms


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
    groups = []

    for group in Group.objects.all():
        subnets = [{
            'id': perm.id,
            'name': perm.name,
            'subnet': perm.codename.split('_')[-1]
        } for perm in group.permissions.all()]

        groups.append({
            'id': group.id,
            'name': group.name,
            'subnets': subnets
        })

    return render(request, "admin_endpoints.html", {
        'sbactive': 'endpoints',
        'admin': request.user.is_superuser,
        'groups': groups
    })


@user_passes_test(lambda u: u.is_superuser)
def group_create(request):
    if request.method == "POST":
        form = forms.GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()
            form.save_m2m()

            return redirect('endpoints')
    else:
        form = forms.GroupForm()

    return render(request, 'admin_group_create.html', {
        'form': form,
        'sbactive': 'endpoints',
        'admin': request.user.is_superuser
    })


@user_passes_test(lambda u: u.is_superuser)
def subnet_create(request):
    if request.method == "POST":
        form = forms.SubnetForm(request.POST)
        if form.is_valid():
            subnet = form.save(commit=False)
            subnet.save()

            return redirect('endpoints')
    else:
        form = forms.SubnetForm()

    return render(request, 'admin_subnet_create.html', {
        'form': form,
        'sbactive': 'endpoints',
        'admin': request.user.is_superuser
    })


@user_passes_test(lambda u: u.is_superuser)
def group_delete(request, group_id):
    grp = Group.objects.get(id=group_id)
    grp.delete()
    return redirect('endpoints')


@user_passes_test(lambda u: u.is_superuser)
def group_subnet_remove(request, group_id, permission_id):
    grp = Group.objects.get(id=group_id)
    perm = Permission.objects.get(id=permission_id)

    grp.permissions.remove(perm)

    return redirect('endpoints')


@user_passes_test(lambda u: u.is_superuser)
def group_subnet_add(request, group_id):
    group = Group.objects.get(id=group_id)

    if request.method == "POST":
        form = forms.GroupSubnetForm(request.POST)
        if form.is_valid():
            gslink = form.cleaned_data

            perm_name = "network_%s" % gslink['subnet']

            content_type = ContentType.objects.get(app_label='subnet')

            try:
                permission = Permission.objects.get(codename=perm_name)
            except ObjectDoesNotExist:
                permission = Permission.objects.create(
                    codename=perm_name,
                    name=gslink['name'],
                    content_type=content_type
                )
                permission.save()

            group.permissions.add(permission)

            return redirect('endpoints')
    else:
        form = forms.GroupSubnetForm()

    return render(request, 'admin_subnet_add.html', {
        'form': form,
        'sbactive': 'endpoints',
        'group_id': group_id,
        'group': group,
        'admin': request.user.is_superuser
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
        'users': all_users,
        'admin': request.user.is_superuser
    })
