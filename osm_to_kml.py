#!/usr/bin/env python3
"""
OSM Airport to KML Converter - Enhanced Version
Queries OpenStreetMap Overpass API for airport data including buildings, vegetation, etc.

Usage: python osm_to_kml.py CYHZ
"""

import sys
import json
import requests
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def query_overpass(icao_code):
    """
    Query Overpass API for comprehensive airport data
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Comprehensive Overpass QL query for all airport features
    query = f"""
    [out:json][timeout:45];
    (
      // Find airport by ICAO code
      relation["aeroway"="aerodrome"]["icao"="{icao_code}"];
      way["aeroway"="aerodrome"]["icao"="{icao_code}"];
      node["aeroway"="aerodrome"]["icao"="{icao_code}"];
    )->.airport;
    
    // Get all features within or near the airport
    (
      // AEROWAY FEATURES
      way["aeroway"="runway"](around.airport:2000);
      way["aeroway"="taxiway"](around.airport:2000);
      way["aeroway"="apron"](around.airport:2000);
      node["aeroway"="parking_position"](around.airport:2000);
      node["aeroway"="gate"](around.airport:2000);
      node["aeroway"="holding_position"](around.airport:2000);
      way["aeroway"="taxilane"](around.airport:2000);
      
      // BUILDINGS
      way["building"="terminal"](around.airport:2000);
      way["building"="hangar"](around.airport:2000);
      way["building"="tower"](around.airport:2000);
      way["aeroway"="terminal"](around.airport:2000);
      way["aeroway"="hangar"](around.airport:2000);
      way["aeroway"="tower"](around.airport:2000);
      way["building"]["aeroway"](around.airport:2000);
      
      // LANDUSE & VEGETATION
      way["landuse"="grass"](around.airport:2000);
      way["landuse"="meadow"](around.airport:2000);
      way["natural"="wood"](around.airport:2000);
      way["natural"="tree_row"](around.airport:2000);
      way["natural"="grassland"](around.airport:2000);
      way["landuse"="forest"](around.airport:2000);
      
      // ROADS & PATHS
      way["highway"="service"]["service"="runway"](around.airport:2000);
      way["highway"="service"]["aeroway"](around.airport:2000);
      
      // WATER FEATURES
      way["natural"="water"](around.airport:2000);
      way["waterway"](around.airport:2000);
    );
    
    out geom;
    """
    
    print(f"Querying Overpass API for {icao_code} (comprehensive query)...")
    response = requests.post(overpass_url, data={'data': query}, timeout=60)
    
    if response.status_code != 200:
        raise Exception(f"Overpass API error: {response.status_code}")
    
    return response.json()

def create_kml_document(icao_code):
    """
    Create base KML document structure with comprehensive styles
    """
    kml = Element('kml', xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, 'Document')
    
    # Use a different variable name to avoid conflict
    doc_name = SubElement(document, 'name')
    doc_name.text = f"{icao_code} Airport - Complete"
    
    # Define styles for all feature types
    styles = {
        # Aeroway features
        'runway': {'color': 'ff0000ff', 'width': '4'},           # Red
        'taxiway': {'color': 'ff00ffff', 'width': '2'},          # Yellow
        'taxilane': {'color': 'ff00aaff', 'width': '1.5'},       # Orange
        'apron': {'color': 'ff808080', 'width': '1'},            # Gray
        'parking': {'color': 'ff00ff00', 'scale': '0.5'},        # Green
        'gate': {'color': 'ff0000ff', 'scale': '0.5'},           # Blue
        'holding': {'color': 'ffff00ff', 'scale': '0.4'},        # Magenta
        
        # Buildings
        'terminal': {'color': 'ff4040ff', 'width': '2'},         # Light Red
        'hangar': {'color': 'ff404040', 'width': '2'},           # Dark Gray
        'tower': {'color': 'ffff4040', 'width': '2'},            # Light Blue
        'building': {'color': 'ff606060', 'width': '1.5'},       # Medium Gray
        
        # Vegetation
        'grass': {'color': 'ff00ff00', 'width': '1'},            # Green
        'meadow': {'color': 'ff00cc00', 'width': '1'},           # Dark Green
        'wood': {'color': 'ff008800', 'width': '1'},             # Forest Green
        'forest': {'color': 'ff006600', 'width': '1'},           # Deep Green
        'tree_row': {'color': 'ff00aa00', 'width': '1'},         # Med Green
        
        # Roads
        'service_road': {'color': 'ffaaaaaa', 'width': '1'},     # Light Gray
        
        # Water
        'water': {'color': 'ffff0000', 'width': '1'},            # Blue
    }
    
    for style_id, style_attrs in styles.items():
        style = SubElement(document, 'Style', id=style_id)
        if 'color' in style_attrs and 'width' in style_attrs:
            # Line/Polygon style
            linestyle = SubElement(style, 'LineStyle')
            line_color = SubElement(linestyle, 'color')
            line_color.text = style_attrs['color']
            line_width = SubElement(linestyle, 'width')
            line_width.text = style_attrs['width']
            # Add fill for polygons
            polystyle = SubElement(style, 'PolyStyle')
            poly_color = SubElement(polystyle, 'color')
            poly_color.text = style_attrs['color'].replace('ff', '4d')  # Semi-transparent
        if 'scale' in style_attrs:
            # Point style
            iconstyle = SubElement(style, 'IconStyle')
            icon_scale = SubElement(iconstyle, 'scale')
            icon_scale.text = style_attrs['scale']
            icon_color = SubElement(iconstyle, 'color')
            icon_color.text = style_attrs['color']
    
    return kml, document

def add_way_to_kml(document, element, style_id, counter):
    """
    Add an OSM way (line or polygon) to KML
    """
    placemark = SubElement(document, 'Placemark')
    
    # Add name - always include one
    tags = element.get('tags', {})
    name_text = tags.get('name') or tags.get('ref', '')
    if not name_text:
        counter['count'] += 1
        name_text = f"{style_id.upper()}_{counter['count']}"
    
    pm_name = SubElement(placemark, 'name')
    pm_name.text = name_text
    
    # Add description with tags
    desc_parts = []
    for key, value in tags.items():
        if key not in ['name', 'ref', 'icao']:
            desc_parts.append(f"{key}: {value}")
    
    if desc_parts:
        pm_desc = SubElement(placemark, 'description')
        pm_desc.text = '\n'.join(desc_parts)
    
    # Add style
    pm_styleurl = SubElement(placemark, 'styleUrl')
    pm_styleurl.text = f"#{style_id}"
    
    # Add geometry
    geometry = element.get('geometry', [])
    if not geometry:
        return
    
    # Determine if it's a closed polygon or line
    is_closed = (geometry[0]['lat'] == geometry[-1]['lat'] and 
                 geometry[0]['lon'] == geometry[-1]['lon'])
    
    # Buildings, aprons, vegetation, water = polygons; others = lines
    polygon_types = ['apron', 'terminal', 'hangar', 'tower', 'building', 
                     'grass', 'meadow', 'wood', 'forest', 'tree_row', 'water']
    
    if is_closed and style_id in polygon_types:
        polygon = SubElement(placemark, 'Polygon')
        outer = SubElement(polygon, 'outerBoundaryIs')
        linearring = SubElement(outer, 'LinearRing')
        ring_coords = SubElement(linearring, 'coordinates')
    else:
        linestring = SubElement(placemark, 'LineString')
        ring_coords = SubElement(linestring, 'coordinates')
    
    # Add coordinates (KML format: lon,lat,alt)
    coord_text = []
    for node in geometry:
        coord_text.append(f"{node['lon']},{node['lat']},0")
    ring_coords.text = ' '.join(coord_text)

def add_node_to_kml(document, element, style_id, counter):
    """
    Add an OSM node (point) to KML
    """
    placemark = SubElement(document, 'Placemark')
    
    # Add name - always include one
    tags = element.get('tags', {})
    name_text = tags.get('name') or tags.get('ref', '')
    if not name_text:
        counter['count'] += 1
        name_text = f"{style_id.upper()}_{counter['count']}"
    
    pm_name = SubElement(placemark, 'name')
    pm_name.text = name_text
    
    # Add description with tags
    desc_parts = []
    for key, value in tags.items():
        if key not in ['name', 'ref', 'icao']:
            desc_parts.append(f"{key}: {value}")
    
    if desc_parts:
        pm_desc = SubElement(placemark, 'description')
        pm_desc.text = '\n'.join(desc_parts)
    
    # Add style
    pm_styleurl = SubElement(placemark, 'styleUrl')
    pm_styleurl.text = f"#{style_id}"
    
    # Add point geometry
    point = SubElement(placemark, 'Point')
    point_coords = SubElement(point, 'coordinates')
    point_coords.text = f"{element['lon']},{element['lat']},0"

def categorize_element(element):
    """
    Categorize OSM element into appropriate folder and style
    Returns (folder_name, style_id) tuple or None if element should be skipped
    """
    tags = element.get('tags', {})
    
    # Aeroway features
    aeroway = tags.get('aeroway')
    if aeroway == 'runway':
        return ('Runways', 'runway')
    elif aeroway == 'taxiway':
        return ('Taxiways', 'taxiway')
    elif aeroway == 'taxilane':
        return ('Taxiways', 'taxilane')
    elif aeroway == 'apron':
        return ('Aprons', 'apron')
    elif aeroway == 'parking_position':
        return ('Parking & Gates', 'parking')
    elif aeroway == 'gate':
        return ('Parking & Gates', 'gate')
    elif aeroway == 'holding_position':
        return ('Parking & Gates', 'holding')
    elif aeroway == 'terminal':
        return ('Buildings', 'terminal')
    elif aeroway == 'hangar':
        return ('Buildings', 'hangar')
    elif aeroway == 'tower':
        return ('Buildings', 'tower')
    
    # Building features
    building = tags.get('building')
    if building == 'terminal':
        return ('Buildings', 'terminal')
    elif building == 'hangar':
        return ('Buildings', 'hangar')
    elif building == 'tower':
        return ('Buildings', 'tower')
    elif building and aeroway:  # Airport building
        return ('Buildings', 'building')
    
    # Vegetation & Landuse
    landuse = tags.get('landuse')
    natural = tags.get('natural')
    if landuse == 'grass' or natural == 'grassland':
        return ('Vegetation', 'grass')
    elif landuse == 'meadow':
        return ('Vegetation', 'meadow')
    elif natural == 'wood' or landuse == 'forest':
        return ('Vegetation', 'wood')
    elif natural == 'tree_row':
        return ('Vegetation', 'tree_row')
    
    # Water
    if natural == 'water' or tags.get('waterway'):
        return ('Water', 'water')
    
    # Roads
    if tags.get('highway') == 'service':
        return ('Service Roads', 'service_road')
    
    return None

def convert_osm_to_kml(osm_data, icao_code):
    """
    Convert OSM data to KML with comprehensive airport features
    """
    kml, document = create_kml_document(icao_code)
    
    # Create folders for organization
    folders = {}
    folder_names = ['Runways', 'Taxiways', 'Aprons', 'Parking & Gates', 
                    'Buildings', 'Vegetation', 'Water', 'Service Roads']
    
    for folder_name in folder_names:
        folder = SubElement(document, 'Folder')
        folder_name_elem = SubElement(folder, 'name')
        folder_name_elem.text = folder_name
        folders[folder_name] = folder
    
    # Counters for unnamed features (one per style type)
    counters = {}
    
    # Process elements
    for element in osm_data.get('elements', []):
        category = categorize_element(element)
        if not category:
            continue
        
        folder_name, style_id = category
        folder = folders[folder_name]
        
        # Initialize counter if needed
        if style_id not in counters:
            counters[style_id] = {'count': 0}
        
        # Add to KML
        if element['type'] == 'way':
            add_way_to_kml(folder, element, style_id, counters[style_id])
        elif element['type'] == 'node':
            add_node_to_kml(folder, element, style_id, counters[style_id])
    
    return kml

def prettify_xml(elem):
    """
    Return a pretty-printed XML string - uses manual indentation to avoid tag name corruption
    """
    from xml.etree import ElementTree as ET
    # Write to string without prettification first
    rough = ET.tostring(elem, encoding='unicode')
    # Use minidom ONLY for indentation, then fix the corrupted tags
    from xml.dom import minidom
    parsed = minidom.parseString(rough)
    pretty = parsed.toprettyxml(indent="  ")
    # Fix the corrupted <n> and </n> tags back to <name> and </name>
    pretty = pretty.replace('<n>', '<name>').replace('</n>', '</name>')
    return pretty

def main():
    if len(sys.argv) != 2:
        print("Usage: python osm_to_kml.py ICAO_CODE")
        print("Example: python osm_to_kml.py CYHZ")
        sys.exit(1)
    
    icao_code = sys.argv[1].upper()
    output_file = f"{icao_code}_ground.kml"
    
    try:
        # Query OSM
        osm_data = query_overpass(icao_code)
        
        if not osm_data.get('elements'):
            print(f"No airport data found for {icao_code}")
            print("This could mean:")
            print("  - The airport is not in OpenStreetMap")
            print("  - The ICAO code is incorrect")
            print("  - The airport lacks detailed data in OSM")
            sys.exit(1)
        
        print(f"Found {len(osm_data['elements'])} features")
        
        # Convert to KML
        kml = convert_osm_to_kml(osm_data, icao_code)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(prettify_xml(kml))
        
        print(f"Successfully created {output_file}")
        print(f"\nFeatures included:")
        print(f"  - Runways, taxiways, aprons")
        print(f"  - Parking positions, gates, holding positions")
        print(f"  - Buildings (terminals, hangars, towers)")
        print(f"  - Vegetation (grass, woods, meadows)")
        print(f"  - Water features")
        print(f"  - Service roads")
        print(f"\nYou can now:")
        print(f"  1. Open {output_file} in Google Earth to verify")
        print(f"  2. Use it as input to your mapbuilder tool")
        
    except requests.exceptions.RequestException as e:
        print(f"Error querying Overpass API: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
