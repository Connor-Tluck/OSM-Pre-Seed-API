"""
OSM Data Visualizer Module
Creates visualizations of OSM vector data using matplotlib and folium
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import LineCollection, PatchCollection
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import folium
from folium import plugins
import json


class OSMVisualizer:
    def __init__(self):
        self.colors = {
            'building': '#8B4513',
            'highway': '#FF0000', 
            'waterway': '#0000FF',
            'natural': '#228B22',
            'amenity': '#FFD700',
            'leisure': '#FF69B4',
            'shop': '#FFA500',
            'tourism': '#9370DB',
            'landuse': '#90EE90',
            'default': '#808080'
        }
    
    def create_matplotlib_plot(self, osm_data: Dict[str, List[Dict]], 
                             bbox: Tuple[float, float, float, float],
                             output_file: str = "osm_plot.png",
                             show_plot: bool = True) -> None:
        """
        Create a matplotlib visualization of OSM data
        
        Args:
            osm_data: Parsed OSM data
            bbox: Bounding box (min_lat, min_lon, max_lat, max_lon)
            output_file: Output file path
            show_plot: Whether to display the plot
        """
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        min_lat, min_lon, max_lat, max_lon = bbox
        
        # Set up the plot bounds
        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)
        ax.set_aspect('equal')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title('OSM Data Visualization')
        ax.grid(True, alpha=0.3)
        
        # Plot ways (lines and polygons)
        ways = osm_data.get('ways', [])
        self._plot_ways(ax, ways)
        
        # Plot nodes (points)
        nodes = osm_data.get('nodes', [])
        self._plot_nodes(ax, nodes)
        
        # Add legend
        self._add_legend(ax)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Matplotlib plot saved to: {output_file}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def create_folium_map(self, osm_data: Dict[str, List[Dict]], 
                         bbox: Tuple[float, float, float, float],
                         output_file: str = "osm_map.html") -> None:
        """
        Create an interactive Folium map of OSM data
        
        Args:
            osm_data: Parsed OSM data
            bbox: Bounding box (min_lat, min_lon, max_lat, max_lon)
            output_file: Output HTML file path
        """
        min_lat, min_lon, max_lat, max_lon = bbox
        
        # Calculate center point
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles='OpenStreetMap'
        )
        
        # Add bounding box
        folium.Rectangle(
            bounds=[[min_lat, min_lon], [max_lat, max_lon]],
            color='red',
            weight=2,
            fill=False,
            popup='Query Bounding Box'
        ).add_to(m)
        
        # Add ways
        ways = osm_data.get('ways', [])
        self._add_ways_to_folium(m, ways)
        
        # Add nodes
        nodes = osm_data.get('nodes', [])
        self._add_nodes_to_folium(m, nodes)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save map
        m.save(output_file)
        print(f"Interactive map saved to: {output_file}")
    
    def _plot_ways(self, ax, ways: List[Dict]) -> None:
        """Plot ways (lines and polygons) on matplotlib axes"""
        for way in ways:
            geometry = way.get('geometry')
            if not geometry:
                continue
                
            geom_type = geometry.get('type')
            coords = geometry.get('coordinates', [])
            
            if not coords:
                continue
            
            # Get color based on tags
            color = self._get_color_for_way(way)
            
            if geom_type == 'LineString':
                # Plot as line
                lons, lats = zip(*coords)
                ax.plot(lons, lats, color=color, linewidth=1, alpha=0.7)
                
            elif geom_type == 'Polygon':
                # Plot as polygon
                if coords and len(coords[0]) > 2:
                    lons, lats = zip(*coords[0])
                    polygon = patches.Polygon(list(zip(lons, lats)), 
                                            facecolor=color, 
                                            edgecolor='black',
                                            alpha=0.5,
                                            linewidth=0.5)
                    ax.add_patch(polygon)
    
    def _plot_nodes(self, ax, nodes: List[Dict]) -> None:
        """Plot nodes (points) on matplotlib axes"""
        if not nodes:
            return
            
        # Group nodes by type for better visualization
        node_types = defaultdict(list)
        
        for node in nodes:
            tags = node.get('tags', {})
            node_type = self._get_node_type(tags)
            node_types[node_type].append((node.get('lon'), node.get('lat')))
        
        # Plot each type with different markers
        markers = ['o', 's', '^', 'v', 'D', 'p', '*', 'h']
        for i, (node_type, coords) in enumerate(node_types.items()):
            if coords:
                lons, lats = zip(*coords)
                color = self.colors.get(node_type, self.colors['default'])
                marker = markers[i % len(markers)]
                ax.scatter(lons, lats, c=color, marker=marker, s=20, alpha=0.7, label=node_type)
    
    def _add_ways_to_folium(self, m, ways: List[Dict]) -> None:
        """Add ways to Folium map"""
        for way in ways:
            geometry = way.get('geometry')
            if not geometry:
                continue
                
            geom_type = geometry.get('type')
            coords = geometry.get('coordinates', [])
            
            if not coords:
                continue
            
            # Get color and popup info
            color = self._get_color_for_way(way)
            popup_text = self._create_popup_text(way)
            
            if geom_type == 'LineString':
                # Add as polyline
                folium.PolyLine(
                    locations=[[lat, lon] for lon, lat in coords],
                    color=color,
                    weight=2,
                    opacity=0.7,
                    popup=popup_text
                ).add_to(m)
                
            elif geom_type == 'Polygon':
                # Add as polygon
                if coords and len(coords[0]) > 2:
                    folium.Polygon(
                        locations=[[lat, lon] for lon, lat in coords[0]],
                        color=color,
                        weight=2,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.3,
                        popup=popup_text
                    ).add_to(m)
    
    def _add_nodes_to_folium(self, m, nodes: List[Dict]) -> None:
        """Add nodes to Folium map"""
        for node in nodes:
            lat = node.get('lat')
            lon = node.get('lon')
            tags = node.get('tags', {})
            
            if lat is None or lon is None:
                continue
            
            # Get color and popup
            node_type = self._get_node_type(tags)
            color = self.colors.get(node_type, self.colors['default'])
            popup_text = self._create_popup_text(node)
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=3,
                popup=popup_text,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
    
    def _get_color_for_way(self, way: Dict) -> str:
        """Get color for a way based on its tags"""
        tags = way.get('tags', {})
        
        # Check for specific feature types
        for tag_key in ['building', 'highway', 'waterway', 'natural', 'amenity', 
                       'leisure', 'shop', 'tourism', 'landuse']:
            if tag_key in tags:
                return self.colors.get(tag_key, self.colors['default'])
        
        return self.colors['default']
    
    def _get_node_type(self, tags: Dict) -> str:
        """Get node type based on tags"""
        for tag_key in ['amenity', 'shop', 'tourism', 'natural', 'leisure']:
            if tag_key in tags:
                return tag_key
        return 'default'
    
    def _create_popup_text(self, element: Dict) -> str:
        """Create popup text for an element"""
        element_id = element.get('id', 'Unknown')
        element_type = element.get('type', 'Unknown')
        tags = element.get('tags', {})
        
        popup = f"<b>{element_type.title()} {element_id}</b><br>"
        
        if tags:
            popup += "<br>Tags:<br>"
            for key, value in list(tags.items())[:5]:  # Show first 5 tags
                popup += f"• {key}: {value}<br>"
            if len(tags) > 5:
                popup += f"... and {len(tags) - 5} more"
        else:
            popup += "No tags"
        
        return popup
    
    def _add_legend(self, ax) -> None:
        """Add legend to matplotlib plot"""
        legend_elements = []
        for feature_type, color in self.colors.items():
            if feature_type != 'default':
                legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                                markerfacecolor=color, markersize=8, 
                                                label=feature_type.title()))
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))


def create_summary_plots(osm_data: Dict[str, List[Dict]], output_dir: str = ".") -> None:
    """Create summary plots showing data distribution"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Element type distribution
    element_types = ['Nodes', 'Ways', 'Relations']
    element_counts = [
        len(osm_data.get('nodes', [])),
        len(osm_data.get('ways', [])),
        len(osm_data.get('relations', []))
    ]
    
    ax1.bar(element_types, element_counts, color=['blue', 'green', 'red'])
    ax1.set_title('Element Type Distribution')
    ax1.set_ylabel('Count')
    
    # Plot 2: Feature type distribution (top 10)
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
        top_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        features, counts = zip(*top_features)
        ax2.barh(range(len(features)), counts)
        ax2.set_yticks(range(len(features)))
        ax2.set_yticklabels(features, fontsize=8)
        ax2.set_title('Top 10 Feature Types')
        ax2.set_xlabel('Count')
    
    # Plot 3: Geometry type distribution
    geometry_counts = {'Point': len(osm_data.get('nodes', []))}
    ways = osm_data.get('ways', [])
    for way in ways:
        if way.get('geometry'):
            geom_type = way['geometry'].get('type', 'Unknown')
            geometry_counts[geom_type] = geometry_counts.get(geom_type, 0) + 1
    
    if geometry_counts:
        ax3.pie(geometry_counts.values(), labels=geometry_counts.keys(), autopct='%1.1f%%')
        ax3.set_title('Geometry Type Distribution')
    
    # Plot 4: Data quality metrics
    total_elements = sum(element_counts)
    tagged_elements = 0
    for element_type in ['nodes', 'ways', 'relations']:
        elements = osm_data.get(element_type, [])
        tagged_elements += sum(1 for elem in elements if elem.get('tags'))
    
    quality_metrics = {
        'Tagged Elements': tagged_elements,
        'Untagged Elements': total_elements - tagged_elements
    }
    
    ax4.bar(quality_metrics.keys(), quality_metrics.values(), color=['green', 'orange'])
    ax4.set_title('Data Quality: Tagged vs Untagged')
    ax4.set_ylabel('Count')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/osm_summary.png", dpi=300, bbox_inches='tight')
    print(f"Summary plots saved to: {output_dir}/osm_summary.png")
    plt.show()


if __name__ == "__main__":
    # Test the visualizer
    from osm_query import OSMQuery, get_sample_bounding_box
    
    print("Testing OSM Visualizer...")
    
    # Get sample data
    osm = OSMQuery()
    bbox = get_sample_bounding_box()
    data = osm.query_bounding_box(*bbox)
    
    # Create visualizations
    visualizer = OSMVisualizer()
    visualizer.create_matplotlib_plot(data, bbox, show_plot=False)
    visualizer.create_folium_map(data, bbox)
    create_summary_plots(data)
    
    print("Visualization tests completed!")