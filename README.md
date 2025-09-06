# OSM Data Query & Analysis API

A comprehensive FastAPI-based service for querying, analyzing, and visualizing OpenStreetMap (OSM) data within specified geographic areas. Designed for data preseeding in machine learning annotation workflows, civil engineering, urban planning, GIS applications, and research.

## Key Features

- **Comprehensive OSM Coverage**: Support for 91+ feature types including civil engineering and survey features
- **Raw Data Queries**: Retrieve OSM nodes, ways, and relations for any geographic area
- **Data Preseeding**: Generate comprehensive datasets for machine learning annotation workflows
- **Data Visualization**: Create interactive maps, static plots, and summary visualizations
- **CSV Export**: Export detailed feature rollups for analysis
- **REST API**: FastAPI-based web service with comprehensive documentation
- **Interactive Documentation**: Custom web interface for easy testing
- **Security Features**: Rate limiting, input validation, and CORS protection

## Available Feature Types

The API supports a comprehensive range of OSM feature types organized into categories:

### Transportation
- `highway`, `railway`, `aeroway`, `waterway`, `aerialway`, `public_transport`
- `traffic_sign`, `traffic_calming`

### Buildings & Infrastructure
- `building`, `man_made`, `barrier`, `power`, `telecom`, `amenity`

### Natural Features
- `natural`, `landuse`, `geological`, `boundary`

### Commercial & Services
- `shop`, `tourism`, `leisure`, `sport`, `healthcare`, `office`, `craft`

### Administrative
- `place`, `military`, `emergency`, `historic`, `heritage`

### Civil Engineering & Survey
- `tunnel`, `bridge`, `embankment`, `retaining_wall`, `cycle_barrier`
- `survey_point`, `benchmark`, `marker`, `culvert`, `drain`, `ditch`
- `street_lamp`, `traffic_signals`, `bollard`, `fence`, `wall`, `gate`
- `manhole`, `utility_pole`, `street_cabinet`, `fire_hydrant`, `pipeline`
- `tower`, `mast`, `antenna`, `substation`, `generator`, `transformer`
- `noise_barrier`, `sound_barrier`, `guard_rail`, `crash_barrier`
- `steps`, `ramp`, `elevator`, `escalator`, `handrail`, `railing`

### Drainage & Inlet Features
- `inlet`, `inlet_grate`, `inlet_kerb_grate`, `kerb_opening`
- `storm_drain`, `catch_basin`

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Connor-Tluck/OSM-Pre-Seed-API.git
cd OSM-Pre-Seed-API
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Start the API server**:
```bash
python start_api.py
```

The API will be available at:
- **Interactive Documentation**: http://localhost:8000/
- **Swagger API Docs**: http://localhost:8000/docs
- **ReDoc API Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Usage

### Interactive Web Interface

Visit http://localhost:8000/ for a user-friendly interface where you can:
- Set bounding box coordinates
- Select feature types from comprehensive categories
- Choose output formats
- Generate reports and visualizations
- Download CSV rollup reports

### API Endpoints

#### Query Raw OSM Data
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lat": 51.5033,
      "min_lon": -0.1196,
      "max_lat": 51.5043,
      "max_lon": -0.1186
    },
    "feature_types": ["highway", "building", "amenity"],
    "outputs": ["data"]
  }'
```

#### Generate Reports and Visualizations
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lat": 51.5033,
      "min_lon": -0.1196,
      "max_lat": 51.5043,
      "max_lon": -0.1186
    },
    "feature_types": ["highway", "building", "amenity"],
    "outputs": ["report", "plot", "map"]
  }'
```

#### Download CSV Rollup Report
```bash
curl -X POST "http://localhost:8000/csv-rollup" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lat": 51.5033,
      "min_lon": -0.1196,
      "max_lat": 51.5043,
      "max_lon": -0.1186
    },
    "feature_types": ["highway", "building", "amenity"]
  }' \
  --output feature_rollup.csv
```

### Available Endpoints

