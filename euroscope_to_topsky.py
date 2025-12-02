#!/usr/bin/env python3
"""
Convert EuroScope line format to TopSky closed polygon format

Usage: python euroscope_to_topsky.py input.txt output.txt [color]

Example:
  python euroscope_to_topsky.py CZUL-HV.txt CZUL-HV_topsky.txt AirspaceA
"""

import sys
import re

def convert_to_topsky(input_file, output_file, color="AirspaceA", polygon_type="Boundary"):
    """Convert EuroScope line segments to TopSky polygon"""
    
    coordinates = []
    
    # Read input file
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            # Parse line: coord1 coord2 COLOR ; comment
            parts = line.split()
            if len(parts) >= 2:
                lat = parts[0]
                lon = parts[1]
                
                # Only add if not duplicate (avoid double-adding connection points)
                coord = (lat, lon)
                if not coordinates or coordinates[-1] != coord:
                    coordinates.append(coord)
    
    # Write TopSky format
    with open(output_file, 'w') as f:
        # Write all coordinates
        for lat, lon in coordinates:
            f.write(f"COORD:{lat}:{lon}\n")
        
        # Close the polygon with COORDPOLY
        f.write(f"COORDPOLY:{color}:{polygon_type}\n")
    
    print(f"✓ Converted {len(coordinates)} coordinates")
    print(f"✓ Output: {output_file}")
    print(f"\nTopSky polygon format:")
    print(f"  - {len(coordinates)} COORD lines")
    print(f"  - 1 COORDPOLY line (color={color}, type={polygon_type})")

def main():
    if len(sys.argv) < 3:
        print("Usage: python euroscope_to_topsky.py input.txt output.txt [color] [type]")
        print("\nExample:")
        print("  python euroscope_to_topsky.py CZUL-HV.txt CZUL-HV_topsky.txt AirspaceA Boundary")
        print("\nCommon colors: AirspaceA, AirspaceB, AirspaceC, AirspaceD")
        print("Common types: Boundary, Restricted, Prohibited, Danger")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    color = sys.argv[3] if len(sys.argv) > 3 else "AirspaceA"
    polygon_type = sys.argv[4] if len(sys.argv) > 4 else "Boundary"
    
    convert_to_topsky(input_file, output_file, color, polygon_type)

if __name__ == "__main__":
    main()
