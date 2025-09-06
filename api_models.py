"""
API Models and Schemas for OSM POC FastAPI
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class OutputType(str, Enum):
    """Available output types"""
    REPORT = "report"
    PLOT = "plot"
    MAP = "map"
    SUMMARY = "summary"
    DATA = "data"
    MACH9 = "mach9"
    ALL = "all"


class BoundingBox(BaseModel):
    """
    Geographic bounding box coordinates for OSM data queries.
    
    Defines a rectangular area on Earth's surface using latitude and longitude coordinates.
    The bounding box must be valid (min < max) and within Earth's coordinate limits.
    
    Examples:
    - London Eye, UK: min_lat=51.5033, min_lon=-0.1196, max_lat=51.5043, max_lon=-0.1186
    - Central Park, NYC: min_lat=40.7648, min_lon=-73.9808, max_lat=40.8006, max_lon=-73.949
    - Times Square, NYC: min_lat=40.758, min_lon=-73.9855, max_lat=40.7585, max_lon=-73.985
    - Small test area: min_lat=40.775, min_lon=-73.975, max_lat=40.785, max_lon=-73.965
    """
    min_lat: float = Field(
        ..., 
        ge=-90, 
        le=90, 
        description="Minimum latitude (southern boundary)",
        example=51.5033
    )
    min_lon: float = Field(
        ..., 
        ge=-180, 
        le=180, 
        description="Minimum longitude (western boundary)",
        example=-0.1196
    )
    max_lat: float = Field(
        ..., 
        ge=-90, 
        le=90, 
        description="Maximum latitude (northern boundary)",
        example=51.5043
    )
    max_lon: float = Field(
        ..., 
        ge=-180, 
        le=180, 
        description="Maximum longitude (eastern boundary)",
        example=-0.1186
    )
    
    @validator('max_lat')
    def max_lat_must_be_greater_than_min_lat(cls, v, values):
        if 'min_lat' in values and v <= values['min_lat']:
            raise ValueError('max_lat must be greater than min_lat')
        return v
    
    @validator('max_lon')
    def max_lon_must_be_greater_than_min_lon(cls, v, values):
        if 'min_lon' in values and v <= values['min_lon']:
            raise ValueError('max_lon must be greater than min_lon')
        return v


class OSMQueryRequest(BaseModel):
    """
    Request model for querying OpenStreetMap data within a specified geographic area.
    
    This endpoint allows you to retrieve raw OSM data (nodes, ways, relations) for specific
    feature types within a bounding box. The data is returned in a structured format suitable
    for further processing and analysis.
    
    Use Cases:
    - Civil engineering surveys
    - Infrastructure mapping
    - Transportation planning
    - Urban analysis
    - GIS data collection
    
    Rate Limits: 20 requests per minute
    """
    bbox: BoundingBox = Field(
        ..., 
        description="Geographic bounding box defining the area to query"
    )
    feature_types: Optional[List[str]] = Field(
        default=None,
        description="List of OSM feature types to query. If None, queries all available features. Available types include: highway, building, amenity, shop, tourism, leisure, natural, landuse, power, telecom, barrier, man_made, railway, waterway, place, office, craft, healthcare, sport, historic, heritage, emergency, military, and many more. See /feature-types endpoint for complete list.",
        example=["highway", "building", "amenity", "shop", "tourism", "leisure", "natural", "landuse", "power", "telecom", "barrier", "man_made", "railway", "waterway", "place"]
    )
    outputs: List[OutputType] = Field(
        default=[OutputType.ALL],
        description="List of output types to generate. Use 'all' to generate all available outputs.",
        example=["report", "plot", "map"]
    )
    
    class Config:
        schema_extra = {
            "example": {
                "bbox": {
                    "min_lat": 51.5033,
                    "min_lon": -0.1196,
                    "max_lat": 51.5043,
                    "max_lon": -0.1186
                },
                "feature_types": [
                    "highway", "building", "amenity", "shop", "tourism", 
                    "leisure", "natural", "landuse", "power", "telecom",
                    "barrier", "man_made", "railway", "waterway", "place"
                ],
                "outputs": ["report", "plot", "map"]
            }
        }


class OSMElement(BaseModel):
    """Individual OSM element"""
    id: int
    type: str
    tags: Dict[str, str] = {}
    geometry: Optional[Dict[str, Any]] = None


class OSMDataResponse(BaseModel):
    """
    Response model containing raw OpenStreetMap data.
    
    This response includes all OSM elements (nodes, ways, relations) found within the
    specified bounding box for the requested feature types. The data is structured
    for easy processing and analysis.
    
    Data Structure:
    - nodes: Point features (e.g., traffic lights, manholes, buildings)
    - ways: Linear and polygonal features (e.g., roads, building outlines)
    - relations: Complex features (e.g., bus routes, administrative boundaries)
    """
    total_elements: int = Field(..., description="Total number of OSM elements found", example=1250)
    nodes: List[OSMElement] = Field(..., description="List of OSM node elements")
    ways: List[OSMElement] = Field(..., description="List of OSM way elements")
    relations: List[OSMElement] = Field(..., description="List of OSM relation elements")
    bbox: BoundingBox = Field(..., description="The bounding box that was queried")
    feature_types: List[str] = Field(..., description="Feature types that were queried")
    query_time: str = Field(..., description="ISO timestamp when the query was executed")


class ReportResponse(BaseModel):
    """Response model for text report"""
    report_text: str
    file_path: Optional[str] = None
    bbox: BoundingBox
    total_elements: int


class VisualizationResponse(BaseModel):
    """Response model for visualizations"""
    file_path: str
    file_type: str
    bbox: BoundingBox
    total_elements: int
    description: str


class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    files: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str = "1.0.0"


# Available feature types for validation - comprehensive OSM feature types
AVAILABLE_FEATURE_TYPES = [
    # Transportation
    "highway", "railway", "aeroway", "waterway", "aerialway", "public_transport",
    
    # Buildings and Infrastructure
    "building", "barrier", "man_made", "power", "telecom",
    
    # Land Use and Natural Features
    "landuse", "natural", "geological", "boundary",
    
    # Amenities and Services
    "amenity", "shop", "tourism", "leisure", "sport", "healthcare",
    
    # Administrative and Places
    "place", "office", "craft", "military", "emergency",
    
    # Historical and Cultural
    "historic", "heritage", "archaeological_site",
    
    # Civil Engineering and Survey Features
    "kerb", "tunnel", "bridge", "embankment", "retaining_wall", "cycle_barrier",
    "survey_point", "benchmark", "marker", "culvert", "drain", "ditch",
    "street_lamp", "traffic_signals", "bollard", "fence", "wall", "gate",
    "manhole", "utility_pole", "street_cabinet", "fire_hydrant", "pipeline",
    "tower", "mast", "antenna", "substation", "generator", "transformer",
    "noise_barrier", "sound_barrier", "guard_rail", "crash_barrier",
    "steps", "ramp", "elevator", "escalator", "handrail", "railing",
    
    # Drainage and Inlet Features
    "inlet", "inlet_grate", "inlet_kerb_grate", "kerb_opening", "storm_drain", "catch_basin",
    
    # Additional Categories
    "route", "traffic_sign", "traffic_calming", "surface", "access",
    "addr", "name", "ref", "operator", "brand", "website", "phone",
    "opening_hours", "fee", "wheelchair", "smoking", "wifi"
]

# Mach9 Engineering & Survey Feature Types - focused on civil engineering
MACH9_FEATURE_TYPES = [
    # Transportation Infrastructure
    "highway", "railway", "aeroway", "waterway", "public_transport",
    
    # Physical Barriers and Structures
    "barrier", "man_made", "building",
    
    # Utility Infrastructure
    "power", "telecom", "amenity",  # includes fire hydrants, manholes, etc.
    
    # Survey and Engineering Features
    "natural", "landuse", "boundary",
    
    # Traffic Control and Safety
    "traffic_sign", "traffic_calming",
    
    # Surface and Access
    "surface", "access", "kerb",  # kerbs/curbs for civil engineering
    
    # Additional Civil Engineering Features
    "tunnel", "bridge", "embankment", "retaining_wall", "cycle_barrier",
    "survey_point", "benchmark", "marker", "culvert", "drain", "ditch",
    "street_lamp", "traffic_signals", "bollard", "fence", "wall", "gate",
    "manhole", "utility_pole", "street_cabinet", "fire_hydrant", "pipeline",
    "tower", "mast", "antenna", "substation", "generator", "transformer",
    "noise_barrier", "sound_barrier", "guard_rail", "crash_barrier",
    "steps", "ramp", "elevator", "escalator", "handrail", "railing",
    
    # Drainage and Inlet Features
    "inlet", "inlet_grate", "inlet_kerb_grate", "kerb_opening", "storm_drain", "catch_basin"
]


class FeatureTypeValidator:
    """Validator for feature types"""
    
    @staticmethod
    def validate_feature_types(feature_types: List[str]) -> List[str]:
        """Validate and filter feature types"""
        if not feature_types:
            return AVAILABLE_FEATURE_TYPES
        
        valid_types = []
        for feature_type in feature_types:
            if feature_type in AVAILABLE_FEATURE_TYPES:
                valid_types.append(feature_type)
            else:
                # Log warning but don't fail
                print(f"Warning: Unknown feature type '{feature_type}' ignored")
        
        return valid_types if valid_types else AVAILABLE_FEATURE_TYPES