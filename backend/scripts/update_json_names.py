"""Update recipient names in extracted JSON files before ingestion."""

import json
from pathlib import Path


def parse_mappings(filepath):
    """Parse mappings file."""
    mappings = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                mappings[parts[0]] = {
                    'name': parts[1],
                    'acronym': parts[2],
                    'city': parts[3],
                    'state': parts[4],
                    'region': int(parts[5]) if parts[5].isdigit() else None
                }
    return mappings


def update_json_files(json_dir, mappings):
    """Update recipient info in JSON files."""
    json_dir = Path(json_dir)
    updated = 0

    for json_file in json_dir.glob('*.json'):
        if json_file.name == 'all_reports_combined.json':
            continue

        with open(json_file, 'r') as f:
            data = json.load(f)

        source_file = data['source_file']
        if source_file in mappings:
            mapping = mappings[source_file]
            data['recipient']['name'] = mapping['name']
            data['recipient']['acronym'] = mapping['acronym']
            data['recipient']['city'] = mapping['city']
            data['recipient']['state'] = mapping['state']
            data['recipient']['region_number'] = mapping['region']

            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"✓ Updated: {json_file.name}")
            updated += 1

    print(f"\nUpdated {updated} JSON files")


if __name__ == '__main__':
    mappings = parse_mappings('scripts/recipient_name_mappings.txt')
    update_json_files('extracted_data', mappings)
