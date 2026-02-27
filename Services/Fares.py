import datetime
import uuid

from db.db import cursor
from schema import FareCreate


def basefare(distance):
    # 50 ruppe per km
    return distance * 50


def create_fare(fare: FareCreate):
    fare_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO Fares (
            Fare_id,
            Base_fare,
            Distance,
            Duration,
            Surge_multiplier,
            Currency,
            Created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            fare_id,
            basefare(fare.distance),
            fare.distance,
            fare.duration,
            fare.surge_multiplier,
            fare.currency,
            datetime.datetime.now(),
        ),
    )

    return fare_id
