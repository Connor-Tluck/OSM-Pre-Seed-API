#!/usr/bin/env python3
"""
OSM Data Query and Visualization POC
Main script that orchestrates the entire workflow
"""

import argparse
import sys
import os
from typing import Tuple, List
import json

from osm_query import OSMQuery, get_sample_bounding_box
from report_generator import OSMReportGenerator, save_json_report
from visualizer import OSMVisualizer, create_summary_plots


def parse_bbox(bbox_str: str) -> Tuple[float, float, float, float]:
    """
    Parse bounding box string in format: min_lat,min_lon,max_lat,max_lon
    
    Args:
        bbox_str: Comma-separated bounding box string
        
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    try:
        coords = [float(x.strip()) for x in bbox_str.split(',')]
        if len(coords) != 4:
            raise ValueError("Bounding box must have exactly 4 coordinates")
        
        min_lat, min_lon, max_lat, max_lon = coords
        
        # Validate coordinates
        if not (-90 <= min_lat <= 90) or not (-90 <= max_lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= min_lon <= 180) or not (-180 <= max_lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if min_lat >= max_lat:
            raise ValueError("min_lat must be less than max_lat")
        if min_lon >= max_lon:
            raise ValueError("min_lon must be less than max_lon")
        
        return min_lat, min_lon, max_lat, max_lon
        
    except ValueError as e:
        print(f"Error parsing bounding box: {e}")
        print("Format should be: min_lat,min_lon,max_lat,max_lon")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="OSM Data Query and Visualization POC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default Central Park bounding box
  python main.py
  
  # Specify custom bounding box
  python main.py --bbox "40.7648,-73.9808,40.8006,-73.9490"
  
  # Query specific feature types only
  python main.py --features "building,highway,amenity"
  
  # Generate only text report
  python main.py --outputs report
  
  # Generate all outputs
  python main.py --outputs all
        """
    )
    
    parser.add_argument(
        '--bbox', 
        type=str,
        help='Bounding box as "min_lat,min_lon,max_lat,max_lon" (default: Central Park, NYC)'
    )
    
    parser.add_argument(
        '--features',
        type=str,
        help='Comma-separated list of OSM feature types to query (default: all common types)'
    )
    
    parser.add_argument(
        '--outputs',
        type=str,
        choices=['report', 'plot', 'map', 'summary', 'all'],
        default='all',
        help='Which outputs to generate (default: all)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory for generated files (default: output)'
    )
    
    parser.add_argument(
        '--show-plot',
        action='store_true',
        help='Display matplotlib plot (default: False)'
    )
    
    args = parser.parse_args()
    
    # Set up output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Parse bounding box
    if args.bbox:
        bbox = parse_bbox(args.bbox)
        print(f"Using custom bounding box: {bbox}")
    else:
        bbox = get_sample_bounding_box()
        print(f"Using default bounding box (Central Park, NYC): {bbox}")
    
    # Parse feature types
    feature_types = None
    if args.features:
        feature_types = [f.strip() for f in args.features.split(',')]
        print(f"Querying feature types: {feature_types}")
    else:
        print("Querying all common feature types")
    
    print("\n" + "="*60)
    print("OSM DATA QUERY AND VISUALIZATION POC")
    print("="*60)
    
    # Step 1: Query OSM data
    print("\n1. Querying OSM data...")
    osm = OSMQuery()
    osm_data = osm.query_bounding_box(*bbox, feature_types=feature_types)
    
    if 'error' in osm_data:
        print(f"Error occurred: {osm_data['error']}")
        sys.exit(1)
    
    total_elements = osm_data.get('total_elements', 0)
    if total_elements == 0:
        print("No data found in the specified bounding box. Try a different area or feature types.")
        sys.exit(1)
    
    print(f"✓ Retrieved {total_elements} elements from OSM")
    
    # Step 2: Generate outputs based on user selection
    outputs = [args.outputs] if args.outputs != 'all' else ['report', 'plot', 'map', 'summary']
    
    if 'report' in outputs:
        print("\n2. Generating text report...")
        generator = OSMReportGenerator()
        report_file = os.path.join(args.output_dir, "osm_report.txt")
        report = generator.generate_report(osm_data, bbox, report_file)
        print(f"✓ Text report generated: {report_file}")
        
        # Also save raw JSON data
        json_file = os.path.join(args.output_dir, "osm_data.json")
        save_json_report(osm_data, json_file)
        print(f"✓ Raw data saved: {json_file}")
    
    if 'plot' in outputs:
        print("\n3. Creating matplotlib visualization...")
        visualizer = OSMVisualizer()
        plot_file = os.path.join(args.output_dir, "osm_plot.png")
        visualizer.create_matplotlib_plot(
            osm_data, bbox, plot_file, show_plot=args.show_plot
        )
        print(f"✓ Matplotlib plot generated: {plot_file}")
    
    if 'map' in outputs:
        print("\n4. Creating interactive map...")
        visualizer = OSMVisualizer()
        map_file = os.path.join(args.output_dir, "osm_map.html")
        visualizer.create_folium_map(osm_data, bbox, map_file)
        print(f"✓ Interactive map generated: {map_file}")
    
    if 'summary' in outputs:
        print("\n5. Creating summary plots...")
        create_summary_plots(osm_data, args.output_dir)
        print(f"✓ Summary plots generated in: {args.output_dir}")
    
    # Final summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Bounding Box: {bbox[0]:.6f}, {bbox[1]:.6f} to {bbox[2]:.6f}, {bbox[3]:.6f}")
    print(f"Total Elements: {total_elements}")
    print(f"  - Nodes: {len(osm_data.get('nodes', []))}")
    print(f"  - Ways: {len(osm_data.get('ways', []))}")
    print(f"  - Relations: {len(osm_data.get('relations', []))}")
    print(f"Output Directory: {args.output_dir}")
    print(f"Generated Files:")
    
    for output in outputs:
        if output == 'report':
            print(f"  - osm_report.txt (text report)")
            print(f"  - osm_data.json (raw data)")
        elif output == 'plot':
            print(f"  - osm_plot.png (matplotlib visualization)")
        elif output == 'map':
            print(f"  - osm_map.html (interactive map)")
        elif output == 'summary':
            print(f"  - osm_summary.png (summary plots)")
    
    print("\n✓ OSM data query and visualization completed successfully!")
    
    # Show quick stats from the report
    if 'report' in outputs:
        print("\nQuick Stats:")
        feature_counts = {}
        for element_type in ['nodes', 'ways', 'relations']:
            elements = osm_data.get(element_type, [])
            for element in elements:
                tags = element.get('tags', {})
                for tag_key in ['amenity', 'building', 'highway', 'landuse', 'leisure', 
                               'natural', 'shop', 'tourism', 'waterway']:
                    if tag_key in tags:
                        feature_type = f"{tag_key}={tags[tag_key]}"
                        feature_counts[feature_type] = feature_counts.get(feature_type, 0) + 1
                        break
        
        if feature_counts:
            top_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print("Top 5 feature types:")
            for feature, count in top_features:
                print(f"  - {feature}: {count}")


if __name__ == "__main__":
    main()