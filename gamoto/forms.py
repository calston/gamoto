from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django import forms
from django.core import validators


def validate_ipv4_cidr(value):
    """
    Validates a CIDR field
    """

    if '/' in value:
        value, prefix = value.split('/')
        try:
            assert(1 <= int(prefix) <= 32)
        except AssertionError:
            raise validators.ValidationError(
                "CIDR prefix must be between 1 and 32")
        except ValueError:
            raise validators.ValidationError(
                "CIDR prefix must be an integer")

    validators.validate_ipv4_address(value)


class CIDRField(forms.GenericIPAddressField):
    def __init__(self, *a, **kwargs):
        self.default_validators = [validate_ipv4_cidr]
        forms.CharField.__init__(self, *a, **kwargs)


class GroupForm(forms.ModelForm):
    """
    Form for creating endpoint groups
    """
    class Meta:
        model = Group
        exclude = ()

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        permission_query = Permission.objects.filter(
            content_type=ContentType.objects.get(app_label='subnet')
        ).order_by('name')

        self.fields['permissions'].queryset = permission_query
        self.fields['permissions'].label_from_instance = self.label_permission

    def label_permission(self, obj):
        subnet = obj.codename.split('_')[-1]
        return obj.name + ': ' + subnet


class UserGroupForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ('password', 'user_permissions', 'username', 'first_name',
                   'last_name', 'last_login', 'is_staff', 'is_active',
                   'is_superuser', 'email', 'date_joined')


class SubnetForm(forms.ModelForm):
    """
    Form for creating endpoint groups
    """
    class Meta:
        model = Permission
        exclude = ()


class GroupSubnetForm(forms.Form):
    """
    Add subnet to group form
    """
    name = forms.CharField(min_length=2, max_length=128)
    subnet = CIDRField()
