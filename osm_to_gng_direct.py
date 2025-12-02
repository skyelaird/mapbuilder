#!/usr/bin/env python3
"""
OSM to GNG Direct Converter with Aerodrome Boundary Filtering
Creates proper GNG structure with SCT Entries, Regions, and Labels sections

Usage: python osm_to_gng_direct.py CYHZ --name "Halifax" --fir CZQM
"""

import sys
import json
import requests
import argparse
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# GNG Color definitions
GNG_COLORS = {
    'TaxiwayGrey': 'ff505050',
    'TaxiwayYellow': 'ff00ffff',
    'RunwayBorder': 'ff808080',
    'ApronSurface': 'ff808080',
    'Building': 'ff808080',
    'GrasSurface': 'ff003200',
    'Labels': 'ffcc33ff',
}

def query_overpass(icao_code):
    """Query Overpass API for airport data inside aerodrome boundary"""
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    query = f"""
    [out:json][timeout:90];
    // Get the aerodrome boundary
    (
      relation["aeroway"="aerodrome"]["icao"="{icao_code}"];
      way["aeroway"="aerodrome"]["icao"="{icao_code}"];
    );
    map_to_area->.a;
    
    // Get features inside the aerodrome
    (
      way["aeroway"](area.a);
      node["aeroway"](area.a);
      way["building"](area.a);
      way["natural"](area.a);
      way["landuse"](area.a);
      way["water"](area.a);
      way["waterway"](area.a);
    );
    
    out body;
    >;
    out skel qt;
    """
    
    print(f"Querying OpenStreetMap for {icao_code} (inside aerodrome boundary only)...")
    response = requests.post(overpass_url, data={'data': query}, timeout=120)
    response.raise_for_status()
    return response.json()

def normalize_hangar_name(name):
    """Normalize hangar misspellings"""
    if not name:
        return name
    # Common misspellings
    name = name.replace('Hanger', 'Hangar')
    name = name.replace('hanger', 'hangar')
    name = name.replace('Hagner', 'Hangar')
    name = name.replace('hagner', 'hangar')
    return name

def create_gng_styles(doc):
    """Create GNG color style definitions"""
    for color_name, color_value in GNG_COLORS.items():
        style = SubElement(doc, 'Style', id=color_name)
        
        # Icon style
        icon_style = SubElement(style, 'IconStyle')
        SubElement(icon_style, 'hotSpot', x="19", y="0", xunits="pixels", yunits="pixels")
        SubElement(icon_style, 'color').text = color_value
        SubElement(icon_style, 'colorMode').text = 'normal'
        SubElement(icon_style, 'scale').text = '1'
        icon = SubElement(icon_style, 'Icon')
        SubElement(icon, 'href').text = 'https://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png'
        
        # Poly style
        poly_style = SubElement(style, 'PolyStyle')
        SubElement(poly_style, 'color').text = color_value.replace('ff', 'cc')  # Semi-transparent
        SubElement(poly_style, 'fill').text = '1'
        SubElement(poly_style, 'outline').text = '0'
        
        # Line style
        line_style = SubElement(style, 'LineStyle')
        SubElement(line_style, 'color').text = color_value
        SubElement(line_style, 'colorMode').text = 'normal'
        SubElement(line_style, 'width').text = '2'

def create_folder_hierarchy(parent, icao, airport_name, fir='CZQM'):
    """Create the GNG folder hierarchy: FIR > ICAO > Airport"""
    fir_folder = SubElement(parent, 'Folder')
    SubElement(fir_folder, 'name').text = fir
    SubElement(fir_folder, 'visibility').text = '1'
    
    icao_folder = SubElement(fir_folder, 'Folder')
    SubElement(icao_folder, 'name').text = icao
    SubElement(icao_folder, 'visibility').text = '1'
    
    airport_folder = SubElement(icao_folder, 'Folder')
    SubElement(airport_folder, 'name').text = airport_name
    SubElement(airport_folder, 'visibility').text = '1'
    
    return airport_folder

