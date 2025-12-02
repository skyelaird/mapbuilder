#!/usr/bin/env python3
"""
Batch process multiple airports from OSM to GNG format

Usage: python batch_process.py
"""

import subprocess
import sys

# Define airports to process
AIRPORTS = [
    {'icao': 'CYHZ', 'name': 'Halifax', 'fir': 'CZQM'},
    {'icao': 'CYYT', 'name': 'St Johns', 'fir': 'CZQX'},
    {'icao': 'CYQM', 'name': 'Greater Moncton', 'fir': 'CZQM'},
    {'icao': 'CYSJ', 'name': 'Saint John', 'fir': 'CZQM'},
    {'icao': 'CYFC', 'name': 'Fredericton', 'fir': 'CZQM'},
]

def process_airport(airport):
    """Process a single airport"""
    icao = airport['icao']
    name = airport['name']
    fir = airport['fir']
    
    print(f"\n{'='*60}")
    print(f"Processing {icao} - {name} ({fir})")
    print(f"{'='*60}")
    
    cmd = [
        'python',
        'osm_to_gng_direct.py',
        icao,
        '--name', name,
        '--fir', fir,
        '--output', f'output/{icao}_gng.kml'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR processing {icao}:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return False

def main():
    """Process all airports"""
    print("CZQM/CZQX Airport Ground Network Batch Processor")
    print(f"Processing {len(AIRPORTS)} airports...\n")
    
    # Create output directory if needed
    import os
    os.makedirs('output', exist_ok=True)
    
    success_count = 0
    failed = []
    
    for airport in AIRPORTS:
        if process_airport(airport):
            success_count += 1
        else:
            failed.append(airport['icao'])
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Successful: {success_count}/{len(AIRPORTS)}")
    
    if failed:
        print(f"Failed: {', '.join(failed)}")
    else:
        print("All airports processed successfully!")
    
    print(f"\nOutput files in: output/")
    print(f"\nNext steps:")
    print(f"  1. Review KML files in Google Earth (optional)")
    print(f"  2. Import each *_gng.kml file into GNG")
    print(f"  3. Export to EuroScope format")

if __name__ == "__main__":
    main()
