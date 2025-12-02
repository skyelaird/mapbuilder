#!/usr/bin/env python3
"""
Analyze CYHZ OSM data - Using 'around' approach instead of area
"""

import requests
import json

overpass_url = "https://overpass-api.de/api/interpreter"

# Simpler query using 'around' instead of area
query = """
[out:json][timeout:90];
// Find CYHZ aerodrome
(
  relation["aeroway"="aerodrome"]["icao"="CYHZ"];
  way["aeroway"="aerodrome"]["icao"="CYHZ"];
  node["aeroway"="aerodrome"]["icao"="CYHZ"];
)->.airport;

// Get features within 2km of the airport
(
  way["aeroway"](around.airport:2000);
  node["aeroway"](around.airport:2000);
  relation["aeroway"](around.airport:2000);
  way["building"](around.airport:2000);
  way["natural"](around.airport:2000);
  way["landuse"](around.airport:2000);
  way["water"](around.airport:2000);
  way["waterway"](around.airport:2000);
  way["highway"](around.airport:2000);
  way["barrier"](around.airport:2000);
);

out body;
>;
out skel qt;
"""

print("Querying OpenStreetMap for CYHZ (using 'around' method)...")
print("This may take 30-60 seconds...")
response = requests.post(overpass_url, data={'data': query}, timeout=120)
response.raise_for_status()
data = response.json()

print(f"\n{'='*70}")
print(f"CYHZ OpenStreetMap Analysis")
print(f"{'='*70}")
print(f"\nTotal elements: {len(data['elements'])}")

# Separate by type
nodes = [e for e in data['elements'] if e['type'] == 'node' and 'tags' in e]
ways = [e for e in data['elements'] if e['type'] == 'way' and 'tags' in e]
relations = [e for e in data['elements'] if e['type'] == 'relation' and 'tags' in e]

print(f"Tagged Nodes: {len(nodes)}")
print(f"Tagged Ways: {len(ways)}")
print(f"Tagged Relations: {len(relations)}")

# Analyze aeroway features in detail
print(f"\n{'='*70}")
print("AEROWAY FEATURES (Critical for Ground Layout)")
print(f"{'='*70}")

aeroway_ways = [w for w in ways if 'aeroway' in w.get('tags', {})]
aeroway_nodes = [n for n in nodes if 'aeroway' in n.get('tags', {})]

print(f"\nAeroway Ways: {len(aeroway_ways)}")
for way in aeroway_ways[:50]:  # Limit to first 50 for readability
    aeroway_type = way['tags']['aeroway']
    is_area = way['nodes'][0] == way['nodes'][-1]  # Closed way = area
    geometry = "AREA/POLYGON" if is_area else "LINE"
    
    # Get additional tags
    name = way['tags'].get('name', way['tags'].get('ref', ''))
    surface = way['tags'].get('surface', '')
    
    print(f"  - {aeroway_type:20} {geometry:15} {name:20} {surface}")

if len(aeroway_ways) > 50:
    print(f"  ... and {len(aeroway_ways) - 50} more aeroway ways")

print(f"\nAeroway Nodes: {len(aeroway_nodes)}")
for node in aeroway_nodes[:30]:  # Limit to first 30
    aeroway_type = node['tags']['aeroway']
    ref = node['tags'].get('ref', node['tags'].get('name', ''))
    print(f"  - {aeroway_type:20} ref={ref}")

if len(aeroway_nodes) > 30:
    print(f"  ... and {len(aeroway_nodes) - 30} more aeroway nodes")

# Buildings
print(f"\n{'='*70}")
print("BUILDINGS")
print(f"{'='*70}")

building_ways = [w for w in ways if 'building' in w.get('tags', {})]
print(f"\nTotal buildings: {len(building_ways)}")

building_types = {}
for way in building_ways:
    btype = way['tags'].get('building', 'yes')
    if btype not in building_types:
        building_types[btype] = []
    name = way['tags'].get('name', '')
    aeroway = way['tags'].get('aeroway', '')
    building_types[btype].append((name, aeroway))