def parse_osm_data(osm_data):
    """Parse OSM JSON into categorized features"""
    nodes = {}
    features = {
        'lines': [],      # For SCT Entries (LineStrings)
        'areas': [],      # For Regions (Polygons)
        'points': []      # For Labels (Points)
    }
    
    # First pass: collect all nodes
    for element in osm_data.get('elements', []):
        if element['type'] == 'node':
            nodes[element['id']] = {
                'lat': element['lat'],
                'lon': element['lon']
            }
    
    # Second pass: process ways and nodes with tags
    for element in osm_data.get('elements', []):
        if element['type'] == 'way':
            tags = element.get('tags', {})
            aeroway = tags.get('aeroway')
            building = tags.get('building')
            natural = tags.get('natural')
            landuse = tags.get('landuse')
            water = tags.get('water')
            waterway = tags.get('waterway')
            
            # Build coordinate list
            coords = []
            for node_id in element['nodes']:
                if node_id in nodes:
                    node = nodes[node_id]
                    coords.append((node['lon'], node['lat']))
            
            if not coords:
                continue
            
            is_closed = element['nodes'][0] == element['nodes'][-1]
            name = tags.get('name', tags.get('ref', ''))
            
            # Aeroway features
            if aeroway == 'taxiway' and not is_closed:
                # Taxiway centerline → SCT Entries
                features['lines'].append({
                    'type': 'taxiway',
                    'color': 'TaxiwayYellow',
                    'coords': coords,
                    'name': name or 'taxiway',
                    'sort_order': 1
                })
            
            elif aeroway == 'taxilane' and not is_closed:
                # Taxilane centerline → SCT Entries
                features['lines'].append({
                    'type': 'taxilane',
                    'color': 'TaxiwayGrey',
                    'coords': coords,
                    'name': name or 'taxilane',
                    'sort_order': 2
                })
            
            elif aeroway == 'runway' and not is_closed:
                # Runway centerline → SCT Entries
                features['lines'].append({
                    'type': 'runway',
                    'color': 'RunwayBorder',
                    'coords': coords,
                    'name': name or 'runway',
                    'sort_order': 0
                })
            
            elif aeroway == 'apron':
                # Apron area → Regions
                features['areas'].append({
                    'type': 'apron',
                    'color': 'ApronSurface',
                    'coords': coords,
                    'name': name or 'apron',
                    'sort_order': 0
                })
            
            elif aeroway == 'hangar' or building == 'hangar':
                # Hangar → Regions (normalize name)
                hangar_name = normalize_hangar_name(name) or 'Hangar'
                features['areas'].append({
                    'type': 'hangar',
                    'color': 'Building',
                    'coords': coords,
                    'name': hangar_name,
                    'sort_order': 1
                })
            
            elif building:
                # Other buildings → Regions
                building_name = normalize_hangar_name(name) or building
                features['areas'].append({
                    'type': 'building',
                    'color': 'Building',
                    'coords': coords,
                    'name': building_name,
                    'sort_order': 2
                })
            
            # Natural features → Regions (all as GrasSurface)
            elif natural == 'wood':
                features['areas'].append({
                    'type': 'wood',
                    'color': 'GrasSurface',
                    'coords': coords,
                    'name': 'woods',
                    'sort_order': 3
                })
            
            elif natural == 'grassland' or landuse == 'grass':
                features['areas'].append({
                    'type': 'grass',
                    'color': 'GrasSurface',
                    'coords': coords,
                    'name': 'grass',
                    'sort_order': 3
                })
            
            elif natural == 'water' or water or waterway:
                # Map water to GrasSurface (as requested)
                features['areas'].append({
                    'type': 'water',
                    'color': 'GrasSurface',
                    'coords': coords,
                    'name': 'water',
                    'sort_order': 4
                })
        
        elif element['type'] == 'node':
            tags = element.get('tags', {})
            aeroway = tags.get('aeroway')
            
            if aeroway in ['gate', 'parking_position', 'stand']:
                # Gate/parking → Labels
                ref = tags.get('ref', tags.get('name', '?'))
                features['points'].append({
                    'type': aeroway,
                    'ref': ref,
                    'lat': element['lat'],
                    'lon': element['lon']
                })
    
    # Sort features by type within each category
    features['lines'].sort(key=lambda x: (x['sort_order'], x['name']))
    features['areas'].sort(key=lambda x: (x['sort_order'], x['name']))
    features['points'].sort(key=lambda x: x['ref'])
    
    return features

