from db.db import sqlite_fetchone


def calculate_surge(lat, lng):

    # Simple supply-demand simulation
    available_res = sqlite_fetchone("""
        SELECT COUNT(*) as count
        FROM "Drivers"
        WHERE "Status" = 'available'
    """)
    available = available_res["count"] if available_res else 0

    active_trips_res = sqlite_fetchone("""
        SELECT COUNT(*) as count
        FROM "Trips"
        WHERE "Status" = 'requested'
    """)
    active_trips = active_trips_res["count"] if active_trips_res else 0

    if available == 0:
        return 2.0

    ratio = active_trips / available

    if ratio > 1.5:
        return 1.8
    elif ratio > 1.0:
        return 1.3
    else:
        return 1.0
