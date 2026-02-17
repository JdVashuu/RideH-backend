import os
import sqlite3

import geohash2

db_path = os.path.join(os.path.dirname(__file__), "db", "ride_hailing.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

res = cursor.execute(
    """
    SELECT Driver_id, Lat, Lng FROM Drivers
    """
)
rows = res.fetchall()

for driver_id, lat, lng in rows:
    g = geohash2.encode(lat, lng, precision=8)
    cursor.execute("UPDATE Drivers SET geohash = ? WHERE Driver_id = ?", (g, driver_id))

conn.commit()
conn.close()

print(db_path)
