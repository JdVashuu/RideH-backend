from fastapi import FastAPI

from Router import ride

app = FastAPI()
app.include_router(ride.router)
