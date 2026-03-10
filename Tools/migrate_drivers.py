import os
import sqlite3

import psycopg2
from dotenv import load_dotenv

# Load environment variables (Make sure your .env has DATABASE_URL)
load_dotenv()

SQLITE_DB_PATH = "db/ride_hailing.db"
POSTGRES_URL = os.getenv("DATABASE_URL")


def migrate_drivers():
    if not POSTGRES_URL:
        print("Error: DATABASE_URL not found in .env file")
        return

    print("Connecting to databases...")
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to Postgres
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cursor = pg_conn.cursor()

    print("Fetching drivers from SQLite...")
    sqlite_cursor.execute("SELECT * FROM Drivers")
    drivers = sqlite_cursor.fetchall()

    if not drivers:
        print("No drivers found in SQLite database.")
        return

    print(f"Found {len(drivers)} drivers. Migrating to Postgres...")

    # Prepare the INSERT query
    # Note: We use double quotes for table/column names to match the schema provided earlier
    insert_query = """
    INSERT INTO "Drivers" (
        "Driver_id", "Name", "Ph_no", "Veh_Type", "Veh_Model",
        "Veh_Num", "Veh_Colour", "Status", "Lat", "Lng",
        "Rating", "Acceptance_Rate", "Cancel_Rate", "geohash"
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT ("Driver_id") DO UPDATE SET
        "Name" = EXCLUDED."Name",
        "Status" = EXCLUDED."Status",
        "Lat" = EXCLUDED."Lat",
        "Lng" = EXCLUDED."Lng";
    """

    count = 0
    for driver in drivers:
        try:
            pg_cursor.execute(
                insert_query,
                (
                    driver["Driver_id"],
                    driver["Name"],
                    driver["Ph_no"],
                    driver["Veh_Type"],
                    driver["Veh_Model"],
                    driver["Veh_Num"],
                    driver["Veh_Colour"],
                    driver["Status"] or "offline",  # Default to offline if null
                    driver["Lat"],
                    driver["Lng"],
                    driver["Rating"],
                    driver["Acceptance_Rate"],
                    driver["Cancel_Rate"],
                    driver["geohash"],
                ),
            )
            count += 1
        except Exception as e:
            print(f"Error migrating driver {driver['Driver_id']}: {e}")
            pg_conn.rollback()
            continue

    pg_conn.commit()
    print(f"Successfully migrated {count} drivers to Supabase!")

    # Close connections
    sqlite_conn.close()
    pg_conn.close()


if __name__ == "__main__":
    migrate_drivers()
