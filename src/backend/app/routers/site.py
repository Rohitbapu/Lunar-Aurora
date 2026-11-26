from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import POINode, PathEdge
from app.services.routing_service import routing_service

router = APIRouter(prefix="/api/site", tags=["Site Map & Landmarks"])

@router.get("/nodes")
def get_site_nodes(db: Session = Depends(get_db)):
    nodes = db.query(POINode).all()
    return nodes

@router.get("/edges")
def get_site_edges(db: Session = Depends(get_db)):
    edges = db.query(PathEdge).all()
    return edges

@router.get("/overview")
def get_site_overview(db: Session = Depends(get_db)):
    nodes = db.query(POINode).all()
    edges = db.query(PathEdge).all()
    return {
        "site_name": "Group of Monuments at Mahabalipuram (4.13 km 7-Stop Trail)",
        "total_poi_count": len(nodes),
        "total_paths_count": len(edges),
        "rest_stops_count": len([n for n in nodes if n.category == "shade_rest" or n.has_benches]),
        "nodes": nodes,
        "edges": edges
    }

@router.get("/telemetry")
def get_site_telemetry(
    start_id: int = Query(1, description="Origin POI node ID"),
    target_id: int = Query(6, description="Destination POI node ID"),
    hour: Optional[float] = Query(None, ge=0.0, le=24.0, description="Hour of day in IST (0-24) for NOAA solar calculation"),
    date: str = Query("2027-01-11", description="Date in YYYY-MM-DD (defaults to Finale date 2027-01-11)"),
    db: Session = Depends(get_db)
):
    """
    Dual-route NOAA solar telemetry + live crowd occupancy endpoint consumed by both
    WebXR ShadeMap.js and the Unity 6 Kiosk (No-SRD simulation mode / Operator HUD).
    """
    try:
        return routing_service.get_dual_telemetry(
            db, start_id=start_id, target_id=target_id, hour=hour, date_str=date
        )
    except ValueError as ve:
        detail = str(ve)
        status_code = 400 if "Invalid date" in detail else 404
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