- **POST /query** - Query OSM data without generating files
- **POST /generate** - Generate OSM data and create outputs
- **POST /csv-rollup** - Generate CSV rollup report
- **GET /download/{session_id}/{filename}** - Download generated files
- **GET /session/{session_id}/files** - List files in a session
- **GET /feature-types** - Get all available OSM feature types
- **GET /examples** - Get example requests
- **GET /health** - Health check endpoint

## Data Preseeding for Machine Learning

This API is designed to support machine learning annotation workflows by providing comprehensive datasets that help annotators understand where features are likely to be located. Key benefits include:

### Pre-annotation Analysis
- **Feature Density Mapping**: Understand the distribution of different feature types across geographic areas
- **Quality Assessment**: Identify areas with rich OSM data coverage for reliable annotations
- **Feature Correlation**: Discover relationships between different feature types in the same area

### Annotation Workflow Support
- **Bounding Box Optimization**: Select optimal areas for annotation based on feature density
- **Feature Type Prioritization**: Focus annotation efforts on the most relevant feature types
- **Data Validation**: Cross-reference annotations with OSM data for quality assurance

### Dataset Preparation
- **Stratified Sampling**: Ensure balanced representation of different feature types
- **Geographic Distribution**: Maintain geographic diversity in training datasets
- **Feature Completeness**: Identify gaps in feature coverage for targeted data collection

## Output Formats

### Text Reports
- Comprehensive statistics and analysis
- Feature type breakdowns
- Quality metrics and data distribution

### Visualizations
- **Static Plots**: Matplotlib-based data visualizations
- **Interactive Maps**: Folium-based maps with feature layers
- **Summary Plots**: Data distribution and quality analysis

### Data Exports
- **JSON**: Raw OSM data in structured format
- **CSV**: Feature rollup reports with detailed counts
- **Engineering Reports**: Specialized analysis for infrastructure features

## Security Features

- **Rate Limiting**: Configurable limits per endpoint
- **Input Validation**: Bounding box size and coordinate validation
- **CORS Protection**: Configurable cross-origin restrictions
- **File Management**: Automatic cleanup of temporary files
- **Error Handling**: Comprehensive error responses

## Project Structure

```
OSM-Pre-Seed-API/
├── api.py                    # Main FastAPI application
├── api_models.py             # Pydantic models and feature types
├── osm_query.py              # OSM Overpass API integration
├── report_generator.py       # Text report generation
├── mach9_report_generator.py # Engineering analysis reports
├── visualizer.py             # Visualization modules
├── start_api.py              # Server startup script
├── static/
│   └── docs.html             # Interactive documentation
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Rate Limits

- **Query endpoints**: 20 requests/minute
- **Generate endpoints**: 10 requests/minute
- **File downloads**: 30 requests/minute
- **Information endpoints**: 60 requests/minute

## Use Cases

### Machine Learning Data Preparation
- Pre-annotation dataset analysis
- Feature distribution mapping
- Training data quality assessment
- Annotation workflow optimization

### Civil Engineering
- Infrastructure surveys and mapping
- Utility location and planning
- Transportation network analysis
- Drainage system assessment

### Urban Planning
- City infrastructure analysis
- Accessibility studies
- Public space planning
- Development impact assessment

### GIS Applications
- Data collection and validation
- Spatial analysis and mapping
- Research and academic studies
- Environmental impact studies

## Configuration

### Environment Variables
- `MAX_BBOX_SIZE`: Maximum bounding box size (default: 0.1 degrees)
- `MAX_FEATURE_TYPES`: Maximum feature types per request (default: 20)
- `MAX_ELEMENTS_PER_REQUEST`: Maximum OSM elements per request (default: 50,000)

### Customization
- Modify `api_models.py` to add new feature types
- Update report generators for custom analysis
- Customize visualizations in `visualizer.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the API documentation at http://localhost:8000/docs
- Review the interactive documentation at http://localhost:8000/

## Version History

- **v1.0.0**: Initial release with comprehensive OSM data querying
- **v1.1.0**: Added engineering reports and CSV rollup functionality
- **v1.2.0**: Enhanced with 91+ feature types and improved documentation