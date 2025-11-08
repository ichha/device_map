from dcim.models import Device, Site
from django.db.models import Q
from ipam.models import VLAN
from packaging import version
from netbox.settings import VERSION
from .settings import plugin_settings

LOCATION_CF_NAME = plugin_settings['device_geolocation_cf']
NETBOX_VERSION = version.parse(VERSION)
LatLon = tuple[float, float]


def get_device_location(device: Device) -> LatLon | None:
    """Extract device geolocation from custom field or site location."""
    # Try from custom field first
    if location_cf := device.custom_field_data.get(LOCATION_CF_NAME):
        try:
            return tuple(map(float, location_cf.replace(' ', '').split(',', maxsplit=1)))
        except Exception:
            pass
    # Then try from site (if available)
    if hasattr(device, 'site') and getattr(device.site, 'latitude', None) and getattr(device.site, 'longitude', None):
        return (device.site.latitude, device.site.longitude)
    return None


def get_connected_devices(device: Device, vlan: VLAN = None):
    """Get list of connected devices to the specified device."""
    included_interfaces = device.interfaces.all()
    if vlan is not None:
        included_interfaces = included_interfaces.filter(Q(untagged_vlan=vlan) | Q(tagged_vlans=vlan))

    if NETBOX_VERSION < version.parse('3.3.0'):
        return Device.objects.filter(interfaces___link_peer_id__in=included_interfaces)
    else:
        return Device.objects.filter(
            interfaces__cable__terminations__interface__in=device.interfaces.all()
        ).exclude(pk=device.id)
