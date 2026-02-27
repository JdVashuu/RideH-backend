import uuid

from db.db import conn, cursor
from schema import FareCreate
from Services.Fares import create_fare
from Services.Matching import CalculateEta


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


# Trip_id, Rider_id, Driver_id, Pickup_lat, Pickup_lng, Drop_lat, Drop_lng, Distance, Fare, Status, Requested_at, Accepted_at, Started_at, Completed_at, Cancelled_at
