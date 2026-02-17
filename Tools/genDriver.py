import datetime
import random
import sqlite3
import uuid

import osmnx as ox
from faker import Faker

city = "Bengaluru, India"
print("Loading city : ", city)

G = ox.graph_from_place(city, network_type="drive")
print("Loading complete!")
# fig, ax = ox.plot_graph(G)

fake = Faker("en_IN")


def random_point_on_road(Graph=G):
    u, v, key = random.choice(list(G.edges(keys=True)))

    data = G.edges[u, v, key]

    if "geometry" in data:
        geom = data["geometry"]
        point = geom.interpolate(random.random(), normalized=True)
        return point.y, point.x  # lat, lng
    else:
        lat = (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2
        lng = (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2
        return lat, lng


def generate_plate():
    return f"KA-{random.randint(1, 99):02}-{fake.random_uppercase_letter()}{fake.random_uppercase_letter()}-{random.randint(1000, 9999)}"


def generate_driver():
    vehicle_types = ["SUV", "Bike", "Car", "Auto"]
    vehicle_ratios = [0.15, 0.05, 0.5, 0.3]
    vehicle_colours = ["Black", "White", "Red", "Silver", "Grey", "Blue"]
    car_models = [
        "Maruti WagonR",
        "Maruti Suzuki Alto",
        "Maruti Swift",
        "Maruti Baleno",
        "Hyundai Grand i10",
        "Hyundai i20",
        "Hyundai Verna",
        "Tata Nexon",
    ]
    suv_models = [
        "Hyundai Creta",
        "Mahindra Bolera",
        "Mahindra XUV700",
        "Mahindra Scorpio",
        "Mahindra Thar",
    ]
    bike_models = [
        "Hero Splender",
        "Honda Activa",
        "TVS Jupiter",
        "Suzuki Access125",
        "Bajaj Pulsor",
    ]
    auto_models = ["Bajaj RE", "Piaggio Ape"]

    vt = random.choices(vehicle_types, weights=vehicle_ratios, k=1)[0]
    if vt == "Car":
        model = random.choice(car_models)
    elif vt == "SUV":
        model = random.choice(suv_models)
    elif vt == "Bike":
        model = random.choice(bike_models)
    else:
        model = random.choice(auto_models)

    lat, lng = random_point_on_road()

    return {
        "Driver_id": str(uuid.uuid4()),
        "Name": fake.name(),
        "Ph_no": fake.phone_number(),
        "Veh_Type": vt,
        "Veh_Model": model,
        "Veh_Num": generate_plate(),
        "Veh_Colour": random.choice(vehicle_colours),
        "Status": "available",
        "Lat": lat,
        "Lng": lng,
        "Rating": 5,
        "Acceptance_Rate": 1,
        "Cancel_Rate": 0,
        "Created_at": datetime.datetime.now().isoformat(),
        "Updated_at": datetime.datetime.now().isoformat(),
    }


# for _ in range(10):
#     print(generate_driver())
#     print()


conn = sqlite3.connect("./db/ride_hailing.db")
curr = conn.cursor()


def save_driver_inDb(Driver):
    curr.execute(
        """
        INSERT INTO Drivers (
                    Driver_id, Name, Ph_no, Veh_Type, Veh_Model, Veh_Num,
                    Veh_Colour, Status, Lat, Lng, Rating, Acceptance_Rate,
                    Cancel_Rate, Created_at, Updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            Driver["Driver_id"],
            Driver["Name"],
            Driver["Ph_no"],
            Driver["Veh_Type"],
            Driver["Veh_Model"],
            Driver["Veh_Num"],
            Driver["Veh_Colour"],
            Driver["Status"],
            Driver["Lat"],
            Driver["Lng"],
            Driver["Rating"],
            Driver["Acceptance_Rate"],
            Driver["Cancel_Rate"],
            Driver["Created_at"],
            Driver["Updated_at"],
        ),
    )

    conn.commit()


for _ in range(499):
    d = generate_driver()
    save_driver_inDb(d)
    print(f"Inserted {d['Name']}")

conn.close()
