"""
OSM API Query Module
Queries OpenStreetMap Overpass API for vector data within a bounding box
"""

import requests
import json
from typing import Dict, List, Tuple, Any
import time


class OSMQuery:
    def __init__(self):
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        self.timeout = 25
        
    def query_bounding_box(self, 
                          min_lat: float, 
                          min_lon: float, 
                          max_lat: float, 
                          max_lon: float,
                          feature_types: List[str] = None) -> Dict[str, Any]:
        """
        Query OSM data for a bounding box
        
        Args:
            min_lat: Minimum latitude
            min_lon: Minimum longitude  
            max_lat: Maximum latitude
            max_lon: Maximum longitude
            feature_types: List of OSM feature types to query (default: common features)
            
        Returns:
            Dictionary containing nodes, ways, and relations
        """
        if feature_types is None:
            feature_types = [
                "amenity", "building", "highway", "landuse", "leisure", 
                "natural", "shop", "tourism", "waterway", "railway",
                "aeroway", "barrier", "boundary", "power", "public_transport"
            ]
        
        # Build the Overpass QL query
        query_parts = []
        for feature_type in feature_types:
            query_parts.append(f'  nwr["{feature_type}"]({min_lat},{min_lon},{max_lat},{max_lon});')
        
        query = f"""
[out:json][timeout:{self.timeout}];
(
{chr(10).join(query_parts)}
);
out geom;
"""
        
        print(f"Querying OSM for bounding box: ({min_lat}, {min_lon}) to ({max_lat}, {max_lon})")
        print(f"Feature types: {', '.join(feature_types)}")
        
        try:
            response = requests.post(self.overpass_url, data=query, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            print(f"Retrieved {len(data.get('elements', []))} elements from OSM")
            
            return self._parse_osm_data(data)
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying OSM API: {e}")
            return {"nodes": [], "ways": [], "relations": [], "error": str(e)}
    
    def _parse_osm_data(self, data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Parse OSM data into structured format"""
        elements = data.get('elements', [])
        
        nodes = []
        ways = []
        relations = []
        
        for element in elements:
            element_type = element.get('type')
            
            if element_type == 'node':
                nodes.append(self._parse_node(element))
            elif element_type == 'way':
                ways.append(self._parse_way(element))
            elif element_type == 'relation':
                relations.append(self._parse_relation(element))
        
        return {
            "nodes": nodes,
            "ways": ways, 
            "relations": relations,
            "total_elements": len(elements)
        }
    
    def _parse_node(self, node: Dict) -> Dict:
        """Parse a node element"""
        return {
            "id": node.get('id'),
            "type": "node",
            "lat": node.get('lat'),
            "lon": node.get('lon'),
            "tags": node.get('tags', {}),
            "geometry": {
                "type": "Point",
                "coordinates": [node.get('lon'), node.get('lat')]
            }
        }
    
    def _parse_way(self, way: Dict) -> Dict:
        """Parse a way element"""
        geometry = None
        
        if 'geometry' in way:
            # LineString or Polygon
            coords = [[point['lon'], point['lat']] for point in way['geometry']]
            if len(coords) > 2 and coords[0] == coords[-1]:
                geometry = {
                    "type": "Polygon",
                    "coordinates": [coords]
                }
            else:
                geometry = {
                    "type": "LineString", 
                    "coordinates": coords
                }
        elif 'nodes' in way:
            # Just node references
            geometry = {
                "type": "LineString",
                "coordinates": way['nodes']  # Will need to be resolved later
            }
        
        return {
            "id": way.get('id'),
            "type": "way",
            "tags": way.get('tags', {}),
            "nodes": way.get('nodes', []),
            "geometry": geometry
        }
    
    def _parse_relation(self, relation: Dict) -> Dict:
        """Parse a relation element"""
        return {
            "id": relation.get('id'),
            "type": "relation", 
            "tags": relation.get('tags', {}),
            "members": relation.get('members', []),
            "geometry": None  # Relations are complex, simplified for POC
        }


def get_sample_bounding_box() -> Tuple[float, float, float, float]:
    """
    Get a sample bounding box for testing (Central Park, NYC)
    Returns: (min_lat, min_lon, max_lat, max_lon)
    """
    # Central Park, NYC
    return (40.7648, -73.9808, 40.8006, -73.9490)


if __name__ == "__main__":
    # Test the OSM query
    osm = OSMQuery()
    bbox = get_sample_bounding_box()
    
    print("Testing OSM Query...")
    result = osm.query_bounding_box(*bbox)
    
    print(f"\nResults:")
    print(f"Nodes: {len(result['nodes'])}")
    print(f"Ways: {len(result['ways'])}")
    print(f"Relations: {len(result['relations'])}")
    print(f"Total: {result['total_elements']}")