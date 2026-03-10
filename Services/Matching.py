import os
import random
from math import atan2, cos, radians, sin, sqrt

import geohash2

from db.db import (
    get_connection,
    release_connection,
    sqlite_query,
)


# Find nearby drivers
def FindDrivers(user_geohash):
    # precision 5 - 4.9km x 4.9km
    # precision 4 - 39km x 19km

    precisions = [5, 4]

    for p in precisions:
        search_region = user_geohash[:p] + "%"
        query = 'SELECT * FROM "Drivers" WHERE "geohash" LIKE %s'
        drivers = sqlite_query(query, (search_region,))
        if len(drivers) > 10:
            print(f"DEBUG: Found {len(drivers)} drivers at precision {p}")
            return drivers


def haversineDist(lat1, lng1, lat2, lng2, precision):
    R = 6371_000  # meters

    dlat = radians(lat1 - lat2)
    dlng = radians(lng1 - lng2)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    dist_m = R * c  # meters
    dist_km = round(dist_m / 1000, precision)

    return dist_km


# Filter drivers with constraints
def filterDrivers(drivers, vehtype_req):
    filtered = []
    print(f"DEBUG: Filtering {len(drivers)} drivers for vehicle type: '{vehtype_req}'")
    for driver in drivers:
        if (
            driver["Status"] == "available"
            and driver["Veh_Type"].lower() == vehtype_req.lower()
        ):
            filtered.append(driver)

    return filtered


# Calc ETA for each driver
def CalculateEta(distance_km):
    avg_speed = 18
    traffic_multiplier = random.uniform(1.2, 2.5)

    eta = (distance_km / avg_speed) * traffic_multiplier * 60
    return eta


# Score and Rank Drivers
def Score_RankDrivers(lat_u, lng_u, vehtype_req):
    user_geohash = geohash2.encode(lat_u, lng_u, precision=8)
    available_drivers = FindDrivers(user_geohash)
    filtered_drivers = filterDrivers(available_drivers, vehtype_req)

    print(f"DEBUG: Found {len(available_drivers)} drivers in geohash region.")
    print(f"DEBUG: {len(filtered_drivers)} drivers match vehicle type {vehtype_req}")

    ranked_results = []

    for driver in filtered_drivers:
        driver_info = dict(driver)

        lat_d = driver_info["Lat"]
        lng_d = driver_info["Lng"]
        acceptance_rate = driver_info["Acceptance_Rate"]

        proximity = haversineDist(
            lat_u, lng_u, lat_d, lng_d, 2
        )  # distance between driver user
        ETA = CalculateEta(proximity)

        score = (
            (0.5 * ETA) + (0.3 * proximity) - (0.2 * acceptance_rate)
        )  # Sort ascending

        driver_info["calculated_score"] = score
        driver_info["ETA"] = int(ETA)
        driver_info["Distance"] = proximity

        ranked_results.append(driver_info)

    ranked_results.sort(key=lambda x: x["calculated_score"])
    return ranked_results


def match_driver(lat, lng, vehicle_type):
    ranked = Score_RankDrivers(lat, lng, vehicle_type)

    for driver in ranked:
        # Atomic Update : only update is status is still available
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                        UPDATE "Drivers"
                        SET "Status" = 'matched'
                        WHERE "Driver_id" = %s
                        AND "Status" = 'available'
                    """,
                    (driver["Driver_id"],),
                )

                # In case of multiple requests for same driver, rowcount = 1 indicates we won
                if cursor.rowcount == 1:
                    conn.commit()
                    return driver, driver["ETA"], driver["Distance"]
                else:
                    conn.rollback()
        finally:
            release_connection(conn)

    return None, None, None


#   main -> score_RankDriver -> [(FindDriver -> filterDrivers), calculateEta]
