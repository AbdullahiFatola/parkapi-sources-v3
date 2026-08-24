"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import pyproj
from validataclass.dataclasses import Default, validataclass
from validataclass.validators import (
    BooleanValidator,
    DataclassValidator,
    DateTimeValidator,
    EnumValidator,
    IntegerValidator,
    Noneable,
    StringValidator,
    UrlValidator,
)

from parkapi_sources.models import GeojsonBaseFeatureInput, ParkingSiteRestrictionInput, StaticParkingSiteInput
from parkapi_sources.models.enums import ParkingAudience, ParkingSiteType, PurposeType, SupervisionType
from parkapi_sources.util import round_7d
from parkapi_sources.validators import EmptystringNoneable, ReplacingStringValidator


class OrganizationType(Enum):
    GEMEINDE = 'GEMEINDE'
    KREIS = 'KREIS'
    BUNDESLAND = 'BUNDESLAND'


class RadvisSupervisionType(Enum):
    KEINE = 'KEINE'
    UNBEKANNT = 'UNBEKANNT'
    VIDEO = 'VIDEO'
    VOR_ORT_PERSONAL = 'VOR-ORT-PERSONAL'

    def to_supervision_type(self) -> SupervisionType:
        return {
            self.KEINE: SupervisionType.NO,
            self.VIDEO: SupervisionType.VIDEO,
            self.VOR_ORT_PERSONAL: SupervisionType.ATTENDED,
        }.get(self)


class LocationType(Enum):
    OEFFENTLICHE_EINRICHTUNG = 'OEFFENTLICHE_EINRICHTUNG'
    BIKE_AND_RIDE = 'BIKE_AND_RIDE'
    UNBEKANNT = 'UNBEKANNT'
    SCHULE = 'SCHULE'
    STRASSENRAUM = 'STRASSENRAUM'
    SONSTIGES = 'SONSTIGES'
    BILDUNGSEINRICHTUNG = 'BILDUNGSEINRICHTUNG'

    def to_related_location(self) -> Optional[str]:
        return {
            self.OEFFENTLICHE_EINRICHTUNG: 'Öffentliche Einrichtung',
            self.BIKE_AND_RIDE: 'Bike and Ride',
            self.SCHULE: 'Schule',
            self.STRASSENRAUM: 'Straßenraum',
            self.BILDUNGSEINRICHTUNG: 'Bildungseinrichtung',
        }.get(self)


class RadvisParkingSiteType(Enum):
    KEINE_ANGABEN = 'KEINE ANGABEN'
    # The real feed uses underscore-separated values; space variants kept for compatibility
    KEINE_ANGABEN_UNDERSCORED = 'KEINE_ANGABEN'
    VORDERRADANSCHLUSS = 'VORDERRADANSCHLUSS'
    ANLEHNBUEGEL = 'ANLEHNBUEGEL'
    FAHRRADBOX = 'FAHRRADBOX'
    DOPPELSTOECKIG = 'DOPPELSTOECKIG'
    SAMMELANLAGE = 'SAMMELANLAGE'
    FAHRRADPARKHAUS = 'FAHRRADPARKHAUS'
    AUTOMATISCHES_PARKSYSTEM = 'AUTOMATISCHES PARKSYSTEM'
    AUTOMATISCHES_PARKSYSTEM_UNDERSCORED = 'AUTOMATISCHES_PARKSYSTEM'
    SCHLIESSFACH = 'SCHLIESSFACH'
    ABSTELLFLAECHE = 'ABSTELLFLAECHE'
    # Real feed value; the 'MIT SICHERHEITSBUEGEL' variant below is kept for compatibility
    VORDERRADANSCHLUSS_SICHERUNGSBUEGEL = 'VORDERRADANSCHLUSS_SICHERUNGSBUEGEL'
    VORDERRADANSCHLUSS_MIT_SICHERHEITSBUEGEL = 'VORDERRADANSCHLUSS MIT SICHERHEITSBUEGEL'
    SONSTIGE = 'SONSTIGE'

    def to_parking_site_type(self) -> ParkingSiteType:
        return {
            self.ANLEHNBUEGEL: ParkingSiteType.STANDS,
            self.FAHRRADBOX: ParkingSiteType.LOCKERS,
            self.VORDERRADANSCHLUSS: ParkingSiteType.WALL_LOOPS,
            self.VORDERRADANSCHLUSS_SICHERUNGSBUEGEL: ParkingSiteType.SAFE_WALL_LOOPS,
            self.VORDERRADANSCHLUSS_MIT_SICHERHEITSBUEGEL: ParkingSiteType.SAFE_WALL_LOOPS,
            self.DOPPELSTOECKIG: ParkingSiteType.TWO_TIER,
            self.FAHRRADPARKHAUS: ParkingSiteType.BUILDING,
            self.SAMMELANLAGE: ParkingSiteType.SHED,
            self.SCHLIESSFACH: ParkingSiteType.LOCKBOX,
            self.KEINE_ANGABEN: ParkingSiteType.OTHER,
            self.KEINE_ANGABEN_UNDERSCORED: ParkingSiteType.OTHER,
            self.AUTOMATISCHES_PARKSYSTEM: ParkingSiteType.OTHER,
            self.AUTOMATISCHES_PARKSYSTEM_UNDERSCORED: ParkingSiteType.OTHER,
            self.ABSTELLFLAECHE: ParkingSiteType.OTHER,
        }.get(self, ParkingSiteType.OTHER)


