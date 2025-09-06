#!/usr/bin/env python3
"""
Example Usage of OSM POC Components
Shows how to use individual modules programmatically
"""

from osm_query import OSMQuery, get_sample_bounding_box
from report_generator import OSMReportGenerator, save_json_report
from visualizer import OSMVisualizer, create_summary_plots


def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===")
    
    # 1. Query OSM data
    osm = OSMQuery()
    bbox = get_sample_bounding_box()  # Central Park, NYC
    data = osm.query_bounding_box(*bbox)
    
    print(f"Retrieved {data['total_elements']} elements")
    print(f"  - Nodes: {len(data['nodes'])}")
    print(f"  - Ways: {len(data['ways'])}")
    print(f"  - Relations: {len(data['relations'])}")
    
    return data, bbox


def example_custom_query():
    """Custom query example"""
    print("\n=== Custom Query Example ===")
    
    # Custom bounding box (smaller area)
    custom_bbox = (40.775, -73.975, 40.785, -73.965)
    
    # Query specific feature types only
    osm = OSMQuery()
    data = osm.query_bounding_box(
        *custom_bbox,
        feature_types=['building', 'amenity', 'highway']
    )
    
    print(f"Custom query retrieved {data['total_elements']} elements")
    return data, custom_bbox


def example_report_generation(data, bbox):
    """Report generation example"""
    print("\n=== Report Generation Example ===")
    
    # Generate text report
    generator = OSMReportGenerator()
    report = generator.generate_report(data, bbox)
    
    # Print first 500 characters of report
    print("Report preview:")
    print(report[:500] + "..." if len(report) > 500 else report)
    
    # Save to file
    generator.generate_report(data, bbox, "example_report.txt")
    print("Full report saved to: example_report.txt")
    
    # Save raw JSON data
    save_json_report(data, "example_data.json")
    print("Raw data saved to: example_data.json")


def example_visualization(data, bbox):
    """Visualization example"""
    print("\n=== Visualization Example ===")
    
    visualizer = OSMVisualizer()
    
    # Create matplotlib plot
    visualizer.create_matplotlib_plot(
        data, bbox, "example_plot.png", show_plot=False
    )
    print("Matplotlib plot saved to: example_plot.png")
    
    # Create interactive map
    visualizer.create_folium_map(data, bbox, "example_map.html")
    print("Interactive map saved to: example_map.html")
    
    # Create summary plots
    create_summary_plots(data, ".")
    print("Summary plots saved to: example_summary.png")


def example_data_analysis(data):
    """Data analysis example"""
    print("\n=== Data Analysis Example ===")
    
    # Count feature types
    feature_counts = {}
    for element_type in ['nodes', 'ways', 'relations']:
        elements = data.get(element_type, [])
        for element in elements:
            tags = element.get('tags', {})
            for tag_key in ['amenity', 'building', 'highway', 'natural']:
                if tag_key in tags:
                    feature_type = f"{tag_key}={tags[tag_key]}"
                    feature_counts[feature_type] = feature_counts.get(feature_type, 0) + 1
                    break
    
    # Show top features
    if feature_counts:
        top_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        print("Top 10 feature types:")
        for feature, count in top_features:
            print(f"  {feature}: {count}")
    
    # Geometry analysis
    geometry_counts = {'Point': len(data.get('nodes', []))}
    ways = data.get('ways', [])
    for way in ways:
        if way.get('geometry'):
            geom_type = way['geometry'].get('type', 'Unknown')
            geometry_counts[geom_type] = geometry_counts.get(geom_type, 0) + 1
    
    print(f"\nGeometry distribution:")
    for geom_type, count in geometry_counts.items():
        print(f"  {geom_type}: {count}")


def main():
    """Run all examples"""
    print("OSM POC - Example Usage")
    print("=" * 50)
    
    try:
        # Basic usage
        data, bbox = example_basic_usage()
        
        # Custom query
        custom_data, custom_bbox = example_custom_query()
        
        # Report generation
        example_report_generation(custom_data, custom_bbox)
        
        # Visualization
        example_visualization(custom_data, custom_bbox)
        
        # Data analysis
        example_data_analysis(custom_data)
        
        print("\n=== Example Usage Complete ===")
        print("Generated files:")
        print("  - example_report.txt")
        print("  - example_data.json")
        print("  - example_plot.png")
        print("  - example_map.html")
        print("  - example_summary.png")
        
    except Exception as e:
        print(f"Error in example: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()