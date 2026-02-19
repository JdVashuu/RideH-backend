from db.db import conn, cursor


def create_trip(rider_id, driver_id, pickup_lat, pickup_lng, drop_lat, drop_lng, surge):
    # cursor.execute("""
    #     INSERT INTO Trips(
    #         Rider_id, Driver_id, Pickup_lat, Pickup_lng, Drop_lat, Drop_lng, Surge
    #     ) VALUES
    #     """
    # )
    return "T001"


#Trip_id, Rider_id, Driver_id, Pickup_lat, Pickup_lng, Drop_lat, Drop_lng, Distance, Fare, Status, Requested_at, Accepted_at, Started_at, Completed_at, Cancelled_at