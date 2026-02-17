from pydantic import BaseModel


class RideRequest(BaseModel):
    rider_id: str
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    vehicle_type: float


class RideResponse(BaseModel):
    trip_id: str
    status: str
    driver_id: str
    eta: str
    surge_multiplier: float
