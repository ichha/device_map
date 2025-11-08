from dcim.models import Device, Site, Cable
from .settings import plugin_settings
from .helpers import get_device_location, LatLon

geomap_settings = plugin_settings['geomap_settings']


def configure_leaflet_map(map_id: str, devices: dict[Device, LatLon] | None = None, calculate_connections=True) -> dict:
    """
    Generate a Leaflet map showing sites, devices, and cable connections.
    :param map_id: initialize the map on the div with this id
    :param devices: dictionary of Device -> (latitude, longitude)
    :param calculate_connections: include cables between devices
    """
    map_config = dict(**geomap_settings, map_id=map_id)
    markers: list[dict] = []
    connections: set[tuple[LatLon, LatLon]] = set()

    # --- Add Site markers ---
    for site in Site.objects.exclude(latitude=None).exclude(longitude=None):
        markers.append(dict(
            position=(site.latitude, site.longitude),
            icon="site",
            type="site",
            site=dict(
                id=site.id,
                name=site.name,
                url=site.get_absolute_url(),
            )
        ))

    # --- Add Device markers ---
    devices_with_loc = {}
    all_devices = Device.objects.prefetch_related("site", "role")
    for device in all_devices:
        # Get coordinates: from custom field or site fallback
        if location := get_device_location(device):
            devices_with_loc[device] = location
        elif device.site and device.site.latitude and device.site.longitude:
            devices_with_loc[device] = (device.site.latitude, device.site.longitude)
        else:
            continue  # Skip devices with no location

        position = devices_with_loc[device]
        markers.append(dict(
            position=position,
            icon=device.role.slug if device.role else "unknown",
            type="device",
            device=dict(
                id=device.id,
                name=device.name,
                site=device.site.name if device.site else "No Site",
                url=device.get_absolute_url(),
                role=device.role.name if device.role else "Unknown"
            )
        ))

    # --- Add Cable connections (device to device) ---
    if calculate_connections:
        for cable in Cable.objects.select_related("termination_a", "termination_b"):
            try:
                dev_a = getattr(cable.termination_a, "device", None)
                dev_b = getattr(cable.termination_b, "device", None)
                if not dev_a or not dev_b:
                    continue

                pos_a = devices_with_loc.get(dev_a) or get_device_location(dev_a)
                pos_b = devices_with_loc.get(dev_b) or get_device_location(dev_b)

                if pos_a and pos_b:
                    connections.add((pos_a, pos_b))
            except Exception:
                continue  # skip malformed cables

    # --- Update map configuration ---
    map_config.update(
        markers=markers,
        connections=list(connections)
    )

    return map_config
