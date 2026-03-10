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


async def simulate_driver(trip_id, route, speed_kmh=100, total_time=None):
    from db.db import sqlite_execute, sqlite_fetchone
    from Services.Trips import get_trip_status

    # Calculate sleep time per step
    if total_time:
        sleep_per_step = total_time / max(len(route) - 1, 1)
    else:
        speed_mps = speed_kmh * 1000 / 3600

    # Get driver_id
    trip = sqlite_fetchone(
        """SELECT "Driver_id" FROM "Trips" WHERE "Trip_id" = ?""", (trip_id,)
    )
    driver_id = trip["Driver_id"] if trip else None

    for i in range(len(route) - 1):
        if get_trip_status(trip_id) in ["completed", "cancelled", "None"]:
            break

        lat1, lng1 = route[i]

        if not total_time:
            lat2, lng2 = route[i + 1]
            distance = haversine(lat1, lng1, lat2, lng2)
            time_required = distance / speed_mps
        else:
            time_required = sleep_per_step

        if driver_id:
            sqlite_execute(
                """UPDATE "Drivers" SET "Lat" = ?, "Lng" = ? WHERE "Driver_id" = ?""",
                (lat1, lng1, driver_id),
            )

        await manager.send_location(
            trip_id, {"lat": lat1, "lng": lng1, "speed": speed_kmh}
        )

        await asyncio.sleep(time_required)
