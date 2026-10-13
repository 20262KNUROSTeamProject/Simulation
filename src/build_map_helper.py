
import json
from pathlib import Path

import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


def angle_diff_deg(a, b):
    """Orientation difference for undirected lines: [0, 180)."""
    return abs((a - b + 90.0) % 180.0 - 90.0)


def segment_info(p1, p2):
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)

    delta = p2 - p1
    length = float(np.linalg.norm(delta))

    if length < 1e-6:
        return None

    angle = np.degrees(np.arctan2(-delta[1], delta[0])) % 180.0

    return {
        "p1": p1,
        "p2": p2,
        "center": (p1 + p2) / 2.0,
        "length": length,
        "angle": angle,
        "direction": delta / length,
    }


def project_interval(segment, direction):
    points = np.vstack([segment["p1"], segment["p2"]])
    values = points @ direction
    return float(values.min()), float(values.max())


def merge_segments(
    segments,
    angle_threshold=8.0,
    perpendicular_threshold=3.0,
    gap_threshold=5.0,
):
    """
    Merge nearly collinear segments when:
      1. orientation difference is small,
      2. perpendicular distance is small,
      3. projected gap is small.

    Distances are measured in pixels.
    """
    segments = [s.copy() for s in segments]
    changed = True

    while changed:
        changed = False

        for i in range(len(segments)):
            if changed:
                break

            a = segments[i]

            for j in range(i + 1, len(segments)):
                b = segments[j]

                if angle_diff_deg(a["angle"], b["angle"]) > angle_threshold:
                    continue

                # Use average orientation as the candidate merge direction.
                theta_a = np.radians(a["angle"])
                theta_b = np.radians(b["angle"])

                # Image y increases downward, hence the negative sine.
                da = np.array([np.cos(theta_a), -np.sin(theta_a)])
                db = np.array([np.cos(theta_b), -np.sin(theta_b)])

                if np.dot(da,db) < 0:
                    db = -db

                direction = da + db
                norm = np.linalg.norm(direction)

                if norm < 1e-6:
                    continue

                direction /= norm
                normal = np.array([-direction[1], direction[0]]) # perpendicular to direction vector

                # Compare perpendicular offsets.
                offset_a = float(a["center"] @ normal)
                offset_b = float(b["center"] @ normal)

                if abs(offset_a - offset_b) > perpendicular_threshold:
                    continue

                # Compare projected intervals along the line direction.
                a_min, a_max = project_interval(a, direction)
                b_min, b_max = project_interval(b, direction)

                gap = max(
                    0.0,
                    max(a_min, b_min) - min(a_max, b_max),
                )

                if gap > gap_threshold:
                    continue

                # Merge both intervals into one segment.
                all_points = np.vstack([
                    a["p1"], a["p2"], b["p1"], b["p2"]
                ])

                along = all_points @ direction
                across = all_points @ normal

                lo = float(along.min())
                hi = float(along.max())
                offset = float(np.mean(across))

                p1 = direction * lo + normal * offset
                p2 = direction * hi + normal * offset

                merged = segment_info(p1, p2)

                if merged is None:
                    continue

                merged["component_id"] = a["component_id"]
                merged["source_segments"] = (
                    a.get("source_segments", 1)
                    + b.get("source_segments", 1)
                )

                segments[i] = merged
                segments.pop(j)

                changed = True
                break

    return segments


def estimate_width(segment, occupied, max_width_px=30):
    """
    Estimate local occupied width near the segment midpoint.

    This is a local cross-section estimate, not a guaranteed
    physical wall thickness.
    """
    center = segment["center"]
    direction = segment["direction"]
    normal = np.array([-direction[1], direction[0]])

    height, width = occupied.shape

    # Sample several points along the segment.
    sample_count = max(3, int(segment["length"] / 5))
    sample_positions = np.linspace(
        0.15, 0.85, sample_count
    )

    widths = []

    for t in sample_positions:
        point = segment["p1"] + t * (
            segment["p2"] - segment["p1"]
        )

        occupied_distances = []

        # Scan both directions across the line.
        for sign in (-1, 1):
            last_distance = 0.0

            for d in np.arange(0.0, max_width_px + 0.5, 0.5):
                q = point + sign * d * normal

                x, y = int(round(q[0])), int(round(q[1]))

                if not (0 <= x < width and 0 <= y < height):
                    break

                if not occupied[y, x]:
                    break

                last_distance = d

            occupied_distances.append(last_distance)

        total_width = sum(occupied_distances)

        if total_width > 0:
            widths.append(total_width)

    if not widths:
        return None

    return float(np.median(widths))


