from pydantic import BaseModel


class RideRequest(BaseModel):
    rider_id: str
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    vehicle_type: str


class RideResponse(BaseModel):
    trip_id: str
    status: str
    driver_id: str
    eta: int
    surge_multiplier: float


class RideAccept(BaseModel):
    driver_id: str
    trip_id: str


class RideArrived(BaseModel):
    driver_id: str
    trip_id: str


class RideCancel(BaseModel):
    driver_id: str
    trip_id: str


class FareCreate(BaseModel):
    distance: float
    duration: float
    surge_multiplier: float
    currency: str


class TripCreate(BaseModel):
    rider_id: str
    driver_id: str
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    distance: float
    fare: float
