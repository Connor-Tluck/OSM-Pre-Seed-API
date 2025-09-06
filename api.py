"""
FastAPI Application for OSM Data Query and Visualization POC
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import aiofiles

from api_models import (
    OSMQueryRequest, OSMDataResponse, ReportResponse, 
    VisualizationResponse, APIResponse, ErrorResponse, 
    HealthResponse, OutputType, FeatureTypeValidator, MACH9_FEATURE_TYPES, AVAILABLE_FEATURE_TYPES
)
from osm_query import OSMQuery
from report_generator import OSMReportGenerator, save_json_report
from visualizer import OSMVisualizer, create_summary_plots
from mach9_report_generator import Mach9ReportGenerator, save_mach9_json_report


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="OSM Data Query & Analysis API",
    description="""
    ## OpenStreetMap Data Query & Analysis API
    
    A comprehensive API for querying, analyzing, and visualizing OpenStreetMap (OSM) data within specified geographic areas.
    
    ### Key Features
    
    * **Raw Data Queries**: Retrieve OSM nodes, ways, and relations for any geographic area
    * **Engineering Reports**: Generate specialized Mach9 engineering and survey reports
    * **Data Visualization**: Create interactive maps, static plots, and summary visualizations
    * **CSV Export**: Export detailed feature rollups for analysis
    * **Comprehensive Coverage**: Support for 60+ OSM feature types including civil engineering features
    
    ### Available Feature Types
    
    The API supports a comprehensive range of OSM feature types organized into categories:
    
    **Transportation**: highway, railway, aeroway, waterway, public_transport, traffic_sign, traffic_calming
    **Buildings & Infrastructure**: building, man_made, barrier, power, telecom, amenity
    **Natural Features**: natural, landuse, geological, boundary
    **Commercial & Services**: shop, tourism, leisure, sport, healthcare, office, craft
    **Administrative**: place, military, emergency, historic, heritage
    **Civil Engineering**: tunnel, bridge, embankment, retaining_wall, cycle_barrier, kerb, culvert, drain, ditch, street_lamp, traffic_signals, bollard, fence, wall, gate, manhole, utility_pole, street_cabinet, fire_hydrant, pipeline, tower, mast, antenna, substation, generator, transformer, noise_barrier, sound_barrier, guard_rail, crash_barrier, steps, ramp, elevator, escalator, handrail, railing
    **Survey & Control**: survey_point, benchmark, marker
    
    Use the `/feature-types` endpoint to get the complete list of available feature types.
    
    ### Use Cases
    
    * **Civil Engineering**: Infrastructure surveys, utility mapping, transportation planning
    * **Urban Planning**: City analysis, accessibility studies, infrastructure assessment
    * **GIS Applications**: Data collection, spatial analysis, mapping projects
    * **Research**: Academic studies, environmental analysis, demographic research
    
    ### Rate Limits
    
    * Query endpoints: 20 requests/minute
    * Generate endpoints: 10 requests/minute
    * File downloads: 30 requests/minute
    * Information endpoints: 60 requests/minute
    
    ### Security Features
    
    * Input validation and sanitization
    * Rate limiting to prevent abuse
    * CORS restrictions for security
    * Bounding box size limits
    * Feature type count limits
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "OSM Data Query API",
        "url": "http://localhost:8000",
    },
    license_info={
        "name": "MIT",
    },
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware with restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vue dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        # Add your production domains here
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Create output directory
OUTPUT_DIR = Path("api_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Mount static files for serving generated files
app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")

# Mount static files for custom docs
STATIC_DIR = Path("static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Security constants
MAX_BBOX_SIZE = 0.1  # Maximum bounding box size in degrees
MAX_FEATURE_TYPES = 20  # Maximum number of feature types per request (increased for Mach9)
MAX_ELEMENTS_PER_REQUEST = 50000  # Maximum elements to return per request


def validate_bounding_box(bbox) -> None:
    """Validate bounding box for security"""
    # Check bounding box size
    bbox_size_lat = bbox.max_lat - bbox.min_lat
    bbox_size_lon = bbox.max_lon - bbox.min_lon
    
    if bbox_size_lat > MAX_BBOX_SIZE or bbox_size_lon > MAX_BBOX_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"Bounding box too large. Maximum size: {MAX_BBOX_SIZE} degrees"
        )
    
    # Check for reasonable coordinate ranges
    if not (-90 <= bbox.min_lat <= 90) or not (-90 <= bbox.max_lat <= 90):
        raise HTTPException(status_code=400, detail="Invalid latitude range")
    
    if not (-180 <= bbox.min_lon <= 180) or not (-180 <= bbox.max_lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid longitude range")


def validate_feature_types(feature_types: List[str]) -> List[str]:
    """Validate and limit feature types"""
    if not feature_types:
        return []
    
    if len(feature_types) > MAX_FEATURE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Too many feature types. Maximum: {MAX_FEATURE_TYPES}"
        )
    
    # Validate against known feature types
    valid_types = FeatureTypeValidator.validate_feature_types(feature_types)
    return valid_types


def validate_outputs(outputs: List[str]) -> List[str]:
    """Validate output types"""
    valid_outputs = ["report", "plot", "map", "summary", "data", "mach9", "all"]
    invalid_outputs = [output for output in outputs if output not in valid_outputs]
    
    if invalid_outputs:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid output types: {invalid_outputs}. Valid types: {valid_outputs}"
        )
    
    return outputs


