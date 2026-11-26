from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.routing_service import routing_service

router = APIRouter(prefix="/api/routing", tags=["Smart Shaded Routing & Rest Stops"])

@router.get("/path")
def get_path(
    start_id: int = Query(..., description="Source POI ID"),
    target_id: int = Query(..., description="Destination POI ID"),
    mode: str = Query("shaded", pattern="^(shaded|shortest)$", description="Routing mode: 'shaded' or 'shortest'"),
    hour: Optional[float] = Query(None, description="Time of day in decimal hours (e.g. 13.5 for 1:30 PM)"),
    db: Session = Depends(get_db)
):
    """
    Computes shortest path or maximum-shade path between two points on the site graph.
    """
    try:
        result = routing_service.find_path(db, start_id, target_id, mode=mode, hour=hour)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/take-a-rest")
def take_a_rest(
    current_node_id: int = Query(..., description="Current visitor node ID"),
    hour: Optional[float] = Query(None, description="Time of day in decimal hours"),
    db: Session = Depends(get_db)
):
    """
    1-Tap Smart Rest Stop:
    Calculates the fastest route to the nearest cool, shaded rest pavilion or bench.
    """
    try:
        result = routing_service.find_nearest_shaded_rest_stop(db, current_node_id, hour=hour)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/solar-status")
def get_solar_status(
    hour: Optional[float] = Query(None, description="Time of day in decimal hours")
):
    """
    Returns current calculated solar elevation, azimuth, and UV heat strain factor.
    """
    elev, azim = routing_service.calculate_solar_position(hour)
    is_peak = (elev > 60.0)
    return {
        "hour": hour,
        "solar_elevation_deg": round(elev, 1),
        "solar_azimuth_deg": round(azim, 1),
        "sun_intensity": "HIGH (Peak Midday)" if is_peak else ("MODERATE" if elev > 25 else "MILD"),
        "shade_recommendation": "Stay in colonnades and tree avenues" if is_peak else "Comfortable walking conditions"
    }
