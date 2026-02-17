import os
import random
import sqlite3
from math import atan2, cos, radians, sin, sqrt

import geohash2
import osmnx as ox

db_path = os.path.join(os.path.dirname(__file__), "db", "ride_hailing.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

G = ox.load_graphml("bengaluru.graphml")
print("Loaded city : Bengaluru")


# Find nearby drivers
def FindDrivers(user_geohash):
    # we have to find drivers where the geohash is same till the first 5 characters
    search_region = user_geohash[:-3] + "%"
    query = """
        SELECT * FROM Drivers
        WHERE geohash LIKE ?
    """

    res = cursor.execute(query, (search_region,))
    drivers = res.fetchall()

    # rewrite this to put vehicle type and checking if status is available
    filtered_drivers = filterDrivers(drivers, "")

    return filtered_drivers


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
def filterDrivers(drivers, vehicleTypeRequested):
    """
    Correct vehicle type (UberX / Auto / Moto / Premium)
    Available status = true
    Not in another trip
    Not temporarily paused
    Not too far (ETA > threshold)
    High cancellation probability drivers may be deprioritized
    """
    pass


# Calc ETA for each driver
def CalculateEta(distance_km):
    avg_speed = 18
    traffic_multiplier = random.uniform(1.2, 2.5)

    eta = (distance_km / avg_speed) * traffic_multiplier * 60
    return eta


# Score and Rank Drivers
def Score_RankDrivers(lat_u, lng_u):
    user_geohash = geohash2.encode(lat_u, lng_u, precision=8)
    available_drivers = FindDrivers(user_geohash)
    ranked_results = []

    for driver in available_drivers:
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

        ranked_results.append(driver_info)

    ranked_results.sort(key=lambda x: x["calculated_score"])
    return ranked_results


# Picking the best driver
def PickBestDriver():
    """
    Use Hungarian Algo for high demand
    Use K-nearest Neighbor selection for normal demand
    """

    pass


def main():
    lat_u = 13.032080
    lng_u = 77.563824

    ranked_drivers = Score_RankDrivers(lat_u, lng_u)
    for i, driver in enumerate(ranked_drivers):
        name = driver["Name"]
        ETA = driver["ETA"]
        score = driver["calculated_score"]

        print(f"{i + 1}. {name} - {ETA} - {score}")


if __name__ == "__main__":
    main()
    conn.close()


#   main -> score_RankDriver -> [(FindDriver -> filterDrivers), calculateEta]
# ---
# Driver definition
# Driver_id
# Name
# Ph_no
# Veh_Type
# Veh_Model
# Veh_Num
# Veh_Colour
# Status
# Lat
# Lng
# Rating
# Acceptance_Rate
# Cancel_Rate
# Updated_at
# Created_at
