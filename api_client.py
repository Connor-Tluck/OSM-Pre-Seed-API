#!/usr/bin/env python3
"""
API Client for OSM POC FastAPI
Demonstrates how to use the API endpoints
"""

import requests
import json
import time
from typing import Dict, Any, List


class OSMAPIClient:
    """Client for OSM POC API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_feature_types(self) -> List[str]:
        """Get available feature types"""
        response = self.session.get(f"{self.base_url}/feature-types")
        response.raise_for_status()
        return response.json()["feature_types"]
    
    def get_examples(self) -> Dict[str, Any]:
        """Get example requests"""
        response = self.session.get(f"{self.base_url}/examples")
        response.raise_for_status()
        return response.json()
    
    def query_osm_data(self, bbox: Dict[str, float], feature_types: List[str] = None) -> Dict[str, Any]:
        """
        Query OSM data without generating files
        
        Args:
            bbox: Bounding box dict with min_lat, min_lon, max_lat, max_lon
            feature_types: List of feature types to query
        """
        payload = {
            "bbox": bbox,
            "feature_types": feature_types,
            "outputs": ["data"]  # Just query, don't generate files
        }
        
        response = self.session.post(f"{self.base_url}/query", json=payload)
        response.raise_for_status()
        return response.json()
    
    def generate_outputs(self, bbox: Dict[str, float], feature_types: List[str] = None, 
                        outputs: List[str] = None) -> Dict[str, Any]:
        """
        Generate OSM data and create outputs
        
        Args:
            bbox: Bounding box dict with min_lat, min_lon, max_lat, max_lon
            feature_types: List of feature types to query
            outputs: List of output types to generate
        """
        if outputs is None:
            outputs = ["report", "plot", "map"]
        
        payload = {
            "bbox": bbox,
            "feature_types": feature_types,
            "outputs": outputs
        }
        
        response = self.session.post(f"{self.base_url}/generate", json=payload)
        response.raise_for_status()
        return response.json()
    
    def download_file(self, session_id: str, filename: str, save_path: str = None) -> str:
        """
        Download a file from a session
        
        Args:
            session_id: Session ID from generate_outputs response
            filename: Name of file to download
            save_path: Local path to save file (default: current directory)
        """
        if save_path is None:
            save_path = filename
        
        response = self.session.get(f"{self.base_url}/download/{session_id}/{filename}")
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return save_path
    
    def list_session_files(self, session_id: str) -> Dict[str, Any]:
        """List all files in a session"""
        response = self.session.get(f"{self.base_url}/session/{session_id}/files")
        response.raise_for_status()
        return response.json()


def demo_api_usage():
    """Demonstrate API usage"""
    print("OSM POC API Client Demo")
    print("=" * 50)
    
    # Initialize client
    client = OSMAPIClient()
    
    try:
        # Health check
        print("1. Health Check...")
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Version: {health['version']}")
        
        # Get available feature types
        print("\n2. Available Feature Types...")
        feature_types = client.get_feature_types()
        print(f"   Found {len(feature_types)} feature types")
        print(f"   Examples: {feature_types[:5]}")
        
        # Get examples
        print("\n3. Example Requests...")
        examples = client.get_examples()
        for name, example in examples["examples"].items():
            print(f"   {name}: {example['description']}")
        
        # Test query (small bounding box)
        print("\n4. Testing OSM Query...")
        bbox = {
            "min_lat": 40.775,
            "min_lon": -73.975,
            "max_lat": 40.785,
            "max_lon": -73.965
        }
        
        query_result = client.query_osm_data(bbox, ["building", "amenity"])
        print(f"   Retrieved {query_result['total_elements']} elements")
        print(f"   Nodes: {len(query_result['nodes'])}")
        print(f"   Ways: {len(query_result['ways'])}")
        print(f"   Relations: {len(query_result['relations'])}")
        
        # Test file generation
        print("\n5. Testing File Generation...")
        generate_result = client.generate_outputs(
            bbox, 
            ["building", "amenity"], 
            ["report", "plot"]
        )
        
        print(f"   Session ID: {generate_result['data']['session_id']}")
        print(f"   Generated {len(generate_result['files'])} files:")
        for file_url in generate_result['files']:
            print(f"     - {file_url}")
        
        # List session files
        print("\n6. Session Files...")
        session_id = generate_result['data']['session_id']
        files_info = client.list_session_files(session_id)
        for file_info in files_info['files']:
            print(f"   {file_info['filename']} ({file_info['size']} bytes)")
        
        # Download a file
        print("\n7. Downloading Report...")
        if files_info['files']:
            first_file = files_info['files'][0]
            downloaded_path = client.download_file(
                session_id, 
                first_file['filename'], 
                f"downloaded_{first_file['filename']}"
            )
            print(f"   Downloaded: {downloaded_path}")
        
        print("\n✓ API Demo completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"✗ API Error: {e}")
        print("Make sure the API server is running: python api.py")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_specific_endpoints():
    """Test specific API endpoints"""
    client = OSMAPIClient()
    
    print("\nTesting Specific Endpoints")
    print("-" * 30)
    
    # Test different bounding boxes
    test_cases = [
        {
            "name": "Central Park (small)",
            "bbox": {"min_lat": 40.775, "min_lon": -73.975, "max_lat": 40.785, "max_lon": -73.965},
            "features": ["building", "amenity"],
            "outputs": ["report"]
        },
        {
            "name": "Transportation only",
            "bbox": {"min_lat": 40.775, "min_lon": -73.975, "max_lat": 40.785, "max_lon": -73.965},
            "features": ["highway", "railway"],
            "outputs": ["plot", "map"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        try:
            result = client.generate_outputs(
                test_case['bbox'],
                test_case['features'],
                test_case['outputs']
            )
            print(f"  ✓ Generated {len(result['files'])} files")
            print(f"  ✓ Session: {result['data']['session_id']}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")


if __name__ == "__main__":
    demo_api_usage()
    test_specific_endpoints()