#!/usr/bin/env python3
"""
OSM to EuroScope Direct Converter
Queries OSM and outputs native EuroScope format - no KML/GNG intermediate

Usage: python osm_to_euroscope.py CYHZ --name "Halifax"

Outputs:
  - CYHZ_Lines.txt (taxiway/runway centerlines)
  - CYHZ_Areas.txt (aprons, buildings, grass, water)
  - CYHZ_Labels.txt (gate positions)
"""

import sys
import json
import requests
import argparse
from math import modf

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
    
    print(f"Querying OpenStreetMap for {icao_code}...")
    response = requests.post(overpass_url, data={'data': query}, timeout=120)
    response.raise_for_status()
    return response.json()

def normalize_hangar_name(name):
    """Normalize hangar misspellings"""
    if not name:
        return name
    name = name.replace('Hanger', 'Hangar')
    name = name.replace('hanger', 'hangar')
    name = name.replace('Hagner', 'Hangar')
    name = name.replace('hagner', 'hangar')
    return name

def decimal_to_dms(decimal_degrees, is_latitude):
    """Convert decimal degrees to DMS format: N044.51.54.928 or W063.31.43.784"""
    is_positive = decimal_degrees >= 0
    decimal_degrees = abs(decimal_degrees)
    
    degrees = int(decimal_degrees)
    minutes_decimal = (decimal_degrees - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    if is_latitude:
        direction = 'N' if is_positive else 'S'
        return f"{direction}{degrees:03d}.{minutes:02d}.{seconds:06.3f}"
    else:
        direction = 'E' if is_positive else 'W'
        return f"{direction}{degrees:03d}.{minutes:02d}.{seconds:06.3f}"

def format_coordinate(lon, lat):
    """Format coordinate pair as EuroScope DMS"""
    lat_dms = decimal_to_dms(lat, True)
    lon_dms = decimal_to_dms(lon, False)
    return f"{lat_dms} {lon_dms}"

def parse_osm_data(osm_data):
    """Parse OSM JSON into categorized features"""
    nodes = {}
    features = {
        'lines': [],
        'areas': [],
        'labels': []
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
            
            # Lines (not closed ways)
            if aeroway == 'runway' and not is_closed:
                features['lines'].append({
                    'type': 'runway',
                    'color': 'COLOR_RunwayBorder',
                    'coords': coords,
                    'name': name or 'runway',
                    'sort_order': 0
                })
            
            elif aeroway == 'taxiway' and not is_closed:
                features['lines'].append({
                    'type': 'taxiway',
                    'color': 'COLOR_TaxiwayYellow',
                    'coords': coords,
                    'name': name or 'taxiway',
                    'sort_order': 1
                })
            
            elif aeroway == 'taxilane' and not is_closed:
                features['lines'].append({
                    'type': 'taxilane',
                    'color': 'COLOR_TaxiwayGrey',
                    'coords': coords,
                    'name': name or 'taxilane',
                    'sort_order': 2
                })
            
            # Areas (closed ways/polygons)
            elif aeroway == 'apron':
                features['areas'].append({
                    'type': 'apron',
                    'color': 'COLOR_ApronSurface',
                    'coords': coords,
                    'name': name or 'apron',
                    'sort_order': 0
                })
            
            elif aeroway == 'hangar' or building == 'hangar':
                hangar_name = normalize_hangar_name(name) or 'Hangar'
                features['areas'].append({
                    'type': 'hangar',
                    'color': 'COLOR_Building',
                    'coords': coords,
                    'name': hangar_name,
                    'sort_order': 1
                })
            
            elif building:
                building_name = normalize_hangar_name(name) or building
                features['areas'].append({
                    'type': 'building',
                    'color': 'COLOR_Building',
                    'coords': coords,
                    'name': building_name,
                    'sort_order': 2
                })
            
            elif natural == 'wood':
                features['areas'].append({
                    'type': 'wood',
                    'color': 'COLOR_GrasSurface',
                    'coords': coords,
                    'name': 'woods',
                    'sort_order': 3
                })
            
            elif natural == 'grassland' or landuse == 'grass':
                features['areas'].append({
                    'type': 'grass',
                    'color': 'COLOR_GrasSurface',
                    'coords': coords,
                    'name': 'grass',
                    'sort_order': 3
                })
            
            elif natural == 'water' or water or waterway:
                features['areas'].append({
                    'type': 'water',
                    'color': 'COLOR_GrasSurface',  # Water as grass surface
                    'coords': coords,
                    'name': 'water',
                    'sort_order': 4
                })
        
        elif element['type'] == 'node':
            tags = element.get('tags', {})
            aeroway = tags.get('aeroway')
            
            if aeroway in ['gate', 'parking_position', 'stand']:
                ref = tags.get('ref', tags.get('name', '?'))
                features['labels'].append({
                    'type': aeroway,
                    'ref': ref,
                    'lat': element['lat'],
                    'lon': element['lon']
                })
    
    # Sort features
    features['lines'].sort(key=lambda x: (x['sort_order'], x['name']))
    features['areas'].sort(key=lambda x: (x['sort_order'], x['name']))
    features['labels'].sort(key=lambda x: x['ref'])
    
    return features

def write_lines_file(features, output_file):
    """Write lines (SCT Entries) in EuroScope format"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for feature in features['lines']:
            # Convert polyline to point-to-point segments
            coords = feature['coords']
            for i in range(len(coords) - 1):
                lon1, lat1 = coords[i]
                lon2, lat2 = coords[i + 1]
                
                coord1 = format_coordinate(lon1, lat1)
                coord2 = format_coordinate(lon2, lat2)
                
                # Comment line with feature name
                if i == 0:
                    f.write(f";{feature['name']}\n")
                
                # Line segment
                f.write(f"{coord1} {coord2} {feature['color']}\n")
    
    print(f"  Lines: {len(features['lines'])} features written to {output_file}")

def write_areas_file(features, output_file):
    """Write areas (Regions) in EuroScope format"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for feature in features['areas']:
            # Comment with feature name
            f.write(f";\n;{feature['name']}\n;\n")
            
            # Color line
            f.write(f"{feature['color']}\n")
            
            # Coordinates (one per line)
            for lon, lat in feature['coords']:
                coord = format_coordinate(lon, lat)
                f.write(f"{coord}\n")
            
            # End marker
            f.write(";\n")
    
    print(f"  Areas: {len(features['areas'])} features written to {output_file}")

def write_labels_file(features, output_file):
    """Write labels in EuroScope format"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for label in features['labels']:
            coord = format_coordinate(label['lon'], label['lat'])
            f.write(f'"{label["ref"]}" {coord} {label["type"]}\n')
    
    print(f"  Labels: {len(features['labels'])} features written to {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Convert OpenStreetMap data directly to EuroScope format'
    )
    parser.add_argument('icao', help='ICAO code (e.g., CYHZ)')
    parser.add_argument('--name', required=True, help='Airport name (for logging)')
    parser.add_argument('--output-dir', default='.', help='Output directory (default: current)')
    
    args = parser.parse_args()
    
    icao = args.icao.upper()
    
    try:
        # Query OSM
        osm_data = query_overpass(icao)
        
        # Parse features
        print(f"Parsing features...")
        features = parse_osm_data(osm_data)
        
        print(f"\nFound:")
        print(f"  Lines: {len(features['lines'])}")
        print(f"  Areas: {len(features['areas'])}")
        print(f"  Labels: {len(features['labels'])}")
        
        # Write output files
        print(f"\nWriting EuroScope files...")
        
        lines_file = f"{args.output_dir}/{icao}_Lines.txt"
        areas_file = f"{args.output_dir}/{icao}_Areas.txt"
        labels_file = f"{args.output_dir}/{icao}_Labels.txt"
        
        write_lines_file(features, lines_file)
        write_areas_file(features, areas_file)
        write_labels_file(features, labels_file)
        
        print(f"\n✓ Success! Files created:")
        print(f"  {lines_file}")
        print(f"  {areas_file}")
        print(f"  {labels_file}")
        print(f"\nReady to integrate into EuroScope sector file!")
        
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