def get_mach9_feature_types() -> List[str]:
    """Get Mach9-specific feature types for civil engineering and survey work"""
    return MACH9_FEATURE_TYPES


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with interactive documentation"""
    docs_path = STATIC_DIR / "docs.html"
    if docs_path.exists():
        with open(docs_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>OSM Data Query API</title></head>
            <body>
                <h1>OSM Data Query API</h1>
                <p>API is running! Visit <a href="/docs">/docs</a> for Swagger documentation.</p>
                <p>Visit <a href="/static/docs.html">/static/docs.html</a> for interactive documentation.</p>
            </body>
        </html>
        """)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.post("/query", response_model=OSMDataResponse)
@limiter.limit("20/minute")
async def query_osm_data(request: Request, query_request: OSMQueryRequest):
    """
    Query raw OpenStreetMap data within a specified geographic area.
    
    This endpoint retrieves OSM elements (nodes, ways, relations) for the specified
    feature types within the given bounding box. The data is returned in a structured
    format suitable for further processing and analysis.
    
    **Parameters:**
    - **bbox**: Geographic bounding box coordinates
    - **feature_types**: List of OSM feature types to query (optional, defaults to all)
    
    **Returns:**
    - Raw OSM data including nodes, ways, and relations
    - Element counts and metadata
    - Query timestamp and bounding box information
    
    **Example Use Cases:**
    - Retrieve all buildings in a city block
    - Get highway data for route planning
    - Extract utility infrastructure for engineering surveys
    
    **Rate Limit:** 20 requests per minute
    """
    try:
        # Security validations
        validate_bounding_box(query_request.bbox)
        feature_types = validate_feature_types(query_request.feature_types)
        validate_outputs(query_request.outputs)
        
        # Create OSM query instance
        osm = OSMQuery()
        
        # Query OSM data
        bbox_tuple = (query_request.bbox.min_lat, query_request.bbox.min_lon, 
                     query_request.bbox.max_lat, query_request.bbox.max_lon)
        
        osm_data = osm.query_bounding_box(*bbox_tuple, feature_types=feature_types)
        
        if 'error' in osm_data:
            raise HTTPException(status_code=500, detail=f"OSM API error: {osm_data['error']}")
        
        # Check if response is too large
        total_elements = osm_data.get('total_elements', 0)
        if total_elements > MAX_ELEMENTS_PER_REQUEST:
            raise HTTPException(
                status_code=413, 
                detail=f"Query returned too many elements ({total_elements}). Maximum: {MAX_ELEMENTS_PER_REQUEST}"
            )
        
        # Convert to response format
        response_data = OSMDataResponse(
            total_elements=total_elements,
            nodes=[{"id": node.get('id'), "type": node.get('type'), 
                   "tags": node.get('tags', {}), "geometry": node.get('geometry')} 
                  for node in osm_data.get('nodes', [])],
            ways=[{"id": way.get('id'), "type": way.get('type'), 
                  "tags": way.get('tags', {}), "geometry": way.get('geometry')} 
                 for way in osm_data.get('ways', [])],
            relations=[{"id": rel.get('id'), "type": rel.get('type'), 
                       "tags": rel.get('tags', {}), "geometry": rel.get('geometry')} 
                      for rel in osm_data.get('relations', [])],
            bbox=query_request.bbox,
            feature_types=feature_types,
            query_time=datetime.now().isoformat()
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=APIResponse)
@limiter.limit("10/minute")
async def generate_outputs(request: Request, generate_request: OSMQueryRequest, background_tasks: BackgroundTasks):
    """
    Generate comprehensive OSM data analysis and create multiple output formats.
    
    This endpoint queries OSM data and generates various output formats including
    text reports, visualizations, interactive maps, and specialized engineering reports.
    Files are temporarily stored and can be downloaded via the provided URLs.
    
    **Available Output Types:**
    - **report**: Detailed text analysis of OSM data
    - **plot**: Static visualization plots (PNG format)
    - **map**: Interactive HTML map with Folium
    - **summary**: Summary statistics and charts
    - **data**: Raw JSON data export
    - **mach9**: Specialized engineering and survey report
    - **all**: Generate all available outputs
    
    **Generated Files:**
    - Text reports (TXT format)
    - Interactive maps (HTML format)
    - Static plots (PNG format)
    - JSON data exports
    - CSV rollup reports (with Mach9)
    
    **File Management:**
    - Files are stored temporarily (1 hour)
    - Automatic cleanup after expiration
    - Download URLs provided in response
    
    **Rate Limit:** 10 requests per minute
    """
    try:
        # Security validations
        validate_bounding_box(generate_request.bbox)
        feature_types = validate_feature_types(generate_request.feature_types)
        validate_outputs(generate_request.outputs)
        
        # Create unique session directory
        session_id = str(uuid.uuid4())
        session_dir = OUTPUT_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Query OSM data
        osm = OSMQuery()
        bbox_tuple = (generate_request.bbox.min_lat, generate_request.bbox.min_lon, 
                     generate_request.bbox.max_lat, generate_request.bbox.max_lon)
        
        osm_data = osm.query_bounding_box(*bbox_tuple, feature_types=feature_types)
        
        if 'error' in osm_data:
            raise HTTPException(status_code=500, detail=f"OSM API error: {osm_data['error']}")
        
        if osm_data.get('total_elements', 0) == 0:
            raise HTTPException(status_code=404, detail="No data found in the specified bounding box")
        
        # Check if response is too large
        total_elements = osm_data.get('total_elements', 0)
        if total_elements > MAX_ELEMENTS_PER_REQUEST:
            raise HTTPException(
                status_code=413, 
                detail=f"Query returned too many elements ({total_elements}). Maximum: {MAX_ELEMENTS_PER_REQUEST}"
            )
        
        # Generate requested outputs
        generated_files = []
        outputs = generate_request.outputs if OutputType.ALL not in generate_request.outputs else [
            OutputType.REPORT, OutputType.PLOT, OutputType.MAP, 
            OutputType.SUMMARY, OutputType.DATA
        ]
        
        # Handle Mach9 output - automatically set feature types for civil engineering
        if OutputType.MACH9 in outputs:
            # Override feature types with Mach9-specific ones
            feature_types = get_mach9_feature_types()
            # Re-query with Mach9 feature types
            osm_data = osm.query_bounding_box(*bbox_tuple, feature_types=feature_types)
            if 'error' in osm_data:
                raise HTTPException(status_code=500, detail=f"OSM API error: {osm_data['error']}")
            total_elements = osm_data.get('total_elements', 0)
            if total_elements > MAX_ELEMENTS_PER_REQUEST:
                raise HTTPException(
                    status_code=413, 
                    detail=f"Query returned too many elements ({total_elements}). Maximum: {MAX_ELEMENTS_PER_REQUEST}"
                )
        
        # Generate text report
        if OutputType.REPORT in outputs:
            generator = OSMReportGenerator()
            report_file = session_dir / "osm_report.txt"
            report = generator.generate_report(osm_data, bbox_tuple, str(report_file))
            generated_files.append(f"/files/{session_id}/osm_report.txt")
        
        # Generate raw data JSON
        if OutputType.DATA in outputs:
            json_file = session_dir / "osm_data.json"
            save_json_report(osm_data, str(json_file))
            generated_files.append(f"/files/{session_id}/osm_data.json")
        
        # Generate matplotlib plot
        if OutputType.PLOT in outputs:
            visualizer = OSMVisualizer()
            plot_file = session_dir / "osm_plot.png"
            visualizer.create_matplotlib_plot(osm_data, bbox_tuple, str(plot_file), show_plot=False)
            generated_files.append(f"/files/{session_id}/osm_plot.png")
        
        # Generate interactive map
        if OutputType.MAP in outputs:
            visualizer = OSMVisualizer()
            map_file = session_dir / "osm_map.html"
            visualizer.create_folium_map(osm_data, bbox_tuple, str(map_file))
            generated_files.append(f"/files/{session_id}/osm_map.html")
        
        # Generate summary plots
        if OutputType.SUMMARY in outputs:
            create_summary_plots(osm_data, str(session_dir))
            generated_files.append(f"/files/{session_id}/osm_summary.png")
        
        # Generate Mach9 engineering report
        if OutputType.MACH9 in outputs:
            mach9_generator = Mach9ReportGenerator()
            mach9_report_file = session_dir / "mach9_engineering_report.txt"
            mach9_generator.generate_mach9_report(osm_data, bbox_tuple, str(mach9_report_file))
            generated_files.append(f"/files/{session_id}/mach9_engineering_report.txt")
            
            # Also generate Mach9 JSON data
            mach9_json_file = session_dir / "mach9_data.json"
            save_mach9_json_report(osm_data, str(mach9_json_file))
            generated_files.append(f"/files/{session_id}/mach9_data.json")
            
            # Generate CSV rollup
            csv_rollup_file = session_dir / "feature_rollup.csv"
            mach9_generator.generate_csv_rollup(osm_data, str(csv_rollup_file))
            generated_files.append(f"/files/{session_id}/feature_rollup.csv")
        
        # Schedule cleanup task (delete files after 1 hour)
        background_tasks.add_task(cleanup_session_files, session_dir)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(generated_files)} files successfully",
            data={
                "session_id": session_id,
                "total_elements": total_elements,
                "bbox": generate_request.bbox.dict(),
                "feature_types": feature_types
            },
            files=generated_files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{session_id}/{filename}")
