"""
Persistence layer -- save / load a quadtree + its map config to a JSON file.

File format:
{
    "map": {
        "name": str,
        "boundary": [cx, cy, hw, hh],
        "image": str | null,
        "extent": [lon_min, lon_max, lat_min, lat_max] | null
    },
    "points": [ point_dict, ... ]
}
"""

import json
import os

from quadtree import create_quadtree, insert, make_boundary, query_all

DEFAULT_FILE = "mapdata.json"


def save(qt, map_config, filepath=DEFAULT_FILE):
    """Persist the quadtree and map config to a JSON file."""
    data = {
        "map": {
            "name": map_config["name"],
            "boundary": list(qt["boundary"]),
            "image": map_config.get("image"),
            "extent": map_config.get("extent"),
        },
        "points": query_all(qt),
    }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def load(filepath=DEFAULT_FILE):
    """Load quadtree and map config from a JSON file.

    Returns (qt, map_config) or (None, None) if file doesn't exist.
    """
    if not os.path.exists(filepath):
        return None, None

    with open(filepath) as f:
        data = json.load(f)

    boundary = make_boundary(*data["map"]["boundary"])
    qt = create_quadtree(boundary)
    for p in data["points"]:
        insert(qt, p)

    map_config = {
        "name": data["map"]["name"],
        "image": data["map"].get("image"),
        "extent": data["map"].get("extent"),
    }
    return qt, map_config
