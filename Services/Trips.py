import asyncio
import uuid

from db.db import conn, cursor, sqlite_fetchone
from schema import FareCreate
from Services.DriverSimulation import simulate_driver
from Services.Fares import create_fare
from Services.Matching import CalculateEta
from Services.RouteService import generate_route


def create_trip(
    Rider_id,
    Driver_id,
    Pickup_lat,
    Pickup_lng,
    Drop_lat,
    Drop_lng,
    Distance,
    surge,
    Status,
    Requested_at,
    Accepted_at,
    Started_at,
    Completed_at,
    Cancelled_at,
):
    trip_id = str(uuid.uuid4())

    fare_data = FareCreate(
        distance=Distance,
        duration=CalculateEta(Distance),
        surge_multiplier=surge,
        currency="inr",
    )

    fare_id = create_fare(fare_data)

    cursor.execute(
        """
        INSERT INTO Trips (
            Trip_id,
           	Rider_id,
           	Driver_id,
           	Pickup_lat,
           	Pickup_lng,
           	Drop_lat,
           	Drop_lng,
           	Distance,
           	Fare,
           	Status,
           	Requested_at,
           	Accepted_at,
           	Started_at,
           	Completed_at,
           	Cancelled_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            trip_id,
            Rider_id,
            Driver_id,
            Pickup_lat,
            Pickup_lng,
            Drop_lat,
            Drop_lng,
            Distance,
            fare_id,
            Status,
            Requested_at,
            Accepted_at,
            Started_at,
            Completed_at,
            Cancelled_at,
        ),
    )

    return trip_id


def get_trip_status(trip_id):
    cursor.execute(
        """
        SELECT Status FROM Trips WHERE Trip_id = ?
    """,
        (trip_id,),
    )
    result = cursor.fetchone()
    return result[0] if result else None


async def start_trip(trip_id):
    trip = sqlite_fetchone(
        "SELECT Pickup_lat, Pickup_lng, Drop_lat, Drop_lng FROM Trips WHERE Trip_id = ?",
        (trip_id,),
    )

    if not trip:
        return {"error": "Trip not found"}

    pickup_lat, pickup_lng, drop_lat, drop_lng = trip

    route = generate_route(pickup_lat, pickup_lng, drop_lat, drop_lng)
    asyncio.create_task(simulate_driver(trip_id, route))


# Trip_id, Rider_id, Driver_id, Pickup_lat, Pickup_lng, Drop_lat, Drop_lng, Distance, Fare, Status, Requested_at, Accepted_at, Started_at, Completed_at, Cancelled_at