@limiter.limit("30/minute")
async def download_file(request: Request, session_id: str, filename: str):
    """
    Download a specific file from a session
    """
    # Validate session_id format (basic UUID check)
    if len(session_id) != 36 or session_id.count('-') != 4:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    # Validate filename (prevent directory traversal)
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = OUTPUT_DIR / session_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


@app.get("/session/{session_id}/files")
@limiter.limit("30/minute")
async def list_session_files(request: Request, session_id: str):
    """
    List all files in a session
    """
    # Validate session_id format
    if len(session_id) != 36 or session_id.count('-') != 4:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    session_dir = OUTPUT_DIR / session_id
    
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    files = []
    for file_path in session_dir.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "download_url": f"/files/{session_id}/{file_path.name}"
            })
    
    return {"session_id": session_id, "files": files}


@app.get("/feature-types")
@limiter.limit("60/minute")
async def get_available_feature_types(request: Request):
    """
    Get comprehensive list of available OpenStreetMap feature types.
    
    This endpoint returns all supported OSM feature types that can be used in queries.
    The list includes 60+ feature types covering transportation, infrastructure,
    amenities, natural features, and more.
    
    **Feature Categories:**
    - **Transportation**: highway, railway, aeroway, waterway, public_transport
    - **Buildings & Infrastructure**: building, barrier, man_made, power, telecom
    - **Land Use & Natural**: landuse, natural, geological, boundary
    - **Amenities & Services**: amenity, shop, tourism, leisure, sport, healthcare
    - **Administrative & Places**: place, office, craft, military, emergency
    - **Historical & Cultural**: historic, heritage, archaeological_site
    - **Civil Engineering**: tunnel, bridge, embankment, retaining_wall, cycle_barrier
    - **Survey Features**: survey_point, benchmark, marker, culvert, drain, ditch
    - **Utilities**: manhole, utility_pole, street_cabinet, fire_hydrant, pipeline
    - **Safety & Barriers**: noise_barrier, guard_rail, crash_barrier, bollard, fence
    
    **Rate Limit:** 60 requests per minute
    """
    return {"feature_types": AVAILABLE_FEATURE_TYPES}


