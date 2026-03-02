import osmnx as ox

G = ox.load_graphml("bengaluru.graphml")


def get_graph():
    return G
