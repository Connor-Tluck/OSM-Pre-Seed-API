"""
Mach9 Engineering & Survey Report Generator
Specialized report for civil engineering and survey work
"""

from collections import defaultdict
from typing import Dict, List, Any, Tuple
import json
import csv
from io import StringIO


class Mach9ReportGenerator:
    """Generate specialized reports for civil engineering and survey work"""
    
    def __init__(self):
        # Define engineering-specific feature categories
        self.transportation_objects = {
            'highway': ['traffic_signals', 'stop', 'give_way', 'traffic_sign'],
            'barrier': ['bollard', 'fence', 'wall', 'gate', 'chain', 'cable_barrier'],
            'man_made': ['street_lamp', 'street_cabinet', 'utility_pole'],
            'amenity': ['fire_station', 'police', 'emergency_services']
        }
        
        self.utility_objects = {
            'amenity': ['fire_hydrant', 'waste_disposal', 'recycling'],
            'man_made': ['manhole', 'utility_pole', 'pipeline', 'tower', 'mast'],
            'power': ['line', 'pole', 'tower', 'substation', 'generator'],
            'telecom': ['pole', 'tower', 'mast', 'antenna']
        }
        
        self.civil_engineering_features = {
            'man_made': ['bridge', 'tunnel', 'embankment', 'cutting', 'pier', 'breakwater', 'pipeline', 'tower', 'mast', 'substation', 'generator', 'transformer'],
            'waterway': ['drain', 'ditch', 'stream', 'river', 'canal', 'culvert'],
            'natural': ['water', 'wetland', 'coastline'],
            'highway': ['bridleway', 'footway', 'cycleway', 'path', 'track', 'steps', 'ramp'],
            'kerb': ['yes', 'raised', 'lowered', 'flush', 'rolled', 'no'],
            'barrier': ['retaining_wall', 'noise_barrier', 'sound_barrier', 'guard_rail', 'crash_barrier', 'cycle_barrier', 'bollard', 'fence', 'wall', 'gate'],
            'amenity': ['fire_hydrant', 'waste_disposal', 'recycling', 'benchmark'],
            'power': ['line', 'pole', 'tower', 'substation', 'generator', 'transformer'],
            'telecom': ['pole', 'tower', 'mast', 'antenna']
        }
        
        self.survey_control_points = {
            'man_made': ['survey_point', 'benchmark', 'marker'],
            'amenity': ['benchmark']
        }
        
        self.drainage_structures = {
            'man_made': ['manhole', 'drain', 'gutter', 'culvert'],
            'waterway': ['drain', 'ditch', 'stream'],
            'highway': ['drain']
        }
        
        self.traffic_control = {
            'highway': ['traffic_signals', 'stop', 'give_way', 'traffic_sign'],
            'barrier': ['bollard', 'fence', 'wall', 'gate'],
            'man_made': ['street_lamp', 'traffic_signals']
        }

    def generate_mach9_report(self, osm_data: Dict[str, Any], bbox: Tuple[float, float, float, float], output_file: str = None) -> str:
        """Generate a Mach9 engineering and survey report"""
        
        min_lat, min_lon, max_lat, max_lon = bbox
        area = (max_lat - min_lat) * (max_lon - min_lon)
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("MACH9 ENGINEERING & SURVEY REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Bounding box information
        report_lines.append("BOUNDING BOX:")
        report_lines.append(f"  Min Lat: {min_lat:.6f}")
        report_lines.append(f"  Min Lon: {min_lon:.6f}")
        report_lines.append(f"  Max Lat: {max_lat:.6f}")
        report_lines.append(f"  Max Lon: {max_lon:.6f}")
        report_lines.append(f"  Area: {area:.6f} square degrees")
        report_lines.append("")
        
        # Summary statistics
        total_elements = osm_data.get('total_elements', 0)
        nodes = osm_data.get('nodes', [])
        ways = osm_data.get('ways', [])
        relations = osm_data.get('relations', [])
        
        report_lines.append("SUMMARY STATISTICS:")
        report_lines.append(f"  Total Elements: {total_elements}")
        report_lines.append(f"  Nodes: {len(nodes)}")
        report_lines.append(f"  Ways: {len(ways)}")
        report_lines.append(f"  Relations: {len(relations)}")
        report_lines.append("")
        
        # Engineering feature analysis
        report_lines.append("ENGINEERING FEATURE ANALYSIS:")
        report_lines.append("-" * 40)
        report_lines.append("")
        
        # Analyze features by category
        transportation_count = self._analyze_transportation_objects(nodes, ways, relations)
        utility_count = self._analyze_utility_objects(nodes, ways, relations)
        civil_count = self._analyze_civil_engineering_features(nodes, ways, relations)
        survey_count = self._analyze_survey_control_points(nodes, ways, relations)
        drainage_count = self._analyze_drainage_structures(nodes, ways, relations)
        
        # Summary counts
        report_lines.append("TRANSPORTATION OBJECTS:")
        report_lines.append(f"  Traffic Signs: {transportation_count.get('traffic_signs', 0)}")
        report_lines.append(f"  Traffic Lights: {transportation_count.get('traffic_lights', 0)}")
        report_lines.append(f"  Bollards: {transportation_count.get('bollards', 0)}")
        report_lines.append(f"  Street Lights: {transportation_count.get('street_lights', 0)}")
        report_lines.append("")
        
        report_lines.append("UTILITY OBJECTS:")
        report_lines.append(f"  Manholes: {utility_count.get('manholes', 0)}")
        report_lines.append(f"  Utility Infrastructure: {utility_count.get('utility_poles', 0) + utility_count.get('utility_cabinets', 0)}")
        report_lines.append(f"  Fire Hydrants: {utility_count.get('fire_hydrants', 0)}")
        report_lines.append("")
        
        report_lines.append("CIVIL ENGINEERING FEATURES:")
        report_lines.append(f"  Bridges: {civil_count.get('bridges', 0)}")
        report_lines.append(f"  Tunnels: {civil_count.get('tunnels', 0)}")
        report_lines.append(f"  Water Structures: {civil_count.get('water_structures', 0)}")
        report_lines.append(f"  Kerbs/Curbs: {civil_count.get('kerbs', 0)}")
        report_lines.append(f"  Retaining Walls: {civil_count.get('retaining_walls', 0)}")
        report_lines.append(f"  Noise Barriers: {civil_count.get('noise_barriers', 0)}")
        report_lines.append(f"  Guard Rails: {civil_count.get('guard_rails', 0)}")
        report_lines.append(f"  Steps/Ramps: {civil_count.get('steps_ramps', 0)}")
        report_lines.append("")
        
        # Detailed feature breakdown
        report_lines.append("=" * 80)
        report_lines.append("DETAILED FEATURE BREAKDOWN")
        report_lines.append("=" * 80)
        
        # Transportation objects detail
        report_lines.append("TRANSPORTATION OBJECTS:")
        self._add_detailed_breakdown(report_lines, nodes, ways, relations, self.transportation_objects)
        report_lines.append("")
        
        # Utility objects detail
        report_lines.append("UTILITY OBJECTS:")
        self._add_detailed_breakdown(report_lines, nodes, ways, relations, self.utility_objects)
        report_lines.append("")
        
        # Civil engineering features detail
        report_lines.append("CIVIL ENGINEERING FEATURES:")
        self._add_detailed_breakdown(report_lines, nodes, ways, relations, self.civil_engineering_features)
        report_lines.append("")
        
        # Survey control points
        report_lines.append("SURVEY CONTROL POINTS:")
        survey_features = self._find_features_by_category(nodes, ways, relations, self.survey_control_points)
        if survey_features:
            for feature_type, features in survey_features.items():
                if features:
                    report_lines.append(f"  {feature_type.title()}: {len(features)} found")
                    for feature in features[:3]:  # Show first 3
                        name = feature.get('tags', {}).get('name', 'Unnamed')
                        element_type = feature.get('type', 'unknown')
                        report_lines.append(f"    - {name} ({element_type})")
        else:
            report_lines.append("  No features found in this category.")
        report_lines.append("")
        
        # Infrastructure analysis
        report_lines.append("=" * 80)
        report_lines.append("INFRASTRUCTURE ANALYSIS")
        report_lines.append("=" * 80)
        
        # Highway infrastructure
        highway_types = defaultdict(int)
        for way in ways:
            tags = way.get('tags', {})
            if 'highway' in tags:
                highway_types[tags['highway']] += 1
        
        if highway_types:
            report_lines.append("HIGHWAY INFRASTRUCTURE:")
            for hw_type, count in sorted(highway_types.items()):
                report_lines.append(f"  {hw_type}: {count} segments")
            report_lines.append("")
        
        # Barrier infrastructure
        barrier_types = defaultdict(int)
        for element in nodes + ways:
            tags = element.get('tags', {})
            if 'barrier' in tags:
                barrier_types[tags['barrier']] += 1
        
        if barrier_types:
            report_lines.append("BARRIER INFRASTRUCTURE:")
            for barrier_type, count in sorted(barrier_types.items()):
                report_lines.append(f"  {barrier_type}: {count} features")
            report_lines.append("")
        
        # Man-made infrastructure
        man_made_types = defaultdict(int)
        for element in nodes + ways:
            tags = element.get('tags', {})
            if 'man_made' in tags:
                man_made_types[tags['man_made']] += 1
        
        if man_made_types:
            report_lines.append("MAN-MADE INFRASTRUCTURE:")
            for mm_type, count in sorted(man_made_types.items()):
                report_lines.append(f"  {mm_type}: {count} features")
            report_lines.append("")
        
        # Survey and engineering recommendations
        report_lines.append("=" * 80)
        report_lines.append("SURVEY & ENGINEERING RECOMMENDATIONS")
        report_lines.append("=" * 80)
        
        recommendations = []
        
        if total_elements < 50:
            recommendations.append("1. Low data density - consider expanding survey area")
        
        if survey_count.get('total', 0) == 0:
            recommendations.append("2. Add survey control points for accurate positioning")
        
        if utility_count.get('manholes', 0) == 0:
            recommendations.append("3. Verify underground utility locations")
        
        if transportation_count.get('traffic_signals', 0) == 0:
            recommendations.append("4. Check for traffic control devices")
        
        if not recommendations:
            recommendations.append("1. Data density appears adequate for engineering analysis")
            recommendations.append("2. Consider additional survey points for critical infrastructure")
        
        for rec in recommendations:
            report_lines.append(rec)
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        report_content = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        return report_content

    def _analyze_transportation_objects(self, nodes: List, ways: List, relations: List) -> Dict[str, int]:
        """Analyze transportation-related objects"""
        counts = defaultdict(int)
        
        for element in nodes + ways + relations:
            tags = element.get('tags', {})
            
            # Traffic signals and signs
            if tags.get('highway') == 'traffic_signals':
                counts['traffic_lights'] += 1
            elif tags.get('highway') in ['stop', 'give_way'] or tags.get('traffic_sign'):
                counts['traffic_signs'] += 1
            
            # Bollards and barriers
            if tags.get('barrier') == 'bollard':
                counts['bollards'] += 1
            
            # Street lights
            if tags.get('man_made') == 'street_lamp' or tags.get('highway') == 'street_lamp':
                counts['street_lights'] += 1
        
        return dict(counts)

    def _analyze_utility_objects(self, nodes: List, ways: List, relations: List) -> Dict[str, int]:
        """Analyze utility-related objects"""
        counts = defaultdict(int)
        
        for element in nodes + ways + relations:
            tags = element.get('tags', {})
            
            # Manholes
            if tags.get('man_made') == 'manhole':
                counts['manholes'] += 1
            
            # Utility poles and cabinets
            if tags.get('man_made') in ['utility_pole', 'street_cabinet']:
                if tags.get('man_made') == 'utility_pole':
                    counts['utility_poles'] += 1
                else:
                    counts['utility_cabinets'] += 1
            
            # Fire hydrants
            if tags.get('amenity') == 'fire_hydrant':
                counts['fire_hydrants'] += 1
        
        return dict(counts)

    def _analyze_civil_engineering_features(self, nodes: List, ways: List, relations: List) -> Dict[str, int]:
        """Analyze civil engineering features"""
        counts = defaultdict(int)
        
        for element in nodes + ways + relations:
            tags = element.get('tags', {})
            
            # Bridges
            if tags.get('man_made') == 'bridge' or tags.get('bridge'):
                counts['bridges'] += 1
            
            # Tunnels
            if tags.get('tunnel') or tags.get('man_made') == 'tunnel':
                counts['tunnels'] += 1
            
            # Water structures
            if tags.get('waterway') or tags.get('natural') == 'water':
                counts['water_structures'] += 1
            
            # Kerbs/Curbs
            if tags.get('kerb'):
                counts['kerbs'] += 1
            
            # Retaining walls
            if tags.get('barrier') == 'retaining_wall':
                counts['retaining_walls'] += 1
            
            # Noise barriers
            if tags.get('barrier') in ['noise_barrier', 'sound_barrier']:
                counts['noise_barriers'] += 1
            
            # Guard rails
            if tags.get('barrier') in ['guard_rail', 'crash_barrier']:
                counts['guard_rails'] += 1
            
            # Steps and ramps
            if tags.get('highway') in ['steps', 'ramp']:
                counts['steps_ramps'] += 1
        
        return dict(counts)

    def _analyze_survey_control_points(self, nodes: List, ways: List, relations: List) -> Dict[str, int]:
        """Analyze survey control points"""
        counts = defaultdict(int)
        
        for element in nodes + ways + relations:
            tags = element.get('tags', {})
            
            if tags.get('man_made') in ['survey_point', 'benchmark', 'marker']:
                counts['survey_points'] += 1
            elif tags.get('amenity') == 'benchmark':
                counts['benchmarks'] += 1
        
        counts['total'] = counts['survey_points'] + counts['benchmarks']
        return dict(counts)

    def _analyze_drainage_structures(self, nodes: List, ways: List, relations: List) -> Dict[str, int]:
        """Analyze drainage structures"""
        counts = defaultdict(int)
        
        for element in nodes + ways + relations:
            tags = element.get('tags', {})
            
            if tags.get('man_made') == 'manhole':
                counts['manholes'] += 1
            elif tags.get('waterway') in ['drain', 'ditch']:
                counts['drains'] += 1
        
        return dict(counts)

    def _add_detailed_breakdown(self, report_lines: List[str], nodes: List, ways: List, relations: List, category_dict: Dict):
        """Add detailed breakdown for a category"""
        features = self._find_features_by_category(nodes, ways, relations, category_dict)
        
        for feature_type, feature_list in features.items():
            if feature_list:
                report_lines.append(f"  {feature_type.title()} ({len(feature_list)} found):")
                for feature in feature_list[:3]:  # Show first 3
                    name = feature.get('tags', {}).get('name', 'Unnamed')
                    element_type = feature.get('type', 'unknown')
                    report_lines.append(f"    - {name} ({element_type})")
                    # Show relevant tags
                    tags = feature.get('tags', {})
                    relevant_tags = {k: v for k, v in tags.items() if k in ['highway', 'barrier', 'man_made', 'amenity', 'power', 'waterway']}
                    if relevant_tags:
                        tag_str = ", ".join([f"{k}={v}" for k, v in relevant_tags.items()])
                        report_lines.append(f"      Tags: {tag_str}")

    def _find_features_by_category(self, nodes: List, ways: List, relations: List, category_dict: Dict) -> Dict[str, List]:
        """Find features that match a category dictionary"""
        features = defaultdict(list)
        
        for element in nodes + ways + relations:
            tags = element.get('tags', {})
            
            for main_key, sub_values in category_dict.items():
                if main_key in tags:
                    tag_value = tags[main_key]
                    if tag_value in sub_values:
                        features[f"{main_key}_{tag_value}"].append(element)
        
        return dict(features)

    def generate_csv_rollup(self, osm_data: Dict[str, Any], output_file: str = None) -> str:
        """Generate CSV rollup with feature counts"""
        
        # Initialize counters
        feature_counts = defaultdict(int)
        tag_counts = defaultdict(int)
        element_type_counts = defaultdict(int)
        
        # Process all elements
        for element_type in ['nodes', 'ways', 'relations']:
            elements = osm_data.get(element_type, [])
            element_type_counts[element_type] = len(elements)
            
            for element in elements:
                tags = element.get('tags', {})
                
                # Count main feature types
                for key, value in tags.items():
                    if key in ['highway', 'railway', 'aeroway', 'waterway', 'public_transport',
                              'building', 'barrier', 'man_made', 'power', 'telecom',
                              'landuse', 'natural', 'boundary', 'amenity', 'tunnel', 'bridge']:
                        feature_counts[f"{key}_{value}"] += 1
                        tag_counts[key] += 1
                    elif key in ['kerb', 'surface', 'access', 'traffic_sign', 'traffic_calming']:
                        feature_counts[f"{key}_{value}"] += 1
                        tag_counts[key] += 1
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Feature_Type', 'Feature_Value', 'Count', 'Category'])
        
        # Write element type summary
        writer.writerow(['ELEMENT_TYPES', '', '', 'SUMMARY'])
        for element_type, count in element_type_counts.items():
            writer.writerow([element_type.upper(), '', count, 'ELEMENT_COUNT'])
        
        writer.writerow(['', '', '', ''])  # Empty row
        
        # Write main feature counts
        writer.writerow(['MAIN_FEATURES', '', '', 'FEATURE_BREAKDOWN'])
        for feature, count in sorted(feature_counts.items()):
            if '_' in feature:
                main_type, sub_type = feature.split('_', 1)
                writer.writerow([main_type, sub_type, count, 'FEATURE_COUNT'])
            else:
                writer.writerow([feature, '', count, 'FEATURE_COUNT'])
        
        writer.writerow(['', '', '', ''])  # Empty row
        
        # Write tag summary
        writer.writerow(['TAG_SUMMARY', '', '', 'TAG_COUNTS'])
        for tag, count in sorted(tag_counts.items()):
            writer.writerow([tag, '', count, 'TAG_COUNT'])
        
        csv_content = output.getvalue()
        output.close()
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(csv_content)
        
        return csv_content


def save_mach9_json_report(osm_data: Dict[str, Any], output_file: str):
    """Save Mach9-specific data as JSON"""
    mach9_data = {
        "report_type": "mach9_engineering_survey",
        "summary": {
            "total_elements": osm_data.get('total_elements', 0),
            "nodes": len(osm_data.get('nodes', [])),
            "ways": len(osm_data.get('ways', [])),
            "relations": len(osm_data.get('relations', []))
        },
        "engineering_features": {
            "transportation_objects": [],
            "utility_objects": [],
            "civil_engineering_features": [],
            "drainage_structures": []
        },
        "raw_data": osm_data
    }
    
    # Filter and categorize features for Mach9
    generator = Mach9ReportGenerator()
    
    # Transportation objects
    for element in osm_data.get('nodes', []) + osm_data.get('ways', []) + osm_data.get('relations', []):
        tags = element.get('tags', {})
        if (tags.get('highway') in ['traffic_signals', 'stop', 'give_way'] or 
            tags.get('barrier') == 'bollard' or 
            tags.get('man_made') == 'street_lamp'):
            mach9_data["engineering_features"]["transportation_objects"].append(element)
    
    # Utility objects
    for element in osm_data.get('nodes', []) + osm_data.get('ways', []) + osm_data.get('relations', []):
        tags = element.get('tags', {})
        if (tags.get('man_made') in ['manhole', 'utility_pole', 'street_cabinet'] or 
            tags.get('amenity') == 'fire_hydrant'):
            mach9_data["engineering_features"]["utility_objects"].append(element)
    
    # Civil engineering features
    for element in osm_data.get('nodes', []) + osm_data.get('ways', []) + osm_data.get('relations', []):
        tags = element.get('tags', {})
        if (tags.get('man_made') == 'bridge' or 
            tags.get('waterway') or 
            tags.get('natural') == 'water'):
            mach9_data["engineering_features"]["civil_engineering_features"].append(element)
    
    # Drainage structures
    for element in osm_data.get('nodes', []) + osm_data.get('ways', []) + osm_data.get('relations', []):
        tags = element.get('tags', {})
        if (tags.get('man_made') == 'manhole' or 
            tags.get('waterway') in ['drain', 'ditch']):
            mach9_data["engineering_features"]["drainage_structures"].append(element)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mach9_data, f, indent=2, ensure_ascii=False)