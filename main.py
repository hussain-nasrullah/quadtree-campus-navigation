#!/usr/bin/env python3
"""
QuadTree Map -- CLI application.

Reads all map data (points, boundary, image) from mapdata.json.
"""

import sys
import uuid

from quadtree import (
    create_quadtree, insert, remove, update, query_all, query_range,
    find_by_id, search_by_name, search_by_category, nearest_neighbor,
    count, depth, make_boundary, make_point,
)
from storage import save, load
from visualize import show_map, show_points_on_map

# -- globals --

QT = None           # the active quadtree
MAP_CONFIG = None   # {"name", "image", "extent"}
DATA_FILE = "mapdata.json"

# -- display helpers --

def print_point(p, idx=None):
    prefix = f"  [{idx}] " if idx is not None else "  "
    print(f"{prefix}{p['name']}")
    print(f"       id: {p['id']}  |  category: {p['category']}")
    print(f"       lon: {p['x']}  lat: {p['y']}")
    if p["data"]:
        print(f"       extra: {p['data']}")


def print_points(points):
    if not points:
        print("  (no results)")
        return
    for i, p in enumerate(points, 1):
        print_point(p, i)


def prompt(msg, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return val if val else default


def ask_visualize():
    ans = prompt("  Show on map? (y/n)", "n")
    return ans.lower() in ("y", "yes")

# -- init / load --

def load_from_file():
    global QT, MAP_CONFIG
    qt, config = load(DATA_FILE)
    if qt is None:
        print(f"  ERROR: {DATA_FILE} not found. Place a valid mapdata.json in the project directory.")
        sys.exit(1)
    QT = qt
    MAP_CONFIG = config
    print(f"Loaded '{config['name']}' from {DATA_FILE} ({count(QT)} locations).")

# -- CLI commands --

def cmd_add():
    pid = prompt("  Point id (leave blank for auto)", None)
    if not pid:
        pid = uuid.uuid4().hex[:8]
    name = prompt("  Name")
    x = float(prompt("  Longitude (x)"))
    y = float(prompt("  Latitude  (y)"))
    cat = prompt("  Category", "General")
    p = make_point(pid, x, y, name, cat)
    if insert(QT, p):
        save(QT, MAP_CONFIG, DATA_FILE)
        print(f"  Added '{name}' (id={pid}).")
        if ask_visualize():
            show_points_on_map(QT, MAP_CONFIG, [p], title=f"Added: {name}")
    else:
        print("  ERROR: point is outside map boundary.")


def cmd_remove():
    pid = prompt("  Point id to remove")
    result = remove(QT, pid)
    if result:
        save(QT, MAP_CONFIG, DATA_FILE)
        print(f"  Removed '{result['name']}'.")
        if ask_visualize():
            show_map(QT, MAP_CONFIG, title=f"After removing: {result['name']}")
    else:
        print(f"  Not found: {pid}")


def cmd_update():
    pid = prompt("  Point id to update")
    p = find_by_id(QT, pid)
    if p is None:
        print(f"  Not found: {pid}")
        return
    print("  Current values:")
    print_point(p)
    print("  Enter new values (leave blank to keep current):")

    new_name = prompt("    Name", p["name"])
    new_cat  = prompt("    Category", p["category"])
    new_x    = prompt("    Longitude (x)", str(p["x"]))
    new_y    = prompt("    Latitude  (y)", str(p["y"]))

    update(QT, pid, name=new_name, category=new_cat,
           x=float(new_x), y=float(new_y))
    save(QT, MAP_CONFIG, DATA_FILE)
    print("  Updated.")
    if ask_visualize():
        updated = find_by_id(QT, pid)
        show_points_on_map(QT, MAP_CONFIG, [updated], title=f"Updated: {new_name}")


def cmd_list():
    points = query_all(QT)
    print(f"\n  All locations in '{MAP_CONFIG['name']}' ({len(points)} total):\n")
    print_points(points)
    if ask_visualize():
        show_map(QT, MAP_CONFIG)


def cmd_search():
    q = prompt("  Search name")
    results = search_by_name(QT, q)
    print_points(results)
    if results and ask_visualize():
        show_points_on_map(QT, MAP_CONFIG, results,
                           title=f"Search: '{q}' ({len(results)} results)")


def cmd_category():
    cat = prompt("  Category")
    results = search_by_category(QT, cat)
    print_points(results)
    if results and ask_visualize():
        show_points_on_map(QT, MAP_CONFIG, results,
                           title=f"Category: {cat} ({len(results)} results)")


def cmd_range():
    print("  Define search rectangle (center + half-dimensions):")
    cx = float(prompt("    Center longitude"))
    cy = float(prompt("    Center latitude"))
    hw = float(prompt("    Half-width"))
    hh = float(prompt("    Half-height"))
    rb = make_boundary(cx, cy, hw, hh)
    results = query_range(QT, rb)
    print_points(results)
    if results and ask_visualize():
        show_points_on_map(QT, MAP_CONFIG, results,
                           title=f"Range query ({len(results)} results)")


def cmd_nearest():
    x = float(prompt("  Your longitude"))
    y = float(prompt("  Your latitude"))
    p = nearest_neighbor(QT, x, y)
    if p:
        print("  Nearest location:")
        print_point(p)
        if ask_visualize():
            show_points_on_map(QT, MAP_CONFIG, [p],
                               title=f"Nearest to ({x}, {y}): {p['name']}")
    else:
        print("  Map is empty.")


def cmd_info():
    print(f"  Map:        {MAP_CONFIG['name']}")
    cx, cy, hw, hh = QT["boundary"]
    print(f"  Boundary:   center=({cx}, {cy})  half=({hw}, {hh})")
    print(f"  Locations:  {count(QT)}")
    print(f"  Tree depth: {depth(QT)}")


def cmd_find():
    pid = prompt("  Point id")
    p = find_by_id(QT, pid)
    if p:
        print_point(p)
        if ask_visualize():
            show_points_on_map(QT, MAP_CONFIG, [p], title=f"Found: {p['name']}")
    else:
        print(f"  Not found: {pid}")


def cmd_categories():
    all_pts = query_all(QT)
    cats = {}
    for p in all_pts:
        cats[p["category"]] = cats.get(p["category"], 0) + 1
    print(f"\n  Categories in '{MAP_CONFIG['name']}':\n")
    for cat, n in sorted(cats.items()):
        print(f"    {cat:20s}  ({n})")


def cmd_visualize():
    grid = prompt("  Show quadtree grid? (y/n)", "n")
    show_grid = grid.lower() in ("y", "yes")
    show_map(QT, MAP_CONFIG, show_grid=show_grid)


def cmd_quadtree():
    show_map(QT, MAP_CONFIG, show_grid=True,
             title=f"{MAP_CONFIG['name']} -- QuadTree Structure (depth={depth(QT)})")


COMMANDS = {
    "add":        ("Add a new location",                cmd_add),
    "remove":     ("Remove a location by id",           cmd_remove),
    "update":     ("Update a location by id",           cmd_update),
    "find":       ("Find a location by id",             cmd_find),
    "list":       ("List all locations",                cmd_list),
    "search":     ("Search locations by name",          cmd_search),
    "category":   ("Filter by category",                cmd_category),
    "categories": ("Show all categories",               cmd_categories),
    "range":      ("Range query (rectangle)",           cmd_range),
    "nearest":    ("Find nearest location to a point",  cmd_nearest),
    "info":       ("Map & tree statistics",             cmd_info),
    "visualize":  ("Show all locations on satellite map",cmd_visualize),
    "quadtree":   ("Visualize quadtree grid on map",    cmd_quadtree),
    "help":       ("Show this help",                    None),
    "quit":       ("Exit",                              None),
}


def print_help():
    print("\n  Available commands:\n")
    for cmd, (desc, _) in COMMANDS.items():
        print(f"    {cmd:12s}  {desc}")
    print()

# -- main loop --

def main():
    print("=" * 55)
    print("  QuadTree Map")
    print("=" * 55)

    load_from_file()
    print_help()

    while True:
        try:
            raw = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not raw:
            continue
        if raw in ("quit", "exit", "q"):
            print("Bye!")
            break
        if raw == "help":
            print_help()
            continue
        if raw in COMMANDS:
            _, fn = COMMANDS[raw]
            if fn:
                fn()
        else:
            print(f"  Unknown command: {raw}  (type 'help')")


if __name__ == "__main__":
    main()
