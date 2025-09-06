"""
Report Generator Module
Generates text reports from OSM data
"""

from typing import Dict, List, Any
from collections import Counter, defaultdict
import json
from datetime import datetime


class OSMReportGenerator:
    def __init__(self):
        self.report_data = {}
    
    def generate_report(self, osm_data: Dict[str, List[Dict]], 
                       bbox: tuple, 
                       output_file: str = None) -> str:
        """
        Generate a comprehensive text report from OSM data
        
        Args:
            osm_data: Parsed OSM data from OSMQuery
            bbox: Bounding box tuple (min_lat, min_lon, max_lat, max_lon)
            output_file: Optional file path to save report
            
        Returns:
            Formatted report string
        """
        self.report_data = osm_data
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("OSM DATA REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Bounding Box: {bbox[0]:.6f}, {bbox[1]:.6f} to {bbox[2]:.6f}, {bbox[3]:.6f}")
        report_lines.append("")
        
        # Summary statistics
        report_lines.extend(self._generate_summary())
        report_lines.append("")
        
        # Feature type analysis
        report_lines.extend(self._generate_feature_analysis())
        report_lines.append("")
        
        # Detailed breakdowns
        report_lines.extend(self._generate_detailed_breakdown())
        report_lines.append("")
        
        # Sample data
        report_lines.extend(self._generate_sample_data())
        
        report_text = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"Report saved to: {output_file}")
        
        return report_text
    
    def _generate_summary(self) -> List[str]:
        """Generate summary statistics"""
        lines = []
        lines.append("SUMMARY STATISTICS")
        lines.append("-" * 40)
        
        total_elements = self.report_data.get('total_elements', 0)
        nodes = len(self.report_data.get('nodes', []))
        ways = len(self.report_data.get('ways', []))
        relations = len(self.report_data.get('relations', []))
        
        lines.append(f"Total Elements: {total_elements}")
        lines.append(f"  - Nodes (Points): {nodes}")
        lines.append(f"  - Ways (Lines/Polygons): {ways}")
        lines.append(f"  - Relations: {relations}")
        lines.append("")
        
        # Geometry type breakdown
        geometry_types = self._count_geometry_types()
        if geometry_types:
            lines.append("Geometry Types:")
            for geom_type, count in geometry_types.items():
                lines.append(f"  - {geom_type}: {count}")
        
        return lines
    
    def _generate_feature_analysis(self) -> List[str]:
        """Generate feature type analysis"""
        lines = []
        lines.append("FEATURE TYPE ANALYSIS")
        lines.append("-" * 40)
        
        # Count features by primary tag
        feature_counts = self._count_features_by_tag()
        
        if feature_counts:
            lines.append("Top Feature Types:")
            for feature_type, count in feature_counts.most_common(20):
                lines.append(f"  {feature_type}: {count}")
        else:
            lines.append("No tagged features found")
        
        return lines
    
    def _generate_detailed_breakdown(self) -> List[str]:
        """Generate detailed breakdown by element type"""
        lines = []
        lines.append("DETAILED BREAKDOWN")
        lines.append("-" * 40)
        
        # Nodes breakdown
        nodes = self.report_data.get('nodes', [])
        if nodes:
            lines.append(f"NODES ({len(nodes)} total):")
            node_tags = self._count_tags_in_elements(nodes)
            for tag, count in node_tags.most_common(10):
                lines.append(f"  {tag}: {count}")
            lines.append("")
        
        # Ways breakdown  
        ways = self.report_data.get('ways', [])
        if ways:
            lines.append(f"WAYS ({len(ways)} total):")
            way_tags = self._count_tags_in_elements(ways)
            for tag, count in way_tags.most_common(10):
                lines.append(f"  {tag}: {count}")
            lines.append("")
        
        # Relations breakdown
        relations = self.report_data.get('relations', [])
        if relations:
            lines.append(f"RELATIONS ({len(relations)} total):")
            relation_tags = self._count_tags_in_elements(relations)
            for tag, count in relation_tags.most_common(10):
                lines.append(f"  {tag}: {count}")
        
        return lines
    
    def _generate_sample_data(self) -> List[str]:
        """Generate sample data examples"""
        lines = []
        lines.append("SAMPLE DATA")
        lines.append("-" * 40)
        
        # Sample nodes
        nodes = self.report_data.get('nodes', [])
        if nodes:
            lines.append("Sample Nodes:")
            for i, node in enumerate(nodes[:3]):
                lines.append(f"  Node {i+1}:")
                lines.append(f"    ID: {node.get('id')}")
                lines.append(f"    Location: {node.get('lat'):.6f}, {node.get('lon'):.6f}")
                if node.get('tags'):
                    lines.append(f"    Tags: {dict(list(node['tags'].items())[:3])}")
                lines.append("")
        
        # Sample ways
        ways = self.report_data.get('ways', [])
        if ways:
            lines.append("Sample Ways:")
            for i, way in enumerate(ways[:3]):
                lines.append(f"  Way {i+1}:")
                lines.append(f"    ID: {way.get('id')}")
                lines.append(f"    Nodes: {len(way.get('nodes', []))}")
                if way.get('tags'):
                    lines.append(f"    Tags: {dict(list(way['tags'].items())[:3])}")
                if way.get('geometry'):
                    geom_type = way['geometry'].get('type', 'Unknown')
                    lines.append(f"    Geometry: {geom_type}")
                lines.append("")
        
        return lines
    
    def _count_geometry_types(self) -> Dict[str, int]:
        """Count geometry types in the data"""
        geometry_counts = Counter()
        
        # Count from nodes (all points)
        nodes = self.report_data.get('nodes', [])
        geometry_counts['Point'] = len(nodes)
        
        # Count from ways
        ways = self.report_data.get('ways', [])
        for way in ways:
            if way.get('geometry'):
                geom_type = way['geometry'].get('type', 'Unknown')
                geometry_counts[geom_type] += 1
        
        return dict(geometry_counts)
    
    def _count_features_by_tag(self) -> Counter:
        """Count features by their primary tag"""
        feature_counts = Counter()
        
        # Count from all elements
        for element_type in ['nodes', 'ways', 'relations']:
            elements = self.report_data.get(element_type, [])
            for element in elements:
                tags = element.get('tags', {})
                # Get the first meaningful tag
                for tag_key, tag_value in tags.items():
                    if tag_key in ['amenity', 'building', 'highway', 'landuse', 'leisure', 
                                 'natural', 'shop', 'tourism', 'waterway', 'railway']:
                        feature_counts[f"{tag_key}={tag_value}"] += 1
                        break
        
        return feature_counts
    
    def _count_tags_in_elements(self, elements: List[Dict]) -> Counter:
        """Count tag occurrences in a list of elements"""
        tag_counts = Counter()
        
        for element in elements:
            tags = element.get('tags', {})
            for tag_key in tags.keys():
                tag_counts[tag_key] += 1
        
        return tag_counts


def save_json_report(osm_data: Dict[str, List[Dict]], output_file: str):
    """Save raw OSM data as JSON for further analysis"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(osm_data, f, indent=2, ensure_ascii=False)
    print(f"Raw data saved to: {output_file}")


if __name__ == "__main__":
    # Test the report generator
    from osm_query import OSMQuery, get_sample_bounding_box
    
    print("Testing Report Generator...")
    
    # Get sample data
    osm = OSMQuery()
    bbox = get_sample_bounding_box()
    data = osm.query_bounding_box(*bbox)
    
    # Generate report
    generator = OSMReportGenerator()
    report = generator.generate_report(data, bbox, "test_report.txt")
    
    print("\nGenerated Report:")
    print(report[:500] + "..." if len(report) > 500 else report)