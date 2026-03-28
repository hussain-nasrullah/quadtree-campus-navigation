"""
Visualization module -- renders points and quadtree grid over a satellite image.

Loads a pre-built satellite image from the map config stored in mapdata.json.
"""

import math
import os
import sys

from PIL import Image
import matplotlib
if sys.platform == "darwin":
    try:
        matplotlib.use("macosx")
    except Exception:
        matplotlib.use("svg")
else:
    try:
        matplotlib.use("TkAgg")
    except Exception:
        matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from quadtree import query_all, count

BASE_DIR = os.path.dirname(__file__)


def _load_image(map_config):
    """Load the satellite image and extent from map config."""
    image_file = map_config.get("image")
    extent = map_config.get("extent")
    if image_file and extent:
        path = os.path.join(BASE_DIR, image_file)
        if os.path.exists(path):
            return Image.open(path), tuple(extent)
    return None, None


# -- drawing --

CATEGORY_COLORS = {
    "Academic":       "#00BFFF",
    "Gate":           "#FF4444",
    "Hostel":         "#FFD700",
    "Sports":         "#00FF7F",
    "Cafe":           "#FF69B4",
    "Mess":           "#FFA500",
    "Admin":          "#FFFFFF",
    "Library":        "#DA70D6",
    "Mosque":         "#7CFC00",
    "Landmark":       "#00FFFF",
    "Medical":        "#FF6347",
    "Infrastructure": "#A9A9A9",
    "Industrial":     "#C0C0C0",
    "Residential":    "#DEB887",
}

DEFAULT_COLOR = "#EEEEEE"


def _color_for(category):
    return CATEGORY_COLORS.get(category, DEFAULT_COLOR)


def _draw_quadtree_grid(ax, qt, alpha=0.6):
    """Recursively draw quadtree cell boundaries."""
    cx, cy, hw, hh = qt["boundary"]
    corners = [
        (cx - hw, cy - hh),
        (cx + hw, cy - hh),
        (cx + hw, cy + hh),
        (cx - hw, cy + hh),
    ]
    poly = Polygon(corners, closed=True, linewidth=0.5,
                   edgecolor="lime", facecolor="none", alpha=alpha, zorder=4)
    ax.add_patch(poly)
    if qt["divided"]:
        for child in ("nw", "ne", "sw", "se"):
            _draw_quadtree_grid(ax, qt[child], alpha * 0.85)


def show_map(qt, map_config, points=None, highlight_ids=None,
             show_grid=False, title=None):
    """Render the satellite image with points overlaid."""
    if points is None:
        points = query_all(qt)

    highlight_ids = set(highlight_ids or [])
    map_name = map_config["name"]

    img, extent = _load_image(map_config)
    if img is None:
        print("  No satellite image available.")
        return

    center_lat = qt["boundary"][1]
    geo_aspect = 1.0 / math.cos(math.radians(center_lat))

    fig, ax = plt.subplots(1, 1, figsize=(12, 14))
    ax.imshow(img, extent=[extent[0], extent[1], extent[2], extent[3]],
              aspect=geo_aspect, zorder=0)
    ax.set_aspect(geo_aspect)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    if show_grid:
        _draw_quadtree_grid(ax, qt)

    seen_categories = set()
    for p in points:
        color = _color_for(p["category"])
        is_hl = p["id"] in highlight_ids
        size = 60 if is_hl else 25
        edge = "white" if is_hl else "black"
        lw = 1.5 if is_hl else 0.4

        label = p["category"] if p["category"] not in seen_categories else None
        seen_categories.add(p["category"])

        ax.scatter(p["x"], p["y"], s=size, c=color, edgecolors=edge,
                   linewidths=lw, zorder=5, label=label)

        if is_hl:
            ax.annotate(
                p["name"], (p["x"], p["y"]),
                textcoords="offset points", xytext=(8, 8),
                fontsize=7, color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.7),
                zorder=6,
            )

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc="upper left", fontsize=7,
                  framealpha=0.8, facecolor="black", labelcolor="white",
                  edgecolor="gray")

    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    ax.tick_params(labelsize=7)
    plot_title = title or f"{map_name}  ({count(qt)} locations)"
    if show_grid:
        plot_title += "  [QuadTree grid]"
    ax.set_title(plot_title, fontsize=12, color="white",
                 bbox=dict(fc="black", alpha=0.7, pad=4))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    plt.tight_layout()
    print("  Displaying map... (close the window to return to CLI)")
    plt.show()


def show_points_on_map(qt, map_config, points, title=None, show_grid=False):
    """Show only specific points highlighted on the satellite image."""
    all_pts = query_all(qt)
    highlight_ids = [p["id"] for p in points]
    show_map(qt, map_config, points=all_pts, highlight_ids=highlight_ids,
             show_grid=show_grid, title=title)
