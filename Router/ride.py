import asyncio
import datetime
import traceback

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from db.db import sqlite_execute, sqlite_fetchone, sqlite_query
from schema import (
    DriverLocation,
    DriverStatus,
    FareRequest,
    FareResponse,
    RideAccept,
    RideArrived,
    RideCancel,
    RideRequest,
    RideResponse,
)
from Services.Matching import CalculateEta, haversineDist, match_driver
from Services.Pricing import calculate_surge
from Services.Fares import basefare
from Services.Trips import (
    create_trip,
    get_trip_status,
    simulate_driver_to_pickup,
    start_trip,
    update_trip_status,
)
from Services.WebSocketManager import manager

router = APIRouter()


@router.put("/driver/status")
def update_driver_status(data: DriverStatus):
    # status: online -> available, offline -> offline
    status = "available" if data.status == "online" else "offline"
    sqlite_execute(
        """UPDATE "Drivers" SET Status = ? WHERE "Driver_id" = ?""",
        (status, data.driver_id),
    )
    return {"status": data.status, "message": f"Driver is now {data.status}"}


@router.put("/driver/location")
def update_driver_location(data: DriverLocation):
    sqlite_execute(
        """UPDATE "Drivers" SET "Lat" = ?, "Lng" = ? WHERE "Driver_id" = ?""",
        (data.lat, data.lng, data.driver_id),
    )
    return {"acknowledged": True}


@router.get("/ride/{trip_id}/status")
def ride_status(trip_id: str):
    status = get_trip_status(trip_id)
    if not status:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"trip_id": trip_id, "status": status}


@router.post("/ride/fare", response_model=FareResponse)
def calculate_ride_fare(data: FareRequest):
    # Base fare for auto
    distance = haversineDist(data.pickup_lat, data.pickup_lng, data.drop_lat, data.drop_lng, 2)
    fare = basefare(distance)
    eta = int(CalculateEta(distance))
    return FareResponse(base_fare=fare, distance=distance, eta=eta)


@router.get("/driver/{driver_id}/current_trip")
def driver_current_trip(driver_id: str):
    trip = sqlite_fetchone(
        """SELECT * FROM "Trips" WHERE "Driver_id" = ? AND "Status" IN ('requested', 'accepted', 'arrived', 'started')""",
        (driver_id,),
    )
    if not trip:
        return {"trip": None}
    return {"trip": dict(trip)}


@router.post("/ride/request", response_model=RideResponse)
async def ride_request(data: RideRequest):
    try:
        req_time = datetime.datetime.now()
        try:
            surge_multiplier = calculate_surge(data.pickup_lat, data.pickup_lng)
        except:
            surge_multiplier = 1.0

        backend_vehicle_type = data.vehicle_type
        mapping = {
            "economy": "Car",
            "comfort": "Car",
            "luxury": "SUV",
            "bike": "Bike",
        }
        if data.vehicle_type.lower() in mapping:
            backend_vehicle_type = mapping[data.vehicle_type.lower()]

        driver, eta, distance = match_driver(
            data.pickup_lat, data.pickup_lng, backend_vehicle_type
        )

        if not driver:
            raise HTTPException(status_code=404, detail="No driver available")

        # Generate actual route for the trip itself (pickup to dropoff)
        from Services.RouteService import generate_route

        trip_route = generate_route(
            data.pickup_lat, data.pickup_lng, data.drop_lat, data.drop_lng
        )

        trip_id = create_trip(
            Rider_id=data.rider_id,
            Driver_id=driver["Driver_id"],
            Pickup_lat=data.pickup_lat,
            Pickup_lng=data.pickup_lng,
            Drop_lat=data.drop_lat,
            Drop_lng=data.drop_lng,
            Distance=distance,
            surge=surge_multiplier,
            Status="requested",
            Requested_at=req_time.isoformat(),
            Accepted_at=None,
            Started_at=None,
            Completed_at=None,
            Cancelled_at=None,
        )

        # Automate acceptance for demo
        update_trip_status(trip_id, "accepted", driver["Driver_id"])
        asyncio.create_task(simulate_driver_to_pickup(trip_id))

        return RideResponse(
            trip_id=trip_id,
            status="matched",
            driver_id=driver["Driver_id"],
            driver_name=driver["Name"],
            rating=driver["Rating"],
            trips=int(driver["Acceptance_Rate"] * 1000),  # Mock trips
            vehicle_model=driver["Veh_Model"],
            vehicle_color=driver["Veh_Colour"],
            vehicle_plate=driver["Veh_Num"],
            eta=eta,
            surge_multiplier=surge_multiplier,
            route=trip_route,
        )
    except Exception as e:
        traceback.print_exc()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ride/accept")
async def ride_accept_driver(data: RideAccept):
    update_trip_status(data.trip_id, "accepted", data.driver_id)
    asyncio.create_task(simulate_driver_to_pickup(data.trip_id))
    return {"status": "accepted", "trip_id": data.trip_id}


@router.post("/ride/arrived")
def ride_arrived_endpoint(data: RideArrived):
    update_trip_status(data.trip_id, "arrived")
    return {"status": "arrived", "trip_id": data.trip_id}


@router.post("/ride/start/{trip_id}")
async def ride_start(trip_id: str):
    update_trip_status(trip_id, "started")
    await start_trip(trip_id)
    return {"status": "started", "trip_id": trip_id}


@router.post("/ride/complete/{trip_id}")
def ride_completed(trip_id: str):
    trip = sqlite_fetchone(
        'SELECT "Driver_id" FROM "Trips" WHERE "Trip_id" = ?', (trip_id,)
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    driver_id = trip["Driver_id"]
    update_trip_status(trip_id, "completed", driver_id)
    return {"status": "completed", "trip_id": trip_id}


@router.post("/ride/cancel")
def ride_cancel(data: RideCancel):
    trip = sqlite_fetchone(
        'SELECT "Driver_id", "Status" FROM "Trips" WHERE "Trip_id" = ?', (data.trip_id,)
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    driver_id = trip["Driver_id"]
    update_trip_status(data.trip_id, "cancelled", driver_id)
    return {"status": "cancelled"}


@router.websocket("/ws/trip/{trip_id}")
async def trip_socket(websocket: WebSocket, trip_id: str):
    await manager.connect(trip_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.send_location(trip_id, data)
    except WebSocketDisconnect:
        manager.disconnect(trip_id, websocket)