@app.get("/mach9-feature-types")
@limiter.limit("60/minute")
async def get_mach9_feature_types_endpoint(request: Request):
    """
    Get Mach9-specific feature types optimized for civil engineering and survey work.
    
    This endpoint returns a curated list of OSM feature types specifically selected
    for civil engineering, infrastructure analysis, and survey applications. These
    features are essential for engineering projects, construction planning, and
    infrastructure assessment.
    
    **Mach9 Engineering Categories:**
    - **Transportation Infrastructure**: highway, railway, aeroway, waterway, public_transport
    - **Physical Barriers**: barrier, man_made, building
    - **Utility Infrastructure**: power, telecom, amenity (includes fire hydrants, manholes)
    - **Survey Features**: natural, landuse, boundary
    - **Traffic Control**: traffic_sign, traffic_calming
    - **Surface & Access**: surface, access, kerb
    
    **Additional Civil Engineering Features:**
    - **Infrastructure**: tunnel, bridge, embankment, retaining_wall, cycle_barrier
    - **Survey Points**: survey_point, benchmark, marker, culvert, drain, ditch
    - **Traffic & Lighting**: street_lamp, traffic_signals, bollard, fence, wall, gate
    - **Utilities**: manhole, utility_pole, street_cabinet, fire_hydrant, pipeline
    - **Structures**: tower, mast, antenna, substation, generator, transformer
    - **Safety**: noise_barrier, sound_barrier, guard_rail, crash_barrier
    - **Accessibility**: steps, ramp, elevator, escalator, handrail, railing
    
    **Use Cases:**
    - Civil engineering surveys
    - Infrastructure mapping
    - Transportation planning
    - Utility location and mapping
    - Safety and accessibility analysis
    
    **Rate Limit:** 60 requests per minute
    """
    return {
        "feature_types": get_mach9_feature_types(),
        "description": "Feature types optimized for civil engineering, surveying, and infrastructure analysis",
        "categories": {
            "transportation_infrastructure": ["highway", "railway", "aeroway", "waterway", "public_transport"],
            "physical_barriers": ["barrier", "man_made", "building"],
            "utility_infrastructure": ["power", "telecom", "amenity"],
            "survey_features": ["natural", "landuse", "boundary"],
            "traffic_control": ["traffic_sign", "traffic_calming"],
            "surface_access": ["surface", "access"]
        }
    }


