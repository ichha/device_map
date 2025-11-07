from dcim.models import Device
from .settings import plugin_settings
from .helpers import get_connected_devices, LatLon

geomap_settings = plugin_settings['geomap_settings']
CPE_DEVICE_ROLE_NAME = plugin_settings['cpe_device_role']

def configure_leaflet_map(map_id: str, devices: dict[Device, LatLon], calculate_connections=True) -> dict:
    valid_devices = {
        device: pos for device, pos in devices.items()
        if device and pos and hasattr(device, 'id')
    }
    device_id_to_latlon = {device.id: position for device, position in valid_devices.items()}
    map_config = dict(**geomap_settings, map_id=map_id)
    markers: list[dict] = []
    connections: set[frozenset] = set()
    for device, position in valid_devices.items():
        role = getattr(device.device_role, 'name', 'Unknown')
        role_slug = getattr(device.device_role, 'slug', 'default')
        markers.append(dict(
            position=position,
            icon=role_slug,
            device=dict(
                id=device.id,
                name=device.name,
                url=device.get_absolute_url(),
                role=role
            )
        ))
        if calculate_connections:
            for peer_device_id in get_connected_devices(device).filter(id__isnull=False).values_list('id', flat=True):
                if peer_position := device_id_to_latlon.get(peer_device_id):
                    connections.add(frozenset((position, peer_position)))
    map_config.update(markers=markers, connections=[tuple(c) for c in connections])
    return map_config
