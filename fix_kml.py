#!/usr/bin/env python3
import sys

if len(sys.argv) != 2:
    print("Usage: python fix_kml.py CYHZ_ground.kml")
    sys.exit(1)

filename = sys.argv[1]

with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace short tag with full tag
old_open = chr(60) + 'n' + chr(62)  # <n>
new_open = chr(60) + 'name' + chr(62)  # <name>
old_close = chr(60) + '/' + 'n' + chr(62)  # </n>
new_close = chr(60) + '/' + 'name' + chr(62)  # </name>

content = content.replace(old_open, new_open)
content = content.replace(old_close, new_close)

with open(filename, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {filename}")
