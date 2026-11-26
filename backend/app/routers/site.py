from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import POINode, PathEdge

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
        "site_name": "Lunar Aurora Ancient Acropolis",
        "total_poi_count": len(nodes),
        "total_paths_count": len(edges),
        "rest_stops_count": len([n for n in nodes if n.category == "shade_rest" or n.has_benches]),
        "nodes": nodes,
        "edges": edges
    }