def build_map(DATA_ROOT_DIR: Path):
    config_path = DATA_ROOT_DIR / "map_config" / "map.json"

    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    image_path = config_path.parent / config["map_path"]

    resolution = float(config["pixel_resolution"])
    wall_height = float(config["wall_height"])
    wall_thickness = float(config["wall_thickness"])
    origin_x, origin_y, origin_yaw = config["origin"]

    image = np.asarray(
        Image.open(image_path).convert("L")
    )

    occupied = image < 100

    num_labels, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            occupied.astype(np.uint8),
            connectivity=8,
            ltype=cv2.CV_32S,
        )
    )

    # Tune these values based on the map.
    epsilon_px = 1.5
    min_segment_length_px = 4.0

    all_segments = []

    # 1. Extract contour segments per connected component.
    for label_id in range(1, num_labels):
        component = (
            labels == label_id
        ).astype(np.uint8) * 255

        contours, _ = cv2.findContours(
            component,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE,
        )

        component_segments = []

        for contour in contours:
            if len(contour) < 3:
                continue

            polygon = cv2.approxPolyDP(
                contour,
                epsilon_px,
                True,
            ).reshape(-1, 2)

            if len(polygon) < 2:
                continue

            for i in range(len(polygon)):
                p1 = polygon[i]
                p2 = polygon[(i + 1) % len(polygon)]

                segment = segment_info(p1, p2)

                if segment is None:
                    continue

                if segment["length"] < min_segment_length_px:
                    continue

                segment["component_id"] = label_id
                segment["source_segments"] = 1

                component_segments.append(segment)

        """ for segment in component_segments:
            result = {
                "component_id": segment["component_id"],
                "start_px": segment['p1'].tolist(),
                "end_px": segment['p2'].tolist(),
                "center_px": segment['center'].tolist(),
                "length_m": segment["length"] * resolution,
                "width_m": wall_thickness,
                "height_m": wall_height,
                "angle_deg": segment["angle"],
                "source_segments": segment["source_segments"],
            }
        
            all_segments.append(result) """

        # 2. Merge nearly collinear segments within this component.
        merged = merge_segments(component_segments)

        for segment in merged:
            # 3. Estimate width from occupied pixels.
            width_px_est = estimate_width(segment, occupied)

            if width_px_est is None:
                width_px_est = wall_thickness / resolution

            # Avoid implausibly small widths.
            width_px_est = max(width_px_est, 1.0)

            # Convert to metric units.
            p1 = segment["p1"]
            p2 = segment["p2"]
            center = segment["center"]

            result = {
                "component_id": segment["component_id"],
                "start_px": p1.tolist(),
                "end_px": p2.tolist(),
                "center_px": center.tolist(),
                "length_m": segment["length"] * resolution,
                "width_m": width_px_est * resolution,
                "height_m": wall_height,
                "angle_deg": segment["angle"],
                "source_segments": segment["source_segments"],
            }

            all_segments.append(result)

    print(f"[INFO] Final segment count: {len(all_segments)}")

    for i, s in enumerate(all_segments):
        print(
            f"[{i}] component={s['component_id']} "
            f"length={s['length_m']:.3f}m "
            f"width={s['width_m']:.3f}m "
            f"height={s['height_m']:.3f}m "
            f"angle={s['angle_deg']:.1f}deg"
        )

    # 4. Visualization: merged segments and estimated widths.
    """ fig, ax = plt.subplots(figsize=(12, 8))

    for i, s in enumerate(all_segments):
        p1 = np.asarray(s["start_px"])
        p2 = np.asarray(s["end_px"])

        # Draw the centerline.
        ax.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            linewidth=2,
        )

        # Draw endpoints and segment ID.
        ax.scatter(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            s=10,
        )

        center = np.asarray(s["center_px"])
        ax.text(
            center[0],
            center[1],
            str(i),
            fontsize=8,
            color="red",
        )

    ax.set_title("Merged Wall Segments")
    ax.set_xlabel("X (pixel)")
    ax.set_ylabel("Y (pixel)")
    ax.set_xlim(0, image.shape[0])
    ax.set_ylim(image.shape[1], 0)
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.show() """

    return all_segments, {"resolution":resolution,"wall_height":wall_height,"wall_thickness":wall_thickness, "origin":(origin_x, origin_y, origin_yaw), "image_shape":image.shape}

# =======================================
# Utils functions
# =======================================

import numpy as np
from pxr import UsdGeom, UsdPhysics, Gf, Sdf

def add_wall_segment(
    stage,
    prim_path: str,
    center,
    length: float,
    thickness: float,
    height: float,
    angle_deg: float,
):
    """
    Create one wall as a cube-like rectangular prism.

    center: (x, y, z), in meters
    length: wall length in meters
    thickness: wall thickness in meters
    height: wall height in meters
    angle_deg: rotation around the Z axis, in degrees
    """

    cube = UsdGeom.Cube.Define(stage, prim_path)
    cube.CreateSizeAttr(1.0)

    # Translate, Rotate, Scale을 일관된 방식으로 설정
    xform = UsdGeom.XformCommonAPI(cube.GetPrim())

    xform.SetTranslate(Gf.Vec3d(
        float(center[0]),
        float(center[1]),
        float(center[2]),
    ))

    xform.SetRotate(
        Gf.Vec3f(0.0, 0.0, -float(angle_deg))
    )

    xform.SetScale(Gf.Vec3f(
        float(length),
        float(thickness),
        float(height),
    ))

    # 정적 벽의 충돌 형상
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim())

    return cube.GetPrim()

def pixel_to_world(
    px,
    py,
    image_height,
    resolution,
    origin_x,
    origin_y,
):
    x = origin_x + px * resolution
    y = origin_y + (image_height - py) * resolution

    return x, y

