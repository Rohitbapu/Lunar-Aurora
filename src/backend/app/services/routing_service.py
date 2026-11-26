import calendar
import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx
from sqlalchemy.orm import Session
from app.models.entities import POINode, PathEdge, TourSession

DEFAULT_DEMO_DATE = "2027-01-11"
MAHABALIPURAM_LAT_DEG = 12.6165
MAHABALIPURAM_LON_DEG = 80.19
IST_OFFSET_HOURS = 5.5
IST_TZ = timezone(timedelta(hours=5, minutes=30))


class RoutingService:
    def calculate_solar_position_details(
        self,
        hour: Optional[float] = None,
        date_str: Optional[str] = DEFAULT_DEMO_DATE,
        latitude_deg: float = MAHABALIPURAM_LAT_DEG,
        longitude_deg: float = MAHABALIPURAM_LON_DEG,
        tz_offset_hours: float = IST_OFFSET_HOURS,
    ) -> Dict[str, Any]:
        """
        Computes real solar geometry using the NOAA General Solar Position Equations
        (fractional year, equation of time, solar declination, true solar time,
        hour angle, solar elevation, and solar azimuth clockwise from North).
        Defaults to the Finale date (2027-01-11) at Mahabalipuram (12.6165 N, 80.19 E, IST).
        """
        effective_date = (date_str or DEFAULT_DEMO_DATE).strip()
        try:
            dt = datetime.strptime(effective_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"Invalid date '{date_str}'. Expected YYYY-MM-DD.") from exc

        if hour is None:
            now_ist = datetime.now(IST_TZ)
            hour = now_ist.hour + now_ist.minute / 60.0 + now_ist.second / 3600.0
        else:
            hour = max(0.0, min(24.0, float(hour)))

        day_of_year = dt.timetuple().tm_yday
        days_in_year = 366 if calendar.isleap(dt.year) else 365

        # Fractional year (radians)
        gamma = (2.0 * math.pi / days_in_year) * (day_of_year - 1 + (hour - 12.0) / 24.0)

        # Equation of time (minutes)
        eq_time_min = 229.18 * (
            0.000075
            + 0.001868 * math.cos(gamma)
            - 0.032077 * math.sin(gamma)
            - 0.014615 * math.cos(2.0 * gamma)
            - 0.040849 * math.sin(2.0 * gamma)
        )

        # Solar declination angle (radians)
        decl_rad = (
            0.006918
            - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2.0 * gamma)
            + 0.000907 * math.sin(2.0 * gamma)
            - 0.002697 * math.cos(3.0 * gamma)
            + 0.00148 * math.sin(3.0 * gamma)
        )
        decl_deg = math.degrees(decl_rad)

        # True solar time (minutes) and solar hour angle (degrees)
        time_offset_min = eq_time_min + 4.0 * longitude_deg - 60.0 * tz_offset_hours
        true_solar_time_min = (hour * 60.0 + time_offset_min) % 1440.0
        hour_angle_deg = true_solar_time_min / 4.0 - 180.0

        lat_rad = math.radians(latitude_deg)
        ha_rad = math.radians(hour_angle_deg)

        # Solar zenith angle
        cos_zenith = (
            math.sin(lat_rad) * math.sin(decl_rad)
            + math.cos(lat_rad) * math.cos(decl_rad) * math.cos(ha_rad)
        )
        cos_zenith = max(-1.0, min(1.0, cos_zenith))
        zenith_rad = math.acos(cos_zenith)
        raw_elevation_deg = 90.0 - math.degrees(zenith_rad)
        elevation_deg = max(0.0, raw_elevation_deg)

        # Solar azimuth (degrees clockwise from North)
        sin_zenith = math.sin(zenith_rad)
        if abs(math.cos(lat_rad) * sin_zenith) < 1e-9:
            azimuth_deg = 180.0
        else:
            cos_azimuth = (
                math.sin(decl_rad) - math.sin(lat_rad) * cos_zenith
            ) / (math.cos(lat_rad) * sin_zenith)
            cos_azimuth = max(-1.0, min(1.0, cos_azimuth))
            az_deg = math.degrees(math.acos(cos_azimuth))
            azimuth_deg = (360.0 - az_deg) if hour_angle_deg > 0.0 else az_deg

        return {
            "date": dt.strftime("%Y-%m-%d"),
            "hour": round(hour, 4),
            "latitude_deg": latitude_deg,
            "longitude_deg": longitude_deg,
            "tz_offset_hours": tz_offset_hours,
            "day_of_year": day_of_year,
            "fractional_year_rad": round(gamma, 6),
            "equation_of_time_min": round(eq_time_min, 3),
            "declination_deg": round(decl_deg, 3),
            "hour_angle_deg": round(hour_angle_deg, 3),
            "solar_elevation_deg": round(elevation_deg, 2),
            "raw_solar_elevation_deg": round(raw_elevation_deg, 2),
            "solar_azimuth_deg": round(azimuth_deg, 2),
        }

    def calculate_solar_position(
        self,
        hour: float = None,
        latitude_deg: float = MAHABALIPURAM_LAT_DEG,
        date_str: str = DEFAULT_DEMO_DATE,
        longitude_deg: float = MAHABALIPURAM_LON_DEG,
    ) -> Tuple[float, float]:
        """Returns (solar_elevation_deg, solar_azimuth_deg) from NOAA equations."""
        details = self.calculate_solar_position_details(
            hour=hour,
            date_str=date_str,
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
        )
        return details["solar_elevation_deg"], details["solar_azimuth_deg"]

    def compute_dynamic_shade(
        self,
        base_shade: float,
        path_type: str,
        hour: float = None,
        date_str: str = DEFAULT_DEMO_DATE,
        elevation_deg: Optional[float] = None,
    ) -> float:
        """
        Model estimate of dynamic shade factor [0.0..1.0] combining edge base_shade_factor,
        path architectural cover, and NOAA solar elevation angle.
        """
        if elevation_deg is None:
            elevation, _ = self.calculate_solar_position(hour=hour, date_str=date_str)
        else:
            elevation = elevation_deg

        if elevation <= 0.0:
            return 1.0

        sin_elev = math.sin(math.radians(elevation))

        if path_type in ("covered_corridor", "cave_shelter"):
            return round(min(0.95, max(base_shade, 0.88)), 2)
        elif path_type in ("colonnade", "cave_approach"):
            return round(max(0.55, base_shade - 0.12 * sin_elev), 2)
        elif path_type == "tree_avenue":
            return round(max(0.45, base_shade - 0.15 * sin_elev), 2)
        elif path_type == "monument_shadow":
            if elevation > 72.0:
                return 0.30
            elif 15.0 <= elevation <= 72.0:
                return round(max(base_shade, 0.78), 2)
            else:
                return 0.55
        elif path_type == "coastal_walk":
            return round(max(0.20, base_shade * (1.0 - 0.45 * sin_elev)), 2)
        else:
            return round(max(0.05, base_shade * (1.0 - 0.55 * sin_elev)), 2)

    def build_graph(
        self,
        db: Session,
        hour: float = None,
        date_str: str = DEFAULT_DEMO_DATE,
    ) -> Tuple[nx.Graph, Dict[int, POINode], Dict[str, Any]]:
        solar_details = self.calculate_solar_position_details(hour=hour, date_str=date_str)
        elev = solar_details["solar_elevation_deg"]

        nodes = db.query(POINode).all()
        edges = db.query(PathEdge).all()

        node_map = {n.id: n for n in nodes}
        G = nx.Graph()

        for n in nodes:
            G.add_node(n.id, name=n.name, slug=n.slug, category=n.category, x=n.x, y=n.y)

        for e in edges:
            shade = self.compute_dynamic_shade(
                e.base_shade_factor, e.path_type, hour=hour, date_str=date_str, elevation_deg=elev
            )
            dist = e.distance_meters
            sun_penalty = 1.0 + (1.0 - shade) * 2.8
            shaded_weight = dist * sun_penalty

            G.add_edge(
                e.source_id,
                e.target_id,
                distance=dist,
                shade=round(shade, 2),
                path_type=e.path_type,
                weight_distance=dist,
                weight_shaded=shaded_weight
            )

        return G, node_map, solar_details

    def find_path(
        self,
        db: Session,
        start_id: int,
        target_id: int,
        mode: str = "shaded",
        hour: float = None,
        date_str: str = DEFAULT_DEMO_DATE,
    ) -> Dict[str, Any]:
        G, node_map, solar_details = self.build_graph(db, hour=hour, date_str=date_str)

        if start_id not in G or target_id not in G:
            raise ValueError(f"Start ID {start_id} or Target ID {target_id} not found in site graph.")

        weight_key = "weight_shaded" if mode == "shaded" else "weight_distance"

        try:
            path_ids = nx.shortest_path(G, source=start_id, target=target_id, weight=weight_key)
        except nx.NetworkXNoPath:
            return {"found": False, "message": "No accessible route between specified points."}

        total_distance = 0.0
        weighted_shade_sum = 0.0
        segments = []

        for i in range(len(path_ids) - 1):
            u, v = path_ids[i], path_ids[i + 1]
            edge_data = G.get_edge_data(u, v)
            d = edge_data["distance"]
            s = edge_data["shade"]
            total_distance += d
            weighted_shade_sum += (d * s)
            segments.append({
                "from_node": node_map[u].name,
                "to_node": node_map[v].name,
                "distance": d,
                "shade_factor": s,
                "path_type": edge_data["path_type"]
            })

        avg_shade = (weighted_shade_sum / total_distance) if total_distance > 0 else 1.0
        sun_exposure = max(0.0, total_distance * (1.0 - avg_shade))

        return {
            "found": True,
            "mode": mode,
            "path_node_ids": path_ids,
            "path_nodes": [
                {
                    "id": n_id,
                    "name": node_map[n_id].name,
                    "slug": node_map[n_id].slug,
                    "x": node_map[n_id].x,
                    "y": node_map[n_id].y,
                    "category": node_map[n_id].category
                }
                for n_id in path_ids
            ],
            "total_distance_meters": round(total_distance, 1),
            "estimated_walk_minutes": round(total_distance / 70.0, 1),
            "average_shade_index": round(avg_shade, 2),
            "sun_exposure_meters": round(sun_exposure, 1),
            "solar_state": solar_details,
            "segments": segments
        }

    def find_nearest_shaded_rest_stop(
        self,
        db: Session,
        current_node_id: int,
        hour: float = None,
        date_str: str = DEFAULT_DEMO_DATE,
    ) -> Dict[str, Any]:
        G, node_map, _ = self.build_graph(db, hour=hour, date_str=date_str)

        if current_node_id not in G:
            raise ValueError(f"Current Node ID {current_node_id} not found.")

        rest_candidates = [
            n for n in node_map.values()
            if (n.category == "shade_rest" or (n.has_tree_shade and n.has_benches)) and n.id != current_node_id
        ]
        if not rest_candidates:
            rest_candidates = [
                n for n in node_map.values()
                if (n.has_benches or n.has_water) and n.id != current_node_id
            ]

        if not rest_candidates:
            return {"found": False, "message": "No rest stops available nearby."}

        best_stop = None
        best_cost = float("inf")

        for cand in rest_candidates:
            try:
                cost = nx.shortest_path_length(G, source=current_node_id, target=cand.id, weight="weight_shaded")
                if cost < best_cost:
                    best_cost = cost
                    best_stop = cand
            except nx.NetworkXNoPath:
                continue

        if best_stop is None:
            return {"found": False, "message": "No reachable shaded rest stops."}

        return self.get_dual_telemetry(
            db, start_id=current_node_id, target_id=best_stop.id, hour=hour, date_str=date_str
        )

    def get_dual_telemetry(
        self,
        db: Session,
        start_id: int = 1,
        target_id: int = 6,
        hour: float = None,
        date_str: str = DEFAULT_DEMO_DATE,
    ) -> Dict[str, Any]:
        """
        Computes BOTH Standard Shortest Path and NOAA-Solar-Optimized Shaded Path,
        plus Heat Exposure Saved (%) model estimate and live active visitor counts per node.
        """
        shortest = self.find_path(db, start_id, target_id, mode="shortest", hour=hour, date_str=date_str)
        shaded = self.find_path(db, start_id, target_id, mode="shaded", hour=hour, date_str=date_str)

        solar_details = shaded.get("solar_state") or self.calculate_solar_position_details(
            hour=hour, date_str=date_str
        )
        elev = solar_details["solar_elevation_deg"]
        azim = solar_details["solar_azimuth_deg"]
        is_peak = elev > 50.0

        shortest_exp = shortest.get("sun_exposure_meters", 1.0) if shortest.get("found") else 1.0
        shaded_exp = shaded.get("sun_exposure_meters", 0.0) if shaded.get("found") else 0.0
        heat_saved_pct = round(max(0.0, (1.0 - (shaded_exp / max(0.1, shortest_exp))) * 100.0), 1)
        dist_delta = round(
            (shaded.get("total_distance_meters", 0.0) - shortest.get("total_distance_meters", 0.0)), 1
        )

        # Active visitor counts per stop from TourSession DB
        active_sessions = db.query(TourSession).filter(TourSession.status == "in_progress").all()
        active_counts: Dict[str, int] = {}
        for sess in active_sessions:
            key = str(sess.current_step)
            active_counts[key] = active_counts.get(key, 0) + 1

        # Flatten primary shaded route fields for backward compatibility with existing callers
        return {
            "found": shaded.get("found", False),
            "start_id": start_id,
            "target_id": target_id,
            "date": solar_details["date"],
            "hour": solar_details["hour"],
            "latitude_deg": solar_details["latitude_deg"],
            "longitude_deg": solar_details["longitude_deg"],
            "path_node_ids": shaded.get("path_node_ids", []),
            "path_nodes": shaded.get("path_nodes", []),
            "total_distance_meters": shaded.get("total_distance_meters", 0.0),
            "estimated_walk_minutes": shaded.get("estimated_walk_minutes", 0.0),
            "average_shade_index": shaded.get("average_shade_index", 0.8),
            "shortest_path": {
                "path_node_ids": shortest.get("path_node_ids", []),
                "total_distance_meters": shortest.get("total_distance_meters", 0.0),
                "average_shade_index": shortest.get("average_shade_index", 0.0),
                "sun_exposure_meters": shortest_exp
            },
            "shaded_path": {
                "path_node_ids": shaded.get("path_node_ids", []),
                "total_distance_meters": shaded.get("total_distance_meters", 0.0),
                "average_shade_index": shaded.get("average_shade_index", 0.0),
                "sun_exposure_meters": shaded_exp
            },
            "route_distance_delta_meters": dist_delta,
            "heat_exposure_saved_pct": heat_saved_pct,
            "heat_estimate_note": "model estimate (distance x (1 - edge_shade_factor))",
            "solar_model": "NOAA General Solar Position Equations",
            "declination_deg": solar_details["declination_deg"],
            "equation_of_time_min": solar_details["equation_of_time_min"],
            "hour_angle_deg": solar_details["hour_angle_deg"],
            "solar_elevation_deg": elev,
            "solar_azimuth_deg": azim,
            "sun_intensity": "HIGH (Peak Midday)" if is_peak else ("MODERATE" if elev > 25 else ("NIGHT / TWILIGHT" if elev <= 0 else "MILD")),
            "shade_recommendation": "Use Shaded Cave Approach & Banyan Canopy (model estimate)" if is_peak else "Comfortable coastal breeze",
            "active_visitor_nodes": active_counts,
            "active_tourists_total": len(active_sessions)
        }

routing_service = RoutingService()
