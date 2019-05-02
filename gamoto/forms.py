from django.contrib.auth.models import Group, Permission
from django import forms
from django.core import validators


def validate_ipv4_cidr(value):
    """
    Validates a CIDR field
    """

    print(value)
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
    # password = forms.CharField(widget=forms.PasswordInput(), initial='')
    class Meta:
        model = Group
        exclude = ()


class SubnetForm(forms.ModelForm):
    """
    Form for creating endpoint groups
    """
    # password = forms.CharField(widget=forms.PasswordInput(), initial='')
    class Meta:
        model = Permission
        exclude = ()


class GroupSubnetForm(forms.Form):
    """
    Add subnet to group form
    """
    name = forms.CharField(min_length=2, max_length=128)
    subnet = CIDRField()
