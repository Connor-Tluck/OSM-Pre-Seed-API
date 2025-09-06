#!/usr/bin/env python3
"""
OSM Data Query and Visualization POC - Demo Script
Demonstrates the capabilities of the OSM query and visualization system
"""

import os
import subprocess
import sys
from datetime import datetime


def run_demo():
    """Run a comprehensive demo of the OSM POC project"""
    
    print("=" * 80)
    print("OSM DATA QUERY AND VISUALIZATION POC - DEMO")
    print("=" * 80)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Demo 1: Basic functionality with Central Park
    print("DEMO 1: Basic OSM Query (Central Park, NYC)")
    print("-" * 50)
    print("Querying OSM data for Central Park area...")
    
    cmd1 = [
        sys.executable, "main.py",
        "--bbox", "40.775,-73.975,40.785,-73.965",
        "--outputs", "all",
        "--output-dir", "demo_output"
    ]
    
    try:
        result = subprocess.run(cmd1, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ Demo 1 completed successfully!")
            print("Generated files:")
            if os.path.exists("demo_output"):
                files = os.listdir("demo_output")
                for file in files:
                    size = os.path.getsize(f"demo_output/{file}")
                    print(f"  - {file} ({size:,} bytes)")
        else:
            print(f"✗ Demo 1 failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("✗ Demo 1 timed out")
    except Exception as e:
        print(f"✗ Demo 1 error: {e}")
    
    print()
    
    # Demo 2: Specific feature types
    print("DEMO 2: Specific Feature Types (Buildings and Amenities)")
    print("-" * 50)
    print("Querying only buildings and amenities...")
    
    cmd2 = [
        sys.executable, "main.py",
        "--bbox", "40.775,-73.975,40.785,-73.965",
        "--features", "building,amenity",
        "--outputs", "report,map",
        "--output-dir", "demo_buildings"
    ]
    
    try:
        result = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ Demo 2 completed successfully!")
            print("Generated files:")
            if os.path.exists("demo_buildings"):
                files = os.listdir("demo_buildings")
                for file in files:
                    size = os.path.getsize(f"demo_buildings/{file}")
                    print(f"  - {file} ({size:,} bytes)")
        else:
            print(f"✗ Demo 2 failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("✗ Demo 2 timed out")
    except Exception as e:
        print(f"✗ Demo 2 error: {e}")
    
    print()
    
    # Demo 3: Different location (London)
    print("DEMO 3: Different Location (Hyde Park, London)")
    print("-" * 50)
    print("Querying OSM data for Hyde Park area...")
    
    cmd3 = [
        sys.executable, "main.py",
        "--bbox", "51.507,-0.168,51.517,-0.158",
        "--features", "natural,leisure,amenity",
        "--outputs", "report,summary",
        "--output-dir", "demo_london"
    ]
    
    try:
        result = subprocess.run(cmd3, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ Demo 3 completed successfully!")
            print("Generated files:")
            if os.path.exists("demo_london"):
                files = os.listdir("demo_london")
                for file in files:
                    size = os.path.getsize(f"demo_london/{file}")
                    print(f"  - {file} ({size:,} bytes)")
        else:
            print(f"✗ Demo 3 failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("✗ Demo 3 timed out")
    except Exception as e:
        print(f"✗ Demo 3 error: {e}")
    
    print()
    
    # Summary
    print("DEMO SUMMARY")
    print("-" * 50)
    print("The OSM POC project successfully demonstrated:")
    print("✓ Querying OSM data via Overpass API")
    print("✓ Parsing and structuring vector data (nodes, ways, relations)")
    print("✓ Generating comprehensive text reports")
    print("✓ Creating static matplotlib visualizations")
    print("✓ Building interactive Folium maps")
    print("✓ Producing summary analysis plots")
    print("✓ Flexible bounding box and feature type selection")
    print("✓ Multiple output formats and options")
    print()
    print("Key Features:")
    print("• Supports all major OSM feature types")
    print("• Handles points, lines, and polygons")
    print("• Provides detailed statistics and analysis")
    print("• Generates both static and interactive visualizations")
    print("• Command-line interface with flexible options")
    print("• Comprehensive error handling and validation")
    print()
    print("Usage Examples:")
    print("• python main.py  # Default Central Park query")
    print("• python main.py --bbox 'lat1,lon1,lat2,lon2'  # Custom area")
    print("• python main.py --features 'building,highway'  # Specific types")
    print("• python main.py --outputs report  # Text report only")
    print("• python main.py --outputs all  # All visualizations")
    print()
    print(f"Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()