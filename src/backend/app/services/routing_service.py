import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx
from sqlalchemy.orm import Session
from app.models.entities import POINode, PathEdge, TourSession

class RoutingService:
    def calculate_solar_position(self, hour: float = None, latitude_deg: float = 12.6165) -> Tuple[float, float]:
        """
        Computes NOAA-aligned solar elevation & azimuth for Mahabalipuram (12.6165° N).
        """
        if hour is None:
            now = datetime.now()
            hour = now.hour + now.minute / 60.0

        if 6.0 <= hour <= 18.0:
            solar_angle_rad = ((hour - 6.0) / 12.0) * math.pi
            elevation = math.sin(solar_angle_rad) * (90.0 - abs(latitude_deg - 15.0))
            azimuth = 90.0 + ((hour - 6.0) / 12.0) * 180.0
        else:
            elevation = 0.0
            azimuth = 0.0

        return max(0.0, elevation), azimuth

    def compute_dynamic_shade(self, base_shade: float, path_type: str, hour: float = None) -> float:
        """
        Computes dynamic shade factor [0.0..1.0] based on solar elevation and architectural canopy.
        """
        elevation, _ = self.calculate_solar_position(hour)

        if path_type == "covered_corridor":
            return 0.95
        elif path_type == "colonnade":
            return 0.85
        elif path_type == "tree_avenue":
            return 0.78
        elif path_type == "monument_shadow":
            if elevation > 72:
                return 0.30
            elif 15 <= elevation <= 72:
                return 0.80
            else:
                return 0.55
        else:
            return 0.05 if elevation > 45 else 0.35

    def build_graph(self, db: Session, hour: float = None) -> Tuple[nx.Graph, Dict[int, POINode]]:
        nodes = db.query(POINode).all()
        edges = db.query(PathEdge).all()

        node_map = {n.id: n for n in nodes}
        G = nx.Graph()

        for n in nodes:
            G.add_node(n.id, name=n.name, slug=n.slug, category=n.category, x=n.x, y=n.y)

        for e in edges:
            shade = self.compute_dynamic_shade(e.base_shade_factor, e.path_type, hour)
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

        return G, node_map

    def find_path(
        self,
        db: Session,
        start_id: int,
        target_id: int,
        mode: str = "shaded",
        hour: float = None
    ) -> Dict[str, Any]:
        G, node_map = self.build_graph(db, hour)

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
        elevation, azimuth = self.calculate_solar_position(hour)

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
            "solar_state": {
                "solar_elevation_deg": round(elevation, 1),
                "solar_azimuth_deg": round(azimuth, 1)
            },
            "segments": segments
        }

    def find_nearest_shaded_rest_stop(self, db: Session, current_node_id: int, hour: float = None) -> Dict[str, Any]:
        G, node_map = self.build_graph(db, hour)

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

        return self.get_dual_telemetry(db, start_id=current_node_id, target_id=best_stop.id, hour=hour)

    def get_dual_telemetry(
        self,
        db: Session,
        start_id: int = 1,
        target_id: int = 6,
        hour: float = None
    ) -> Dict[str, Any]:
        """
        Computes BOTH Standard Shortest Path and Solar-Optimized Shaded Path,
        plus Heat Exposure Saved (%) and live active visitor counts per node.
        """
        shortest = self.find_path(db, start_id, target_id, mode="shortest", hour=hour)
        shaded = self.find_path(db, start_id, target_id, mode="shaded", hour=hour)

        elev, azim = self.calculate_solar_position(hour)
        is_peak = elev > 55.0

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
            "solar_elevation_deg": round(elev, 1),
            "solar_azimuth_deg": round(azim, 1),
            "sun_intensity": "HIGH (Peak Midday)" if is_peak else ("MODERATE" if elev > 25 else "MILD"),
            "shade_recommendation": "Use Shaded Colonnade & Banyan Canopy" if is_peak else "Comfortable coastal breeze",
            "active_visitor_nodes": active_counts,
            "active_tourists_total": len(active_sessions)
        }

routing_service = RoutingService()
