from typing import Optional, Tuple
from packaging import version

from dcim.models import Device
from django.db.models import QuerySet, Q
from ipam.models import VLAN
from netbox.settings import VERSION

from .settings import plugin_settings


# --- Constants ---
LOCATION_CF_NAME = plugin_settings['device_geolocation_cf']

# Fix invalid NetBox Docker version like '4.4.4-Docker-3.4.1'
NETBOX_VERSION = version.parse(VERSION.split('-')[0])

LatLon = Tuple[float, float]


# --- Functions ---

def get_device_location(device: Device) -> Optional[LatLon]:
    """Extract device geolocation from custom field as (lat, lon)."""
    if location_cf := device.custom_field_data.get(LOCATION_CF_NAME):
        try:
            return tuple(map(float, location_cf.replace(' ', '').split(',', maxsplit=1)))
        except (ValueError, AttributeError):
            return None
    return None


def get_connected_devices(device: Device, vlan: Optional[VLAN] = None) -> QuerySet[Device]:
    """
    Get list of connected devices to the specified device.
    If VLAN is specified, only include devices whose interfaces use that VLAN.
    """
    included_interfaces = device.interfaces.all()
    if vlan is not None:
        included_interfaces = included_interfaces.filter(
            Q(untagged_vlan=vlan) | Q(tagged_vlans=vlan)
        )

    # NetBox 3.3+ uses cables and terminations for interface links
    return (
        Device.objects.filter(
            interfaces__cable__terminations__interface__in=included_interfaces
        )
        .exclude(pk=device.id)
        .distinct()
    )


def are_devices_connected(device_a: Device, device_b: Device) -> bool:
    """Check if two devices are directly connected by a cable."""
    return Device.objects.filter(
        interfaces__cable__terminations__interface__in=device_a.interfaces.all(),
        pk=device_b.pk,
    ).exists()
