import asyncio
from math import atan2, cos, radians, sin, sqrt

from Services.WebSocketManager import manager


def haversine(lat1, lng1, lat2, lng2):
    R = 6371_000  # meters

    dlat = radians(lat1 - lat2)
    dlng = radians(lng1 - lng2)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    dist_m = R * c  # meters

    return dist_m


async def simulate_driver(trip_id, route, speed_kmh=35):
    speed_mps = speed_kmh * 1000 / 3600

    for i in range(len(route) - 1):
        if get_trip_status(trip_id) in ["completed", "cancelled", "None"]:
            break

        lat1, lng1 = route[i]
        lat2, lng2 = route[i + 1]

        distance = haversine(lat1, lng1, lat2, lng2)
        time_required = distance / speed_mps

        await manager.send_location(
            trip_id, {"lat": lat1, "lng": lng1, "speed": speed_kmh}
        )

        await asyncio.sleep(time_required)
