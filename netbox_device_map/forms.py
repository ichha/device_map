from django import forms

from dcim.models import DeviceRole, Device
from ipam.models import VLANGroup, VLAN
from netbox.forms import NetBoxModelForm  # For model forms
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField


class DeviceMapFilterForm(forms.Form):  # Removed BootstrapMixin
    vlan_group = DynamicModelChoiceField(
        queryset=VLANGroup.objects.all(),
        required=False,
        label="VLAN group",
        help_text="VLAN group for VLAN selection"
    )
    vlan = DynamicModelChoiceField(
        queryset=VLAN.objects.all(),
        label="VLAN",
        required=False,
        help_text="Filter devices by VLAN attached to any device interface",
        query_params={"group_id": "$vlan_group"}
    )
    device_roles = DynamicModelMultipleChoiceField(
        queryset=DeviceRole.objects.all(),
        required=False,
        label="Device roles",
        help_text="Display devices of only the specified device roles"
    )
    calculate_connections = forms.BooleanField(
        required=False,
        label="Calculate connections between devices",
        initial=True
    )


class ConnectedCpeForm(forms.Form):  # No change needed here
    vlan = forms.ModelChoiceField(
        queryset=VLAN.objects.all(),
        required=False
    )
