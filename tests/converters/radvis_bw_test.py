"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from requests_mock import Mocker

from parkapi_sources.converters import RadvisBwPullConverter
from parkapi_sources.models import ParkingAudience, ParkingSiteType, PurposeType, SupervisionType
from parkapi_sources.util import RequestHelper
from tests.converters.helper import validate_static_parking_site_inputs


@pytest.fixture
def radvis_bw_config_helper(mocked_config_helper: Mock):
    config = {
        'PARK_API_RADVIS_USER': 'de14131a-c542-445a-999b-88393df54903',
        'PARK_API_RADVIS_PASSWORD': '20832cbc-377d-41e4-aee8-7bc1a87dfe90',
        'PARK_API_RADVIS_IGNORE_SOURCES': '',
    }
    mocked_config_helper.get.side_effect = lambda key, default=None: config.get(key, default)
    return mocked_config_helper


@pytest.fixture
def radvis_bw_pull_converter(radvis_bw_config_helper: Mock, request_helper: RequestHelper) -> RadvisBwPullConverter:
    return RadvisBwPullConverter(config_helper=radvis_bw_config_helper, request_helper=request_helper)


class RadvisBwConverterTest:
    @staticmethod
    def test_get_static_parking_sites(radvis_bw_pull_converter: RadvisBwPullConverter, requests_mock: Mocker):
        json_path = Path(Path(__file__).parent, 'data', 'radvis_bw.json')
        with json_path.open() as json_file:
            json_data = json_file.read()

        requests_mock.get(
            'https://radvis.landbw.de/api/geoserver/basicauth/radvis/wfs?service=WFS&version=2.0.0&request=GetFeature'
            '&typeNames=radvis%3Aabstellanlage&outputFormat=application/json',
            text=json_data,
        )
        static_parking_site_inputs, import_parking_site_exceptions = radvis_bw_pull_converter.get_static_parking_sites()

        # 13 features: 8 real feed features (7 MOBIDATABW + 1 RADVIS AUSSER_BETRIEB, all skipped)
        # + 5 importable RADVIS features added for mapping coverage.
        assert len(static_parking_site_inputs) == 5
        assert len(import_parking_site_exceptions) == 0

        validate_static_parking_site_inputs(static_parking_site_inputs)

        inputs_by_uid = {site.uid: site for site in static_parking_site_inputs}

        # Skipped: MOBIDATABW source system, even with status AKTIV / KEINE ANGABEN
        assert '161357006' not in inputs_by_uid
        assert '161357099' not in inputs_by_uid
        # Skipped: RADVIS source but status AUSSER_BETRIEB / AUSSER BETRIEB / GEPLANT
        assert '160084219' not in inputs_by_uid
        assert '161357201' not in inputs_by_uid
        assert '161357200' not in inputs_by_uid

        # Basics: ANLEHNBUEGEL -> STANDS, description built from beschreibung + weitere_information
        rathaus = inputs_by_uid['200000001']
        assert rathaus.name == 'Rathaus Freiburg'
        assert rathaus.type == ParkingSiteType.STANDS
        assert rathaus.purpose == PurposeType.BIKE
        assert rathaus.operator_name == 'Stadt Freiburg'
        assert rathaus.capacity == 12
        assert rathaus.description == 'Fahrradständer am Rathaus 24h geöffnet'
        assert rathaus.has_realtime_data is False
        assert rathaus.has_fee is None
        assert rathaus.supervision_type == SupervisionType.NO
        assert rathaus.related_location == 'Straßenraum'
        assert rathaus.restrictions == []

        # SCHLIESSFACH -> LOCKBOX + purpose ITEM; restrictions from charging/cargo counts
        bike_station = inputs_by_uid['200000002']
        assert bike_station.type == ParkingSiteType.LOCKBOX
        assert bike_station.purpose == PurposeType.ITEM
        assert bike_station.is_covered is True
        assert bike_station.has_fee is True
        assert bike_station.fee_description == '2 EUR/Tag'
        assert bike_station.supervision_type == SupervisionType.VIDEO
        assert bike_station.related_location == 'Bike and Ride'
        assert bike_station.public_url == 'https://booking.example.com/bike-station-karlsruhe'
        assert bike_station.photo_url == 'https://example.com/bike-station-karlsruhe.jpg'
        assert sorted(
            [(restriction.type.value, restriction.capacity) for restriction in bike_station.restrictions],
        ) == [
            ('CARGOBIKE', 2),
            ('CHARGING', 4),
        ]

        # Blank name/betreiber -> fallback name, operator omitted; fee 0 counts as fee (not ""/null)
        anon = inputs_by_uid['200000003']
        assert anon.name == 'Abstellanlage'
        assert anon.operator_name is None
        assert anon.type == ParkingSiteType.SAFE_WALL_LOOPS
        assert anon.purpose == PurposeType.BIKE
        assert anon.has_fee is True
        assert anon.supervision_type is None
        assert anon.related_location is None
        assert anon.description == 'Kostenlos'

        # SAMMELANLAGE -> SHED; only weitere_information set; ATTENDED supervision
        sammel = inputs_by_uid['200000004']
        assert sammel.type == ParkingSiteType.SHED
        assert sammel.purpose == PurposeType.BIKE
        assert sammel.supervision_type == SupervisionType.ATTENDED
        assert sammel.related_location == 'Öffentliche Einrichtung'
        assert sammel.description == 'Bewachte Anlage'
        assert sammel.has_fee is True

        # FAHRRADPARKHAUS -> BUILDING; charging count 0 must not create a restriction
        parkhaus = inputs_by_uid['200000005']
        assert parkhaus.type == ParkingSiteType.BUILDING
        assert parkhaus.purpose == PurposeType.BIKE
        assert parkhaus.related_location == 'Bildungseinrichtung'
        assert parkhaus.restrictions == []
        assert parkhaus.has_fee is None
        assert parkhaus.description is None
