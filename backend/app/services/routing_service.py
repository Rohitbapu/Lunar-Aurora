import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx
from sqlalchemy.orm import Session
from app.models.entities import POINode, PathEdge

class RoutingService:
    def __init__(self):
        pass

    def calculate_solar_position(self, hour: float = None, latitude_deg: float = 13.0) -> Tuple[float, float]:
        """
        Calculates approximate solar elevation (deg) and azimuth (deg) for a given hour.
        0.0 to 24.0. Defaults to current local hour.
        """
        if hour is None:
            now = datetime.now()
            hour = now.hour + now.minute / 60.0

        # Simplified solar elevation: peaks at solar noon (~12:00)
        # Elevation: 0 at sunrise (~6:00), 90 at zenith, 0 at sunset (~18:00)
        if 6.0 <= hour <= 18.0:
            solar_angle_rad = ((hour - 6.0) / 12.0) * math.pi
            elevation = math.sin(solar_angle_rad) * (90.0 - abs(latitude_deg - 15.0))
            # Azimuth: 90 deg (East at sunrise) -> 180 deg (South at noon) -> 270 deg (West at sunset)
            azimuth = 90.0 + ((hour - 6.0) / 12.0) * 180.0
        else:
            elevation = 0.0 # Night
            azimuth = 0.0
            
        return max(0.0, elevation), azimuth

    def compute_dynamic_shade(self, base_shade: float, path_type: str, hour: float = None) -> float:
        """
        Computes dynamic shade factor (0.0 to 1.0) considering time of day and path structure.
        """
        elevation, azimuth = self.calculate_solar_position(hour)
        
        # Covered colonnades and corridors provide permanent shelter from overhead sun
        if path_type == "covered_corridor":
            return 0.95
        elif path_type == "colonnade":
            # Best when sun has slight angle, still high shelter at noon
            return 0.85
        elif path_type == "tree_avenue":
            # High canopy filters sunlight throughout daytime
            return 0.75
        elif path_type == "monument_shadow":
            # Shadow length depends on solar elevation (cotangent of elevation)
            if elevation > 75: # Overhead sun = minimal building shadow
                return 0.3
            elif 15 <= elevation <= 75:
                return 0.8 # Long shadows cast by grand walls
            else:
                return 0.5
        else: # open_stone
            if elevation > 45:
                return 0.05 # Scorching midday heat
            else:
                return 0.35 # Mild morning/evening

    def build_graph(self, db: Session, hour: float = None) -> Tuple[nx.Graph, Dict[int, POINode]]:
        """
        Builds NetworkX weighted graph from POINodes and PathEdges.
        """
        nodes = db.query(POINode).all()
        edges = db.query(PathEdge).all()

        node_map = {n.id: n for n in nodes}
        G = nx.Graph()

        for n in nodes:
            G.add_node(n.id, name=n.name, slug=n.slug, category=n.category, x=n.x, y=n.y)

        for e in edges:
            shade = self.compute_dynamic_shade(e.base_shade_factor, e.path_type, hour)
            
            # Standard distance weight
            dist = e.distance_meters
            
            # Shaded path weight: penalizes low shade heavily
            # If shade=1.0, weight = dist * 1.0
            # If shade=0.0, weight = dist * 3.5 (tourist expends 3.5x thermal effort)
            sun_penalty = 1.0 + (1.0 - shade) * 2.5
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

        # Calculate path details
        total_distance = 0.0
        weighted_shade_sum = 0.0
        segments = []

        for i in range(len(path_ids) - 1):
            u, v = path_ids[i], path_ids[i+1]
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
            "estimated_walk_minutes": round(total_distance / 70.0, 1), # average 70m/min strolling speed
            "average_shade_index": round(avg_shade, 2),
            "solar_state": {
                "solar_elevation_deg": round(elevation, 1),
                "solar_azimuth_deg": round(azimuth, 1)
            },
            "segments": segments
        }

    def find_nearest_shaded_rest_stop(self, db: Session, current_node_id: int, hour: float = None) -> Dict[str, Any]:
        """
        Smart 'Take a Rest' button logic:
        Finds the nearest shaded pavilion or bench area along the coolest route.
        """
        G, node_map = self.build_graph(db, hour)

        if current_node_id not in G:
            raise ValueError(f"Current Node ID {current_node_id} not found.")

        # Prefer true cool tree-shaded rest pavilions with seating & water first
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
        best_path = None
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

        # Retrieve full path details
        return self.find_path(db, current_node_id, best_stop.id, mode="shaded", hour=hour)

routing_service = RoutingService()