@app.post("/csv-rollup")
@limiter.limit("10/minute")
async def generate_csv_rollup(request: Request, query_request: OSMQueryRequest):
    """
    Generate comprehensive CSV rollup report with detailed feature analysis.
    
    This endpoint creates a detailed CSV report containing feature counts and analysis
    for all OSM elements within the specified area. The CSV includes categorized
    breakdowns of features, element types, and tag summaries.
    
    **CSV Structure:**
    - **Element Types**: Summary of nodes, ways, and relations
    - **Feature Breakdown**: Detailed counts by feature type and value
    - **Tag Summary**: Aggregated tag counts across all elements
    
    **Use Cases:**
    - Data analysis and reporting
    - Feature density analysis
    - Infrastructure inventory
    - Research and academic studies
    - Quality assessment of OSM data
    
    **Output Format:**
    - CSV file with headers: Feature_Type, Feature_Value, Count, Category
    - Organized sections for easy analysis
    - Ready for import into Excel, R, Python, or other analysis tools
    
    **Rate Limit:** 10 requests per minute
    """
    try:
        # Validate inputs
        validate_bounding_box(query_request.bbox)
        validate_feature_types(query_request.feature_types)
        
        bbox_tuple = (
            query_request.bbox.min_lat, query_request.bbox.min_lon,
            query_request.bbox.max_lat, query_request.bbox.max_lon
        )
        
        # Query OSM data
        osm = OSMQuery()
        osm_data = osm.query_bounding_box(*bbox_tuple, feature_types=query_request.feature_types)
        
        if 'error' in osm_data:
            raise HTTPException(status_code=500, detail=f"OSM API error: {osm_data['error']}")
        
        total_elements = osm_data.get('total_elements', 0)
        if total_elements > MAX_ELEMENTS_PER_REQUEST:
            raise HTTPException(
                status_code=413, 
                detail=f"Query returned too many elements ({total_elements}). Maximum: {MAX_ELEMENTS_PER_REQUEST}"
            )
        
        # Generate CSV rollup
        mach9_generator = Mach9ReportGenerator()
        csv_content = mach9_generator.generate_csv_rollup(osm_data)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=osm_feature_rollup.csv"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/examples")