class StatusType(Enum):
    KEINE_ANGABEN = 'KEINE ANGABEN'
    # The real feed uses underscore-separated values; space variants kept for compatibility
    KEINE_ANGABEN_UNDERSCORED = 'KEINE_ANGABEN'
    GEPLANT = 'GEPLANT'
    AKTIV = 'AKTIV'
    AUSSER_BETRIEB = 'AUSSER BETRIEB'
    AUSSER_BETRIEB_UNDERSCORED = 'AUSSER_BETRIEB'

    def is_importable(self) -> bool:
        return self in [
            StatusType.AKTIV,
            StatusType.KEINE_ANGABEN,
            StatusType.KEINE_ANGABEN_UNDERSCORED,
        ]


@validataclass
class RadvisFeaturePropertiesInput:
    id: int = IntegerValidator()
    name: str = EmptystringNoneable(StringValidator(max_length=256)), Default(None)
    betreiber: str = EmptystringNoneable(StringValidator(max_length=256)), Default(None)
    quell_system: str = StringValidator()
    externe_id: Optional[str] = Noneable(StringValidator())
    # Use EmptystringNoneable because zustaendig and zustaendig_orga_typ can be empty strings
    zustaendig: Optional[str] = EmptystringNoneable(StringValidator())
    zustaendig_orga_typ: Optional[OrganizationType] = EmptystringNoneable(EnumValidator(OrganizationType))
    kapazitaet: int = IntegerValidator()
    anzahl_lademoeglichkeiten: Optional[int] = Noneable(IntegerValidator())
    kapazitaet_lastenraeder: Optional[int] = Noneable(IntegerValidator())
    ueberwacht: RadvisSupervisionType = EnumValidator(RadvisSupervisionType)
    abstellanlagen_ort: LocationType = EnumValidator(LocationType)
    stellplatzart: RadvisParkingSiteType = EnumValidator(RadvisParkingSiteType)
    ueberdacht: bool = BooleanValidator()
    gebuehren_pro_tag: Optional[int] = Noneable(IntegerValidator())
    gebuehren_pro_monat: Optional[int] = Noneable(IntegerValidator())
    gebuehren_pro_jahr: Optional[int] = Noneable(IntegerValidator())
    beschreibung_gebuehren: Optional[str] = (
        Noneable(ReplacingStringValidator(mapping={'\n': ' ', '\r': ''})),
        Default(None),
    )
    beschreibung: Optional[str] = (
        Noneable(ReplacingStringValidator(mapping={'\x80': ' ', '\n': ' ', '\r': ''})),
        Default(None),
    )
    weitere_information: Optional[str] = (
        Noneable(ReplacingStringValidator(mapping={'\n': ' ', '\r': ''})),
        Default(None),
    )
    photo_url: Optional[str] = Noneable(UrlValidator(max_length=4096)), Default(None)
    url: Optional[str] = Noneable(UrlValidator(max_length=4096)), Default(None)
    status: StatusType = EnumValidator(StatusType)
    zuletzt_bearbeitet_am: datetime = DateTimeValidator(
        local_timezone=timezone.utc,
        target_timezone=timezone.utc,
        discard_milliseconds=True,
    )

    def to_dicts(self) -> list[dict]:
        description: Optional[str] = None
        if self.beschreibung and self.weitere_information:
            description = f'{self.beschreibung} {self.weitere_information}'
        elif self.beschreibung:
            description = self.beschreibung
        elif self.weitere_information:
            description = self.weitere_information

        has_fee: Optional[bool] = None
        if (
            self.gebuehren_pro_tag
            or self.gebuehren_pro_monat
            or self.gebuehren_pro_jahr
            or self.beschreibung_gebuehren is not None
        ):
            has_fee = True

        restrictions: list[ParkingSiteRestrictionInput] = []
        if self.anzahl_lademoeglichkeiten:
            restrictions.append(
                ParkingSiteRestrictionInput(
                    type=ParkingAudience.CHARGING,
                    capacity=self.anzahl_lademoeglichkeiten,
                ),
            )
        if self.kapazitaet_lastenraeder:
            restrictions.append(
                ParkingSiteRestrictionInput(
                    type=ParkingAudience.CARGOBIKE,
                    capacity=self.kapazitaet_lastenraeder,
                ),
            )

        return [
            {
                'uid': str(self.id),
                'name': self.name or 'Abstellanlage',
                'type': self.stellplatzart.to_parking_site_type(),
                'capacity': self.kapazitaet,
                'purpose': PurposeType.BIKE,
                'operator_name': self.betreiber,
                'description': description,
                'has_realtime_data': False,
                'is_covered': self.ueberdacht,
                'related_location': self.abstellanlagen_ort.to_related_location(),
                'supervision_type': self.ueberwacht.to_supervision_type(),
                'static_data_updated_at': self.zuletzt_bearbeitet_am,
                'photo_url': self.photo_url,
                'public_url': self.url,
                'fee_description': self.beschreibung_gebuehren,
                'has_fee': has_fee,
                'restrictions': restrictions,
            },
        ]


@validataclass
class RadvisFeatureInput(GeojsonBaseFeatureInput):
    properties: RadvisFeaturePropertiesInput = DataclassValidator(RadvisFeaturePropertiesInput)

    def to_static_parking_site_inputs_with_proj(self, proj: pyproj.Proj) -> list[StaticParkingSiteInput]:
        property_dicts: list[dict] = self.properties.to_dicts()
        static_parking_site_inputs: list[StaticParkingSiteInput] = []

        for property_dict in property_dicts:
            static_parking_site_input = StaticParkingSiteInput(
                lat=round_7d(self.geometry.y),
                lon=round_7d(self.geometry.x),
                **property_dict,
            )

            coordinates = proj(float(static_parking_site_input.lon), float(static_parking_site_input.lat), inverse=True)
            static_parking_site_input.lon = round_7d(coordinates[0])
            static_parking_site_input.lat = round_7d(coordinates[1])

            static_parking_site_inputs.append(static_parking_site_input)

        return static_parking_site_inputs
