import json

from parkapi_sources.models import SourceInfo
from universal_converter import InputKind, MappingDocument, MappingRule, SourceFormat, UniversalConverter


def rules():
    return [
        MappingRule('uid', 'id', required=True),
        MappingRule('name', 'name', required=True),
        MappingRule('type', default='CAR_PARK', required=True),
        MappingRule('lat', 'lat', required=True),
        MappingRule('lon', 'lon', required=True),
        MappingRule('capacity', 'capacity', required=True),
    ]


def test_direct_convert_json():
    c = UniversalConverter(SourceInfo(uid='s1', name='Standalone', has_realtime_data=False))
    js = json.dumps([{'id': '1', 'name': 'A', 'lat': 48.1, 'lon': 8.1, 'capacity': 1}])
    out, err = c.convert(js, SourceFormat.JSON, rules(), InputKind.STATIC)
    assert len(out) == 1
    assert len(err) == 0


def test_mapping_document_with_sample_payload():
    mapping_yaml = json.dumps({
        "source_uid": "sample",
        "source_name": "Sample",
        "source_format": "json",
        "input_kind": "static",
        "has_realtime_data": False,
        "pull": {"url": "https://example.com/parking"},
        "mapping_rules": [
            {"target_field": "uid", "source_field": "id", "required": True},
            {"target_field": "name", "source_field": "name", "required": True},
            {"target_field": "type", "default": "CAR_PARK", "required": True},
            {"target_field": "lat", "source_field": "lat", "required": True},
            {"target_field": "lon", "source_field": "lon", "required": True},
            {"target_field": "capacity", "source_field": "capacity", "required": True},
        ],
        "sample_payload": [{"id": "source-1", "name": "Sample Parking", "lat": 48.2, "lon": 8.2, "capacity": 50}],
    })

    document = MappingDocument.from_yaml(mapping_yaml)
    converter = UniversalConverter(
        SourceInfo(uid=document.source_uid, name=document.source_name, has_realtime_data=document.has_realtime_data),
    )
    out, err = converter.convert_from_mapping_document(document, use_sample_data=True)
    assert len(out) == 1
    assert len(err) == 0


def test_error_collection():
    c = UniversalConverter(SourceInfo(uid='s2', name='Standalone', has_realtime_data=False))
    js = json.dumps([{'id': 'missing-capacity', 'name': 'Broken', 'lat': 48.1, 'lon': 8.1}])
    out, err = c.convert(js, SourceFormat.JSON, rules(), InputKind.STATIC)
    assert len(out) == 0
    assert len(err) == 1
    assert err[0].source_uid == 's2'


def test_exception_rules_merge_and_exclude():
    mapping_yaml = json.dumps({
        "source_uid": "sample-ex",
        "source_name": "SampleEx",
        "source_format": "json",
        "input_kind": "static",
        "has_realtime_data": False,
        "pull": {"url": "https://example.com/parking"},
        "mapping_rules": [
            {"target_field": "uid", "source_field": "id", "required": True},
            {"target_field": "name", "source_field": "name", "required": True},
            {"target_field": "type", "default": "CAR_PARK", "required": True},
            {"target_field": "lat", "source_field": "lat", "required": True},
            {"target_field": "lon", "source_field": "lon", "required": True},
            {"target_field": "capacity", "source_field": "capacity", "required": True},
            {"target_field": "address", "source_field": "street"},
            {"target_field": "fee_description", "source_field": "fee"},
        ],
        "exceptions": [
            {"target_field": "address", "merge_from": ["street", "city"], "separator": ", "},
            {"target_field": "fee_description", "exclude": True},
        ],
        "sample_payload": [
            {"id": "source-2", "name": "Sample Two", "lat": 48.21, "lon": 8.21, "capacity": 20, "street": "A St 1", "city": "Town", "fee": "paid"}
        ],
    })
    document = MappingDocument.from_yaml(mapping_yaml)
    converter = UniversalConverter(SourceInfo(uid='sample-ex', name='SampleEx', has_realtime_data=False))
    out, err = converter.convert_from_mapping_document(document, use_sample_data=True)
    assert len(err) == 0
    assert len(out) == 1
    assert out[0].address == 'A St 1, Town'
    assert out[0].fee_description is None
