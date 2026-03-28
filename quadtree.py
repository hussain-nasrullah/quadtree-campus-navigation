"""
QuadTree ADT — implemented with plain dicts and tuples (no classes).

A quadtree node is a dict:
{
    "boundary": (cx, cy, half_w, half_h),   # center + half-dimensions
    "capacity": int,
    "points":   [ point, ... ],              # list of points stored here
    "divided":  bool,
    "nw": node | None,
    "ne": node | None,
    "sw": node | None,
    "se": node | None,
}

A point is a dict:
{
    "id":       str,
    "x":        float,      # longitude
    "y":        float,      # latitude
    "name":     str,
    "category": str,
    "data":     dict,       # any extra key-value pairs
}
"""

# ── helpers ──────────────────────────────────────────────────────────

def make_boundary(cx, cy, half_w, half_h):
    return (cx, cy, half_w, half_h)


def make_point(id, x, y, name, category, data=None):
    return {
        "id": id,
        "x": x,
        "y": y,
        "name": name,
        "category": category,
        "data": data or {},
    }


def contains(boundary, point):
    """Return True if *point* lies inside *boundary*."""
    cx, cy, hw, hh = boundary
    return (cx - hw <= point["x"] <= cx + hw and
            cy - hh <= point["y"] <= cy + hh)


def intersects(boundary, range_boundary):
    """Return True if two boundaries overlap."""
    cx1, cy1, hw1, hh1 = boundary
    cx2, cy2, hw2, hh2 = range_boundary
    return not (cx1 - hw1 > cx2 + hw2 or
                cx1 + hw1 < cx2 - hw2 or
                cy1 - hh1 > cy2 + hh2 or
                cy1 + hh1 < cy2 - hh2)


# ── core quadtree operations ────────────────────────────────────────

def create_quadtree(boundary, capacity=1):
    """Create and return a new quadtree node."""
    return {
        "boundary": boundary,
        "capacity": capacity,
        "points": [],
        "divided": False,
        "nw": None,
        "ne": None,
        "sw": None,
        "se": None,
    }


def _subdivide(qt):
    """Split *qt* into four children."""
    cx, cy, hw, hh = qt["boundary"]
    cap = qt["capacity"]
    qhw, qhh = hw / 2, hh / 2

    qt["nw"] = create_quadtree(make_boundary(cx - qhw, cy + qhh, qhw, qhh), cap)
    qt["ne"] = create_quadtree(make_boundary(cx + qhw, cy + qhh, qhw, qhh), cap)
    qt["sw"] = create_quadtree(make_boundary(cx - qhw, cy - qhh, qhw, qhh), cap)
    qt["se"] = create_quadtree(make_boundary(cx + qhw, cy - qhh, qhw, qhh), cap)
    qt["divided"] = True


def insert(qt, point):
    """Insert a point into the quadtree.  Returns True on success."""
    if not contains(qt["boundary"], point):
        return False

    if len(qt["points"]) < qt["capacity"] and not qt["divided"]:
        qt["points"].append(point)
        return True

    if not qt["divided"]:
        _subdivide(qt)
        # redistribute existing points into children
        existing = qt["points"]
        qt["points"] = []
        for p in existing:
            _insert_into_children(qt, p)

    return _insert_into_children(qt, point)


def _insert_into_children(qt, point):
    for child in ("nw", "ne", "sw", "se"):
        if insert(qt[child], point):
            return True
    return False


def query_range(qt, range_boundary):
    """Return all points within *range_boundary*."""
    found = []
    if not intersects(qt["boundary"], range_boundary):
        return found

    for p in qt["points"]:
        if contains(range_boundary, p):
            found.append(p)

    if qt["divided"]:
        for child in ("nw", "ne", "sw", "se"):
            found.extend(query_range(qt[child], range_boundary))

    return found


def query_all(qt):
    """Return every point stored in the quadtree."""
    points = list(qt["points"])
    if qt["divided"]:
        for child in ("nw", "ne", "sw", "se"):
            points.extend(query_all(qt[child]))
    return points


def find_by_id(qt, point_id):
    """Find and return a single point by its id, or None."""
    for p in qt["points"]:
        if p["id"] == point_id:
            return p
    if qt["divided"]:
        for child in ("nw", "ne", "sw", "se"):
            result = find_by_id(qt[child], point_id)
            if result is not None:
                return result
    return None


def remove(qt, point_id):
    """Remove a point by id.  Returns the removed point or None."""
    for i, p in enumerate(qt["points"]):
        if p["id"] == point_id:
            return qt["points"].pop(i)

    if qt["divided"]:
        for child in ("nw", "ne", "sw", "se"):
            result = remove(qt[child], point_id)
            if result is not None:
                return result
    return None


def update(qt, point_id, **kwargs):
    """Update fields of a point in-place.  Returns True if found."""
    point = find_by_id(qt, point_id)
    if point is None:
        return False

    # if coordinates changed, remove & re-insert
    if "x" in kwargs or "y" in kwargs:
        old = remove(qt, point_id)
        old.update(kwargs)
        return insert(qt, old)

    for k, v in kwargs.items():
        if k in point:
            point[k] = v
        else:
            point["data"][k] = v
    return True


def search_by_name(qt, query):
    """Return all points whose name contains *query* (case-insensitive)."""
    query_lower = query.lower()
    return [p for p in query_all(qt) if query_lower in p["name"].lower()]


def search_by_category(qt, category):
    """Return all points matching *category* (case-insensitive)."""
    cat_lower = category.lower()
    return [p for p in query_all(qt) if p["category"].lower() == cat_lower]


def nearest_neighbor(qt, x, y):
    """Brute-force nearest neighbor from all points."""
    all_pts = query_all(qt)
    if not all_pts:
        return None
    return min(all_pts, key=lambda p: (p["x"] - x) ** 2 + (p["y"] - y) ** 2)


def count(qt):
    """Return total number of points in the quadtree."""
    n = len(qt["points"])
    if qt["divided"]:
        for child in ("nw", "ne", "sw", "se"):
            n += count(qt[child])
    return n


def depth(qt):
    """Return the maximum depth of the quadtree."""
    if not qt["divided"]:
        return 0
    return 1 + max(depth(qt[child]) for child in ("nw", "ne", "sw", "se"))
