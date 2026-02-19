from fastapi import APIRouter, HTTPException

from schema import RideRequest, RideResponse
from Services.Matching import match_driver
from Services.Pricing import calculate_surge
from Services.Trips import create_trip

router = APIRouter()


@router.post("/ride/request", response_model=RideResponse)
def request_ride(data: RideRequest):
    surge_multiplier = calculate_surge(data.pickup_lat, data.pickup_lng)

    driver, eta = match_driver(data.pickup_lat, data.pickup_lng, data.vehicle_type)

    if not driver:
        raise HTTPException(status_code=404, detail="No driver available")

    trip_id = create_trip(
        rider_id=data.rider_id,
        driver_id=driver["Driver_id"],
        pickup_lat=data.pickup_lat,
        pickup_lng=data.pickup_lng,
        drop_lat=data.drop_lat,
        drop_lng=data.drop_lng,
        surge=surge_multiplier,
    )

    return RideResponse(
        trip_id=trip_id,
        status="matched",
        driver_id=driver["Driver_id"],
        eta=eta,
        surge_multiplier=surge_multiplier,
    )
