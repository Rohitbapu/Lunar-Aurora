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
    hour: Optional[float] = Query(None, ge=0.0, le=24.0, description="Time of day in IST decimal hours (e.g. 13.5 for 1:30 PM)"),
    date: str = Query("2027-01-11", description="Date in YYYY-MM-DD (defaults to Finale date 2027-01-11)"),
    db: Session = Depends(get_db)
):
    """
    Computes shortest path or maximum-shade path between two points on the site graph using NOAA solar geometry.
    """
    try:
        result = routing_service.find_path(db, start_id, target_id, mode=mode, hour=hour, date_str=date)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/take-a-rest")
def take_a_rest(
    current_node_id: int = Query(..., description="Current visitor node ID"),
    hour: Optional[float] = Query(None, ge=0.0, le=24.0, description="Time of day in IST decimal hours"),
    date: str = Query("2027-01-11", description="Date in YYYY-MM-DD (defaults to Finale date 2027-01-11)"),
    db: Session = Depends(get_db)
):
    """
    1-Tap Smart Rest Stop:
    Calculates the fastest route to the nearest cool, shaded rest pavilion or cave bench.
    """
    try:
        result = routing_service.find_nearest_shaded_rest_stop(db, current_node_id, hour=hour, date_str=date)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/solar-status")
def get_solar_status(
    hour: Optional[float] = Query(None, ge=0.0, le=24.0, description="Time of day in IST decimal hours"),
    date: str = Query("2027-01-11", description="Date in YYYY-MM-DD (defaults to Finale date 2027-01-11)")
):
    """
    Returns NOAA General Solar Position values (declination, equation of time, hour angle,
    elevation, azimuth) and heat recommendation for Mahabalipuram.
    """
    try:
        details = routing_service.calculate_solar_position_details(hour=hour, date_str=date)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    elev = details["solar_elevation_deg"]
    is_peak = (elev > 50.0)
    return {
        **details,
        "sun_intensity": "HIGH (Peak Midday)" if is_peak else ("MODERATE" if elev > 25 else ("NIGHT / TWILIGHT" if elev <= 0 else "MILD")),
        "shade_recommendation": "Stay in cave shelters and tree avenues" if is_peak else "Comfortable coastal breeze conditions",
        "solar_model": "NOAA General Solar Position Equations",
    }
