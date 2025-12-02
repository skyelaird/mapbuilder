# OSM to GNG Direct Converter

**One-step converter: OpenStreetMap → GNG KML format**

No intermediate files. Just query OSM and get GNG-ready output.

---

## Quick Start

### Single Airport

```bash
python osm_to_gng_direct.py CYHZ --name "Halifax" --fir CZQM
```

Creates: `CYHZ_gng.kml` ready for GNG import.

### All CZQM/CZQX Airports

```bash
python batch_process.py
```

Processes all airports defined in the script:
- CYHZ (Halifax)
- CYYT (St Johns)
- CYQM (Greater Moncton)
- CYSJ (Saint John)
- CYFC (Fredericton)

Output files in `output/` directory.

---

## Complete Workflow

```
OpenStreetMap
    ↓
[osm_to_gng_direct.py] ← ONE SCRIPT
    ↓
GNG KML (ready to import)
    ↓
[Google Earth Pro] - Optional review
    ↓
[GNG Import]
    ↓
[GNG Export to EuroScope]
    ↓
Done!
```

---

## Command Reference

### Basic Usage

```bash
python osm_to_gng_direct.py <ICAO> --name "<Airport Name>" [options]
```

### Options

- `--name` (required): Airport name for folder structure
- `--fir`: FIR code (default: CZQM)
- `--output` / `-o`: Output filename (default: `<ICAO>_gng.kml`)

### Examples

```bash
# Halifax (CZQM)
python osm_to_gng_direct.py CYHZ --name "Halifax"

# St Johns (CZQX)
python osm_to_gng_direct.py CYYT --name "St Johns" --fir CZQX

# Custom output location
python osm_to_gng_direct.py CYQM --name "Greater Moncton" -o custom/moncton.kml
```

---

## What It Does

1. **Queries OpenStreetMap** via Overpass API for:
   - Runways → `RunwayBorder`
   - Taxiways → `TaxiwayYellow`
   - Taxilanes → `TaxiwayGrey`
   - Aprons → `Apron`
   - Parking positions/gates/stands → `ParkPos`

2. **Converts to GNG format** with:
   - Correct folder hierarchy: `SCT Entries > FIR > ICAO > Groundlayout > Airport`
   - LineString geometry (not Polygons)
   - Color descriptions WITHOUT `COLOR_` prefix
   - GNG style definitions

3. **Outputs ready-to-import KML** that GNG can directly import

---

## File Structure

```
mapbuilder/
├── osm_to_gng_direct.py    ← Main script
├── batch_process.py         ← Batch processor
└── output/                  ← Output directory
    ├── CYHZ_gng.kml
    ├── CYYT_gng.kml
    └── ...
```

---

## Advantages Over Two-Step Process

✅ **Simpler**: One command instead of two  
✅ **Faster**: No intermediate file I/O  
✅ **Cleaner**: No leftover OSM KML files  
✅ **Less confusion**: Clear input → output  

---

## Customization

### Add More Airports

Edit `batch_process.py`:

```python
AIRPORTS = [
    {'icao': 'CYHZ', 'name': 'Halifax', 'fir': 'CZQM'},
    {'icao': 'CYYY', 'name': 'Your Airport', 'fir': 'CZQM'},  # Add here
]
```

### Change Color Mapping

Edit `osm_to_gng_direct.py`:

```python
FEATURE_COLOR_MAP = {
    'runway': 'RunwayBorder',
    'taxiway': 'TaxiwayYellow',  # Change to 'TaxiwayGrey' etc.
    # ...
}
```

---

## Troubleshooting

### No features found

- Check ICAO code is correct
- Airport might not be mapped in OSM
- Try viewing raw OSM data: https://www.openstreetmap.org/

### GNG import fails

- Verify KML structure in Google Earth first
- Check folder names match GNG expectations
- Ensure LineStrings (not Polygons) are used

### Network timeouts

- Overpass API may be busy
- Wait 30 seconds and retry
- Script has 60-second timeout

---

## Technical Details

**Coordinate Order**: Longitude, Latitude, Altitude (KML standard)

**Geometry**: LineStrings with `tessellate=1` and `altitudeMode=clampToGround`

**Description Field**: Contains ONLY color name (e.g., `TaxiwayGrey`), NOT `COLOR_TaxiwayGrey`. GNG adds the `COLOR_` prefix when exporting to EuroScope.

**Folder Hierarchy**: Must exactly match:
```
SCT Entries
└── FIR (e.g., CZQM)
    └── ICAO (e.g., CYHZ)
        └── Groundlayout
            └── Airport Name (e.g., Halifax)
                └── Placemarks
```

---

## Next Steps After Running

1. **Optional**: Open `<ICAO>_gng.kml` in Google Earth to review
2. **Import to GNG**: Load the KML file
3. **Export from GNG**: Save as EuroScope `.txt` format
4. **Integrate**: Add to your sector file release

---

## Requirements

- Python 3.6+
- `requests` library: `pip install requests`
- Internet connection (for OSM queries)

---

## Questions?

This script was designed specifically for CZQM/CZQX vACC workflow based on analysis of actual GNG exports and EuroScope format requirements.

**Tested with**: CYHZ reference export matching exact GNG structure.
