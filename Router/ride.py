import datetime

from fastapi import APIRouter, HTTPException

from db.db import sqlite_execute, sqlite_query
from schema import RideAccept, RideArrived, RideCancel, RideRequest, RideResponse
from Services.Matching import match_driver
from Services.Pricing import calculate_surge
from Services.Trips import create_trip

router = APIRouter()


@router.post("/ride/request", response_model=RideResponse)
def ride_request(data: RideRequest):
    req_time = datetime.datetime.now()
    surge_multiplier = calculate_surge(data.pickup_lat, data.pickup_lng)

    driver, eta, distance = match_driver(
        data.pickup_lat, data.pickup_lng, data.vehicle_type
    )

    if not driver:
        raise HTTPException(status_code=404, detail="No driver available")

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
        Requested_at=req_time,
        Accepted_at="",
        Started_at="",
        Completed_at="",
        Cancelled_at="",
    )

    return RideResponse(
        trip_id=trip_id,
        status="matched",
        driver_id=driver["Driver_id"],
        eta=eta,
        surge_multiplier=surge_multiplier,
    )


@router.post("/ride/accept")
def ride_accept_driver(data: RideAccept):
    accepted_time = datetime.datetime.now()

    # Verify trip exists
    trip = sqlite_query("SELECT Status FROM Trips WHERE Trip_id = ?", (data.trip_id,))
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    sqlite_execute(
        "UPDATE Drivers SET Status = 'on_trip' WHERE Driver_id = ?", (data.driver_id,)
    )
    sqlite_execute(
        "UPDATE Trips SET Status = 'accepted', Accepted_at = ? WHERE Trip_id = ?",
        (accepted_time.isoformat(), data.trip_id),
    )

    return {"status": "accepted", "time": accepted_time, "trip_id": data.trip_id}


@router.post("/ride/arrived")
def ride_arrived(data: RideArrived):
    arrival_time = datetime.datetime.now()

    sqlite_execute(
        "UPDATE Trips SET Status = 'arrived', Arrived_at = ? WHERE Trip_id = ?",
        (arrival_time.isoformat(), data.trip_id),
    )
    return {"status": "arrived", "time": arrival_time, "trip_id": data.trip_id}


@router.post("/ride/start/{trip_id}")
def ride_start(trip_id: str):
    start_time = datetime.datetime.now()

    sqlite_execute(
        "UPDATE Trips SET Status = 'started', Started_at = ? WHERE Trip_id = ?",
        (start_time.isoformat(), trip_id),
    )
    return {"status": "started", "time": start_time, "trip_id": trip_id}


@router.post("/ride/complete/{trip_id}")
def ride_completed(trip_id: str):
    completion_time = datetime.datetime.now()

    trip = sqlite_query("SELECT Driver_id FROM Trips WHERE Trip_id = ?", (trip_id,))
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    driver_id = trip[0]["Driver_id"]

    sqlite_execute(
        "UPDATE Trips SET Status = 'completed', Completed_at = ? WHERE Trip_id = ?",
        (completion_time.isoformat(), trip_id),
    )

    sqlite_execute(
        "UPDATE Drivers SET Status = 'available' WHERE Driver_id = ?", (driver_id,)
    )

    return {
        "status": "completed",
        "time": completion_time,
        "trip_id": trip_id,
    }


@router.post("/ride/cancel")
def ride_cancel(data: RideCancel):
    cancel_time = datetime.datetime.now()

    trip = sqlite_query(
        "SELECT Driver_id, Status FROM Trips WHERE Trip_id = ?", (data.trip_id,)
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    driver_id = trip[0]["Driver_id"]
    current_status = trip[0]["Status"]

    if current_status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a ride that is already {current_status}",
        )

    sqlite_execute(
        "UPDATE Trips SET Status = 'cancelled', Cancelled_at = ? WHERE Trip_id = ?",
        (cancel_time.isoformat(), data.trip_id),
    )

    sqlite_execute(
        "UPDATE Drivers SET Status = 'available' WHERE Driver_id = ?", (driver_id,)
    )

    return {"status": "cancelled", "time": cancel_time}
