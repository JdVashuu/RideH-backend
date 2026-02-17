from fastapi import FastAPI, HTTPException
from

app = FastAPI()


@app.get("/")
def root():
    return {"Hello": "World"}
