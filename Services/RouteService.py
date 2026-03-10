import networkx as nx
import osmnx as ox

from Tools.graph_loader import get_graph


def generate_route(pickup_lat, pickup_lng, drop_lat, drop_lng):
    G = get_graph()

    origin = ox.distance.nearest_nodes(G, pickup_lng, pickup_lat)
    destination = ox.distance.nearest_nodes(G, drop_lng, drop_lat)

    route = nx.shortest_path(G, origin, destination, weight="length")

    coords = [(G.nodes[node]["y"], G.nodes[node]["x"]) for node in route]

    return coords
