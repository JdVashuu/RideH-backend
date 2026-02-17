from db import cursor


def calculate_surge(lat, lng):

    # Simple supply-demand simulation
    available = cursor.execute("""
        SELECT COUNT(*) as count
        FROM Drivers
        WHERE status = 'AVAILABLE'
    """).fetchone()["count"]

    active_trips = cursor.execute("""
        SELECT COUNT(*) as count
        FROM Trips
        WHERE status = 'REQUESTED'
    """).fetchone()["count"]

    if available == 0:
        return 2.0

    ratio = active_trips / available

    if ratio > 1.5:
        return 1.8
    elif ratio > 1.0:
        return 1.3
    else:
        return 1.0