for btype, items in sorted(building_types.items()):
    print(f"\n  {btype}: {len(items)} buildings")
    for name, aeroway in items[:10]:  # Show first 10
        if name or aeroway:
            display = f"{name} ({aeroway})" if aeroway else name
            print(f"    - {display}")
    if len(items) > 10:
        print(f"    ... and {len(items)-10} more")

# Natural features
print(f"\n{'='*70}")
print("NATURAL FEATURES (Vegetation)")
print(f"{'='*70}")

natural_ways = [w for w in ways if 'natural' in w.get('tags', {})]
print(f"\nTotal natural features: {len(natural_ways)}")

natural_types = {}
for way in natural_ways:
    ntype = way['tags'].get('natural', 'unknown')
    natural_types[ntype] = natural_types.get(ntype, 0) + 1

for ntype, count in sorted(natural_types.items(), key=lambda x: -x[1]):
    print(f"  {ntype}: {count}")

# Landuse
print(f"\n{'='*70}")
print("LANDUSE")
print(f"{'='*70}")

landuse_ways = [w for w in ways if 'landuse' in w.get('tags', {})]
print(f"\nTotal landuse features: {len(landuse_ways)}")

landuse_types = {}
for way in landuse_ways:
    ltype = way['tags'].get('landuse', 'unknown')
    landuse_types[ltype] = landuse_types.get(ltype, 0) + 1

for ltype, count in sorted(landuse_types.items(), key=lambda x: -x[1]):
    print(f"  {ltype}: {count}")

# Summary for mapping decisions
print(f"\n{'='*70}")
print("MAPPING DECISION SUMMARY")
print(f"{'='*70}")

# Taxiways
taxiways_line = [w for w in aeroway_ways if w['tags']['aeroway'] == 'taxiway' and w['nodes'][0] != w['nodes'][-1]]
taxiways_area = [w for w in aeroway_ways if w['tags']['aeroway'] == 'taxiway' and w['nodes'][0] == w['nodes'][-1]]
print(f"\nTaxiways:")
print(f"  - As LINES (centerlines): {len(taxiways_line)}")
print(f"  - As AREAS (surfaces): {len(taxiways_area)}")

# Taxilanes
taxilanes_line = [w for w in aeroway_ways if w['tags']['aeroway'] == 'taxilane' and w['nodes'][0] != w['nodes'][-1]]
taxilanes_area = [w for w in aeroway_ways if w['tags']['aeroway'] == 'taxilane' and w['nodes'][0] == w['nodes'][-1]]
print(f"\nTaxilanes:")
print(f"  - As LINES: {len(taxilanes_line)}")
print(f"  - As AREAS: {len(taxilanes_area)}")

# Runways
runways_line = [w for w in aeroway_ways if w['tags']['aeroway'] == 'runway' and w['nodes'][0] != w['nodes'][-1]]
runways_area = [w for w in aeroway_ways if w['tags']['aeroway'] == 'runway' and w['nodes'][0] == w['nodes'][-1]]
print(f"\nRunways:")
print(f"  - As LINES (centerlines): {len(runways_line)}")
print(f"  - As AREAS (surfaces): {len(runways_area)}")

# Aprons
aprons = [w for w in aeroway_ways if w['tags']['aeroway'] == 'apron']
print(f"\nAprons (should be areas): {len(aprons)}")

# Parking positions
parking = [n for n in aeroway_nodes if n['tags']['aeroway'] in ['parking_position', 'gate', 'stand']]
print(f"\nParking positions/gates/stands: {len(parking)}")
if parking:
    print("\nSample parking positions:")
    for p in parking[:10]:
        ref = p['tags'].get('ref', p['tags'].get('name', '?'))
        ptype = p['tags']['aeroway']
        print(f"  - {ptype}: {ref}")

# Save full data
output_file = 'cyhz_osm_full.json'
with open(output_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n{'='*70}")
print(f"Full OSM data saved to: {output_file}")
print(f"{'='*70}")
