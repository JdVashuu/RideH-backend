import asyncio
import datetime
import uuid

from db.db import sqlite_execute, sqlite_fetchone
from schema import FareCreate
from Services.DriverSimulation import simulate_driver
from Services.Fares import create_fare
from Services.Matching import CalculateEta
from Services.RouteService import generate_route


def update_trip_status(trip_id, status, driver_id=None):
    now = datetime.datetime.now().isoformat()

    status_cols = {
        "accepted": "Accepted_at",
        "arrived": "Arrived_at",
        "started": "Started_at",
        "completed": "Completed_at",
        "cancelled": "Cancelled_at",
    }

    col = status_cols.get(status)
    if col:
        query = f'UPDATE "Trips" SET "Status" = ?, "{col}" = ? WHERE "Trip_id" = ?'
        sqlite_execute(query, (status, now, trip_id))
    else:
        sqlite_execute(
            'UPDATE "Trips" SET "Status" = ? WHERE "Trip_id" = ?', (status, trip_id)
        )

    if driver_id and status == "accepted":
        sqlite_execute(
            "UPDATE \"Drivers\" SET \"Status\" = 'on_trip' WHERE \"Driver_id\" = ?", (driver_id,)
        )
    elif driver_id and status in ["completed", "cancelled"]:
        sqlite_execute(
            "UPDATE \"Drivers\" SET \"Status\" = 'available' WHERE \"Driver_id\" = ?", (driver_id,)
        )


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

    sqlite_execute(
        """
        INSERT INTO "Trips" (
            "Trip_id",
           	"Rider_id",
           	"Driver_id",
           	"Pickup_lat",
           	"Pickup_lng",
           	"Drop_lat",
           	"Drop_lng",
           	"Distance",
           	"Fare",
           	"Status",
           	"Requested_at",
           	"Accepted_at",
           	"Started_at",
           	"Completed_at",
           	"Cancelled_at"
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
    result = sqlite_fetchone(
        """
        SELECT "Status" FROM "Trips" WHERE "Trip_id" = ?
    """,
        (trip_id,),
    )
    return result["Status"] if result else None


async def simulate_driver_to_pickup(trip_id):
    trip = sqlite_fetchone(
        """
        SELECT t."Pickup_lat", t."Pickup_lng", d."Lat", d."Lng", d."Driver_id"
        FROM "Trips" t
        JOIN "Drivers" d ON t."Driver_id" = d."Driver_id"
        WHERE t."Trip_id" = ?
        """,
        (trip_id,),
    )

    if not trip:
        return

    pickup_lat, pickup_lng, driver_lat, driver_lng, driver_id = trip["Pickup_lat"], trip["Pickup_lng"], trip["Lat"], trip["Lng"], trip["Driver_id"]

    route = generate_route(driver_lat, driver_lng, pickup_lat, pickup_lng)

    await simulate_driver(trip_id, route, total_time=10)
    update_trip_status(trip_id, "arrived")

    await asyncio.sleep(3)
    update_trip_status(trip_id, "started")

    await start_trip(trip_id)


async def start_trip(trip_id):
    trip = sqlite_fetchone(
        "SELECT \"Pickup_lat\", \"Pickup_lng\", \"Drop_lat\", \"Drop_lng\" FROM \"Trips\" WHERE \"Trip_id\" = ?",
        (trip_id,),
    )

    if not trip:
        return {"error": "Trip not found"}

    pickup_lat, pickup_lng, drop_lat, drop_lng = trip["Pickup_lat"], trip["Pickup_lng"], trip["Drop_lat"], trip["Drop_lng"]

    route = generate_route(pickup_lat, pickup_lng, drop_lat, drop_lng)

    TRIP_DURATION = 80

    asyncio.create_task(simulate_driver(trip_id, route, total_time=TRIP_DURATION))

    async def finish_trip():
        await asyncio.sleep(TRIP_DURATION + 2)
        update_trip_status(trip_id, "completed")

    asyncio.create_task(finish_trip())
