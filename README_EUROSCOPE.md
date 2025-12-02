# OSM to EuroScope Direct Converter

**Skip KML/GNG entirely - go straight from OpenStreetMap to EuroScope format!**

## Quick Start

```bash
python osm_to_euroscope.py CYHZ --name "Halifax"
```

**Output:**
- `CYHZ_Lines.txt` - Taxiway/runway centerlines (SCT format)
- `CYHZ_Areas.txt` - Aprons, buildings, grass, water (GEO format)
- `CYHZ_Labels.txt` - Gate positions

## Complete Workflow

```
OpenStreetMap
    ↓
[osm_to_euroscope.py]  ← ONE COMMAND
    ↓
EuroScope .txt files
    ↓
Copy/paste into sector file
    ↓
Done!
```

## Usage Examples

```bash
# Halifax (CZQM)
python osm_to_euroscope.py CYHZ --name "Halifax"

# St Johns (CZQX)
python osm_to_euroscope.py CYYT --name "St Johns"

# Custom output directory
python osm_to_euroscope.py CYQM --name "Greater Moncton" --output-dir output/
```

## Output Format

### Lines File (CYHZ_Lines.txt)
```
;runway
N044.51.55.807 W063.31.36.968 N044.52.58.644 W063.30.34.931 COLOR_RunwayBorder
;taxiway
N044.52.07.474 W063.31.56.705 N044.52.07.412 W063.31.56.555 COLOR_TaxiwayYellow
```

### Areas File (CYHZ_Areas.txt)
```
;
;apron
;
COLOR_ApronSurface
N044.51.54.928 W063.31.43.784
N044.51.54.564 W063.31.43.133
N044.51.53.757 W063.31.41.630
;
```

### Labels File (CYHZ_Labels.txt)
```
"2A" N044.52.05.123 W063.31.42.456 gate
"2B" N044.52.05.234 W063.31.42.567 gate
```

## Feature Mapping

**Lines (Centerlines):**
- Runways → `COLOR_RunwayBorder`
- Taxiways → `COLOR_TaxiwayYellow`
- Taxilanes → `COLOR_TaxiwayGrey`

**Areas (Polygons):**
- Aprons → `COLOR_ApronSurface`
- Buildings/Hangars → `COLOR_Building`
- Grass/Woods → `COLOR_GrasSurface`
- Water → `COLOR_GrasSurface`

**Labels:**
- Gates, parking positions, stands with ref numbers

## Advantages

✅ **No intermediate steps** - OSM → EuroScope directly
✅ **Faster** - No KML generation or GNG processing
✅ **Cleaner** - Native EuroScope format
✅ **Automatable** - Easy to batch process airports
✅ **Filterable** - Only features inside aerodrome boundary

## Integration into Sector File

1. Open your sector file (e.g., `CZQM.sct`)
2. Find the `[GEO]` section
3. Copy/paste contents of `CYHZ_Areas.txt`
4. Find the appropriate line section
5. Copy/paste contents of `CYHZ_Lines.txt`
6. Add labels as needed from `CYHZ_Labels.txt`

## Comparison with KML Method

| Method | Steps | Output |
|--------|-------|--------|
| **KML/GNG** | OSM → KML → Google Earth → GNG → Export → EuroScope | 5 steps |
| **Direct** | OSM → EuroScope | 1 step |

## Features

- ✅ Aerodrome boundary filtering (only features inside airport)
- ✅ Hangar name normalization (Hanger → Hangar)
- ✅ Sorted output (runways, then taxiways, then buildings, etc.)
- ✅ DMS coordinate format (N044.51.54.928 W063.31.43.784)
- ✅ Proper comment formatting
- ✅ Color-coded by feature type

## Requirements

- Python 3.6+
- `requests` library: `pip install requests`
- Internet connection (for OSM queries)

## Notes

- Query takes 30-60 seconds depending on airport size
- Only includes features within OSM aerodrome boundary
- Runway/taxiway surfaces (not just centerlines) must be added manually if desired
- You can manually edit output files before integrating into sector file

## Troubleshooting

**No features found:**
- Verify ICAO code is correct
- Check that airport exists in OpenStreetMap
- Some small airports may not have detailed mapping

**Missing features:**
- OSM data may be incomplete for some airports
- Consider contributing to OpenStreetMap to improve data

**Wrong colors:**
- Edit the color mappings in the script if needed
- Colors match standard GNG/EuroScope conventions

---

**This tool was designed specifically for CZQM/CZQX vACC workflow but works for any airport worldwide!**