def create_sct_entries_section(parent, features, icao, airport_name, fir):
    """Create SCT Entries section (Lines)"""
    sct_folder = SubElement(parent, 'Folder', id="SCT Entries")
    SubElement(sct_folder, 'name').text = 'SCT Entries'
    SubElement(sct_folder, 'visibility').text = '1'
    
    # Create hierarchy: FIR > ICAO > Groundlayout > Airport
    fir_folder = SubElement(sct_folder, 'Folder')
    SubElement(fir_folder, 'name').text = fir
    SubElement(fir_folder, 'visibility').text = '1'
    
    icao_folder = SubElement(fir_folder, 'Folder')
    SubElement(icao_folder, 'name').text = icao
    SubElement(icao_folder, 'visibility').text = '1'
    
    groundlayout = SubElement(icao_folder, 'Folder')
    SubElement(groundlayout, 'name').text = 'Groundlayout'
    SubElement(groundlayout, 'visibility').text = '1'
    
    airport_folder = SubElement(groundlayout, 'Folder')
    SubElement(airport_folder, 'name').text = airport_name
    SubElement(airport_folder, 'visibility').text = '1'
    
    # Add line features (already sorted)
    for i, feature in enumerate(features['lines'], 1):
        placemark = SubElement(airport_folder, 'Placemark')
        SubElement(placemark, 'name').text = f"{feature['color']} {i})"
        SubElement(placemark, 'description').text = feature['color']
        SubElement(placemark, 'styleUrl').text = f"#{feature['color']}"
        SubElement(placemark, 'visibility').text = '1'
        
        linestring = SubElement(placemark, 'LineString')
        SubElement(linestring, 'tessellate').text = '1'
        SubElement(linestring, 'altitudeMode').text = 'clampToGround'
        
        coord_string = ' '.join([f"{lon},{lat},0" for lon, lat in feature['coords']])
        SubElement(linestring, 'coordinates').text = coord_string

def create_regions_section(parent, features, icao, airport_name, fir):
    """Create Regions section (Polygons)"""
    regions_folder = SubElement(parent, 'Folder', id="Regions")
    SubElement(regions_folder, 'name').text = 'Regions'
    SubElement(regions_folder, 'visibility').text = '1'
    
    # Create hierarchy: FIR > ICAO > Airport
    fir_folder = SubElement(regions_folder, 'Folder')
    SubElement(fir_folder, 'name').text = fir
    SubElement(fir_folder, 'visibility').text = '1'
    
    icao_folder = SubElement(fir_folder, 'Folder')
    SubElement(icao_folder, 'name').text = icao
    SubElement(icao_folder, 'visibility').text = '1'
    
    airport_folder = SubElement(icao_folder, 'Folder')
    SubElement(airport_folder, 'name').text = airport_name
    SubElement(airport_folder, 'visibility').text = '1'
    
    # Add area features (already sorted)
    for feature in features['areas']:
        placemark = SubElement(airport_folder, 'Placemark')
        SubElement(placemark, 'name').text = feature['name']
        SubElement(placemark, 'description').text = feature['color']
        SubElement(placemark, 'styleUrl').text = f"#{feature['color']}"
        SubElement(placemark, 'visibility').text = '1'
        
        polygon = SubElement(placemark, 'Polygon')
        SubElement(polygon, 'tessellate').text = '1'
        SubElement(polygon, 'altitudeMode').text = 'clampToGround'
        
        outer = SubElement(polygon, 'outerBoundaryIs')
        ring = SubElement(outer, 'LinearRing')
        
        coord_string = ' '.join([f"{lon},{lat},0" for lon, lat in feature['coords']])
        SubElement(ring, 'coordinates').text = coord_string

