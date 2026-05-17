# universal-converter

Single intelligent converter for all parking sources, driven by a mapping document.

## Key idea
Instead of many source-specific converters, use **one UniversalConverter** + one source mapping document.

## What it supports
- Source pull by URL (+ optional auth headers/query params)
- Formats: JSON, GeoJSON, CSV, XML, Excel
- Transform rules: direct `source_field`, computed `resolver`, `default`, `required`
- Validation against ParkAPI Source models (`StaticParkingSiteInput`, `RealtimeParkingSiteInput`)
- Per-row error collection

## Mapping template
Use `templates/universal_mapping_template.yaml` as the baseline for any source.
It describes:
- source metadata
- pull URL/credentials
- field-level mapping rules
- sample payload for offline tests

## Usage sketch
1. Load mapping YAML into `MappingDocument.from_yaml(...)`.
2. Build `UniversalConverter(SourceInfo(...))`.
3. Run `convert_from_mapping_document(...)`.


## Local setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run tests
```bash
pytest
```
