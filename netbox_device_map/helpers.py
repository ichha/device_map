from typing import Tuple, Optional
from packaging import version
from dcim.models import Device
from django.db.models import QuerySet, Q
from ipam.models import VLAN
from netbox.settings import VERSION
from .settings import plugin_settings

LOCATION_CF_NAME = plugin_settings.get('device_geolocation_cf', 'geolocation')
NETBOX_VERSION = version.parse(VERSION.split('-')[0])
LatLon = Tuple[float, float]

def get_device_location(device: Device) -> Optional[LatLon]:
    if not device:
        return None
    location_cf = device.custom_field_data.get(LOCATION_CF_NAME)
    if not location_cf:
        return None
    try:
        lat, lon = map(float, location_cf.replace(' ', '').split(',', maxsplit=1))
        return lat, lon
    except (ValueError, AttributeError):
        return None

def get_connected_devices(device: Device, vlan: Optional[VLAN] = None) -> QuerySet[Device]:
    if not device:
        return Device.objects.none()
    interfaces = device.interfaces.all()
    if vlan is not None:
        interfaces = interfaces.filter(
            Q(untagged_vlan=vlan) | Q(tagged_vlans=vlan)
        )
    connected_devices = Device.objects.filter(
        interfaces__cable__terminations__interface__in=interfaces
    ).exclude(pk=device.pk).distinct()
    return connected_devices

def are_devices_connected(device_a: Device, device_b: Device) -> bool:
    if not device_a or not device_b:
        return False
    return Device.objects.filter(
        pk=device_b.pk,
        interfaces__cable__terminations__interface__in=device_a.interfaces.all(),
    ).exists()