def create_labels_section(parent, features, icao, airport_name, fir):
    """Create Labels section (Points) with proper hierarchy"""
    labels_folder = SubElement(parent, 'Folder', id="Labels")
    SubElement(labels_folder, 'name').text = 'Labels'
    SubElement(labels_folder, 'visibility').text = '1'
    
    # Create hierarchy: FIR > ICAO > Airport
    fir_folder = SubElement(labels_folder, 'Folder')
    SubElement(fir_folder, 'name').text = fir
    SubElement(fir_folder, 'visibility').text = '1'
    
    icao_folder = SubElement(fir_folder, 'Folder')
    SubElement(icao_folder, 'name').text = icao
    SubElement(icao_folder, 'visibility').text = '1'
    
    airport_folder = SubElement(icao_folder, 'Folder')
    SubElement(airport_folder, 'name').text = airport_name
    SubElement(airport_folder, 'visibility').text = '1'
    
    # Add point labels (already sorted)
    for point in features['points']:
        placemark = SubElement(airport_folder, 'Placemark')
        SubElement(placemark, 'name').text = point['ref']
        SubElement(placemark, 'description').text = 'Labels'
        SubElement(placemark, 'styleUrl').text = '#Labels'
        SubElement(placemark, 'visibility').text = '1'
        
        kml_point = SubElement(placemark, 'Point')
        SubElement(kml_point, 'coordinates').text = f"{point['lon']},{point['lat']},0"

def convert_osm_to_gng(osm_data, icao, airport_name, fir):
    """Convert OSM data to GNG KML format"""
    # Create KML root
    kml = Element('kml', xmlns="http://www.opengis.net/kml/2.2")
    doc = SubElement(kml, 'Document')
    SubElement(doc, 'name').text = f"{icao} Ground Layout"
    SubElement(doc, 'visibility').text = '1'
    SubElement(doc, 'open').text = '1'
    
    # Add GNG styles
    create_gng_styles(doc)
    
    # Parse OSM data
    features = parse_osm_data(osm_data)
    
    print(f"\nFound features:")
    print(f"  Lines (SCT Entries): {len(features['lines'])}")
    print(f"  Areas (Regions): {len(features['areas'])}")
    print(f"  Points (Labels): {len(features['points'])}")
    
    # Create three main sections with proper hierarchies
    create_sct_entries_section(doc, features, icao, airport_name, fir)
    create_regions_section(doc, features, icao, airport_name, fir)
    create_labels_section(doc, features, icao, airport_name, fir)
    
    return kml

def prettify_xml(elem):
    """Return pretty-printed XML string"""
    rough_string = tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    parser = argparse.ArgumentParser(
        description='Convert OpenStreetMap airport data directly to GNG KML format'
    )
    parser.add_argument('icao', help='ICAO code (e.g., CYHZ)')
    parser.add_argument('--name', required=True, help='Airport name (e.g., "Halifax")')
    parser.add_argument('--fir', default='CZQM', help='FIR code (default: CZQM)')
    parser.add_argument('--output', '-o', help='Output file (default: <ICAO>_gng.kml)')
    
    args = parser.parse_args()
    
    icao = args.icao.upper()
    output_file = args.output or f"{icao}_gng.kml"
    
    try:
        # Query OSM
        osm_data = query_overpass(icao)
        
        # Convert to GNG
        print(f"Converting to GNG format...")
        kml = convert_osm_to_gng(osm_data, icao, args.name, args.fir)
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(prettify_xml(kml))
        
        print(f"\n✓ Success! Created: {output_file}")
        print(f"\nNext steps:")
        print(f"  1. Optional: Review in Google Earth")
        print(f"  2. Import to GNG")
        print(f"  3. Export to EuroScope")
        
    except requests.exceptions.RequestException as e:
        print(f"Error querying OpenStreetMap: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