@limiter.limit("60/minute")
async def get_example_requests(request: Request):
    """
    Get example requests for different use cases
    """
    examples = {
        "london_eye": {
            "description": "London Eye, UK - All features",
            "request": {
                "bbox": {
                    "min_lat": 51.5033,
                    "min_lon": -0.1196,
                    "max_lat": 51.5043,
                    "max_lon": -0.1186
                },
                "feature_types": None,
                "outputs": ["report", "plot", "map"]
            }
        },
        "comprehensive_urban": {
            "description": "Comprehensive urban features - buildings, amenities, transportation, utilities",
            "request": {
                "bbox": {
                    "min_lat": 51.5033,
                    "min_lon": -0.1196,
                    "max_lat": 51.5043,
                    "max_lon": -0.1186
                },
                "feature_types": [
                    "highway", "building", "amenity", "shop", "tourism", 
                    "leisure", "natural", "landuse", "power", "telecom",
                    "barrier", "man_made", "railway", "waterway", "place",
                    "office", "craft", "healthcare", "sport", "historic"
                ],
                "outputs": ["report", "plot", "map"]
            }
        },
        "transportation_infrastructure": {
            "description": "Transportation and infrastructure features",
            "request": {
                "bbox": {
                    "min_lat": 51.5033,
                    "min_lon": -0.1196,
                    "max_lat": 51.5043,
                    "max_lon": -0.1186
                },
                "feature_types": [
                    "highway", "railway", "public_transport", "aeroway", 
                    "waterway", "barrier", "man_made", "power", "telecom",
                    "traffic_sign", "traffic_calming", "surface", "access"
                ],
                "outputs": ["plot", "map", "data"]
            }
        },
        "commercial_amenities": {
            "description": "Commercial and amenity features",
            "request": {
                "bbox": {
                    "min_lat": 51.5033,
                    "min_lon": -0.1196,
                    "max_lat": 51.5043,
                    "max_lon": -0.1186
                },
                "feature_types": [
                    "building", "amenity", "shop", "tourism", "leisure", 
                    "sport", "healthcare", "office", "craft", "place",
                    "historic", "heritage", "emergency", "military"
                ],
                "outputs": ["report", "data"]
            }
        },
        "mach9_engineering": {
            "description": "Mach9 Engineering Report - Comprehensive civil engineering and survey features",
            "request": {
                "bbox": {
                    "min_lat": 51.5033,
                    "min_lon": -0.1196,
                    "max_lat": 51.5043,
                    "max_lon": -0.1186
                },
                "feature_types": [
                    "highway", "railway", "aeroway", "waterway", "public_transport",
                    "barrier", "man_made", "building", "power", "telecom", "amenity",
                    "natural", "landuse", "boundary", "traffic_sign", "traffic_calming",
                    "surface", "access", "kerb", "tunnel", "bridge", "embankment",
                    "retaining_wall", "cycle_barrier", "survey_point", "benchmark",
                    "marker", "culvert", "drain", "ditch", "street_lamp", "traffic_signals",
                    "bollard", "fence", "wall", "gate", "manhole", "utility_pole",
                    "street_cabinet", "fire_hydrant", "pipeline", "tower", "mast",
                    "antenna", "substation", "generator", "transformer", "noise_barrier",
                    "sound_barrier", "guard_rail", "crash_barrier", "steps", "ramp",
                    "elevator", "escalator", "handrail", "railing"
                ],
                "outputs": ["mach9"]
            }
        }
    }
    
    return {"examples": examples}


async def cleanup_session_files(session_dir: Path):
    """
    Background task to clean up session files after 1 hour
    """
    import asyncio
    await asyncio.sleep(3600)  # Wait 1 hour
    
    if session_dir.exists():
        shutil.rmtree(session_dir)
        print(f"Cleaned up session directory: {session_dir}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)