from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


def validate_ipv4_cidr(value):
    """
    Validates a CIDR field
    """
    vals = value.split(',')

    for val in vals:
        if '/' in val:
            ip, prefix = val.split('/')
            try:
                assert(0 <= int(prefix) <= 32)
            except AssertionError:
                raise validators.ValidationError(
                    "CIDR prefix must be between 0 and 32")
            except ValueError:
                raise validators.ValidationError(
                    "CIDR prefix must be an integer")

            validators.validate_ipv4_address(ip)


class CIDRField(forms.GenericIPAddressField):
    def __init__(self, *a, **kwargs):
        self.default_validators = [validate_ipv4_cidr]
        forms.CharField.__init__(self, *a, **kwargs)


class GroupForm(forms.ModelForm):
    """
    Form for creating endpoint groups
    """

    default = forms.BooleanField(initial=False, required=False)

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

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))

    def label_permission(self, obj):
        subnet = obj.codename.split('_')[-1]
        return obj.name + ': ' + subnet


class UserGroupForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ('password', 'user_permissions', 'username', 'first_name',
                   'last_name', 'last_login', 'is_staff', 'is_active',
                   'is_superuser', 'email', 'date_joined')

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))


class SubnetForm(forms.ModelForm):
    """
    Form for creating endpoint groups
    """
    class Meta:
        model = Permission
        exclude = ()

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))


class GroupSubnetForm(forms.Form):
    """
    Add subnet to group form
    """
    name = forms.CharField(min_length=2, max_length=128)
    subnet = CIDRField()

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
