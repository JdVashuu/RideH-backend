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
    driver_name: str
    rating: float
    trips: int
    vehicle_model: str
    vehicle_color: str
    vehicle_plate: str
    eta: int
    surge_multiplier: float
    route: list[list[float]] | None = None


class RideAccept(BaseModel):
    driver_id: str
    trip_id: str


class RideArrived(BaseModel):
    driver_id: str
    trip_id: str


class RideCancel(BaseModel):
    driver_id: str
    trip_id: str


class FareRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float


class FareResponse(BaseModel):
    base_fare: float
    distance: float
    eta: int


class FareCreate(BaseModel):
    distance: float
    duration: float
    surge_multiplier: float
    currency: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str


class TokenData(BaseModel):
    user_id: str | None = None


class DriverStatus(BaseModel):
    driver_id: str
    status: str
    lat: float | None = None
    lng: float | None = None


class DriverLocation(BaseModel):
    driver_id: str
    lat: float
    lng: float
    heading: float | None = None
    speed: float | None = None


class RiderRegister(BaseModel):
    name: str
    ph_no: str
    email: str
    password: str


class RiderLogin(BaseModel):
    email: str
    password: str
