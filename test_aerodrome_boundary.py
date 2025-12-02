#!/usr/bin/env python3
"""
Query OSM for features INSIDE the CYHZ aerodrome boundary only
"""

import requests
import json

overpass_url = "https://overpass-api.de/api/interpreter"

# First, let's see what the aerodrome boundary looks like
query_aerodrome = """
[out:json][timeout:30];
(
  relation["aeroway"="aerodrome"]["icao"="CYHZ"];
  way["aeroway"="aerodrome"]["icao"="CYHZ"];
);
out geom;
"""

print("Step 1: Querying for CYHZ aerodrome boundary...")
response = requests.post(overpass_url, data={'data': query_aerodrome}, timeout=60)
response.raise_for_status()
aerodrome_data = response.json()

print(f"\nAerodrome elements found: {len(aerodrome_data['elements'])}")
for elem in aerodrome_data['elements']:
    print(f"  - Type: {elem['type']}, ID: {elem['id']}")
    if 'tags' in elem:
        print(f"    Tags: {elem['tags']}")

# Save aerodrome boundary
with open('cyhz_aerodrome_boundary.json', 'w') as f:
    json.dump(aerodrome_data, f, indent=2)

print("\nAerodrome boundary saved to: cyhz_aerodrome_boundary.json")

# Now query features using the aerodrome as area
# Try different syntax approaches
query_inside = """
[out:json][timeout:90];
// Get the aerodrome
(
  relation["aeroway"="aerodrome"]["icao"="CYHZ"];
  way["aeroway"="aerodrome"]["icao"="CYHZ"];
);
map_to_area->.a;

// Get features inside
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

print("\n" + "="*70)
print("Step 2: Querying for features INSIDE aerodrome boundary...")
print("="*70)

try:
    response = requests.post(overpass_url, data={'data': query_inside}, timeout=120)
    response.raise_for_status()
    inside_data = response.json()
    
    print(f"\nElements inside aerodrome: {len(inside_data['elements'])}")
    
    # Count types
    nodes = [e for e in inside_data['elements'] if e['type'] == 'node' and 'tags' in e]
    ways = [e for e in inside_data['elements'] if e['type'] == 'way' and 'tags' in e]
    
    print(f"  Tagged nodes: {len(nodes)}")
    print(f"  Tagged ways: {len(ways)}")
    
    # Save
    with open('cyhz_inside_aerodrome.json', 'w') as f:
        json.dump(inside_data, f, indent=2)
    
    print("\nData saved to: cyhz_inside_aerodrome.json")
    
    # Quick summary
    buildings = [w for w in ways if 'building' in w.get('tags', {})]
    aeroways = [w for w in ways if 'aeroway' in w.get('tags', {})]
    natural = [w for w in ways if 'natural' in w.get('tags', {})]
    
    print(f"\n  Buildings: {len(buildings)}")
    print(f"  Aeroway features: {len(aeroways)}")
    print(f"  Natural features: {len(natural)}")
    
except Exception as e:
    print(f"\nError with area query: {e}")
    print("\nThis might mean:")
    print("  1. The aerodrome is not a proper area in OSM")
    print("  2. The area ID needs to be computed differently")
    print("  3. We need to use polygon intersection instead")
    
    print("\nFalling back to using bounding box or manual filtering...")
