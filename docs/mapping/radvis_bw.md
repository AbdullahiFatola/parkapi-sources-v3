# RadVIS BW Bike Parking

The state of Baden-Württemberg publishes a GeoJSON dataset with locations of bicycle parking installations (`Abstellanlagen`) across the country, delivered via the MobiDataBW data exchange (`"quell_system": "MOBIDATABW"`). Each feature describes a group of bicycle stands or racks available for public use.

The geometry coordinates are in a projected CRS (UTM zone 32N, WGS84 ellipsoid, EPSG:25832). The converter reprojects them to WGS84 lat/lon using `pyproj` before creating the `ParkingSite`.

Parking installations with `"status": "GEPLANT"` (planned, not yet built) or `"status": "AUSSER BETRIEB"` (decommissioned) should not be integrated. Sources configured in `PARK_API_RADVIS_IGNORE_SOURCES` are skipped as well (RadVIS contains duplicated data from other systems).


## `ParkingSite` Properties

Static values:

Each bicycle parking installation is mapped to a static `ParkingSite` as follows.

Attributes which are set statically by the converter:

* `has_realtime_data` is always set to `false`
* `purpose` is always set to `BIKE`
* `lat` and `lon` are computed from the GeoJSON point geometry, reprojected from UTM zone 32N (EPSG:25832) to WGS84
* `uid` is derived from the numeric feature id

| Field                          | Type                              | Cardinality | Mapping                                           | Comment                                                                      |
|--------------------------------|-----------------------------------|-------------|---------------------------------------------------|------------------------------------------------------------------------------|
| id                             | integer                           | 1           | uid                                               |                                                                              |
| name                           | string                            | ?           | name                                              | Fallback `Abstellanlage` if blank                                            |
| betreiber                      | string                            | ?           | operator_name                                     | Omit if blank                                                                |
| externe_id                     | string                            | ?           | —                                                 | External id from the source system, not mapped                               |
| quell_system                   | string                            | 1           | —                                                 | Used for `PARK_API_RADVIS_IGNORE_SOURCES` filtering                          |
| zustaendig                     | string                            | ?           | —                                                 | Responsible body, not mapped (empty string treated as unset)                 |
| zustaendig_orga_typ            | [OrganizationType](#OrganizationType) | ?        | —                                                 | Not mapped (empty string treated as unset)                                   || kapazitaet                     | integer                           | 1           | capacity                                          |                                                                              |
| anzahl_lademoeglichkeiten      | integer                           | ?           | [restrictions](#ParkingSiteRestriction)           | Map to `CHARGING` restriction if > 0                                         |
| kapazitaet_lastenraeder        | integer                           | ?           | [restrictions](#ParkingSiteRestriction)           | Map to `CARGOBIKE` restriction if > 0                                        |
| ueberwacht                     | [Ueberwachung](#Ueberwachung)    | 1           | supervision_type                                  | See [Ueberwachung](#Ueberwachung)                                            |
| abstellanlagen_ort             | [AbstellanlagenOrt](#AbstellanlagenOrt) | 1      | related_location                                  | See [AbstellanlagenOrt](#AbstellanlagenOrt)                                  |
| groessenklasse                 | string                            | ?           | —                                                 | Size class (e.g. `BASISANGEBOT_XS`), ignored                                 |
| stellplatzart                  | [Stellplatzart](#Stellplatzart)  | 1           | type                                              | See [Stellplatzart](#Stellplatzart)                                          |
| ueberdacht                     | boolean                           | 1           | is_covered                                        |                                                                              |
| gebuehren_pro_tag              | integer                           | ?           | has_fee                                           | `has_fee` set to `true` if any fee is > 0 or a fee description is present  |
| gebuehren_pro_monat            | integer                           | ?           | has_fee                                           | See above                                                                    |
| gebuehren_pro_jahr             | integer                           | ?           | has_fee                                           | See above                                                                    |
| beschreibung_gebuehren         | string                            | ?           | fee_description                                   |                                                                              |
| beschreibung                   | string                            | ?           | description                                       | Combined with `weitere_information` (see below)                              |
| weitere_information            | string                            | ?           | description                                       | Appended to `beschreibung`, separated by a space                             |
| photo_url                      | string                            | ?           | photo_url                                         |                                                                              |
| url                            | string                            | ?           | public_url                                        | Booking/info URL from the source system (e.g. online booking)               |
| status                         | [Status](#Status)                | 1           | —                                                 | `AKTIV` and `KEINE ANGABEN` are imported, `GEPLANT` and `AUSSER BETRIEB` skipped |
| zuletzt_bearbeitet_am          | datetime                          | 1           | static_data_updated_at                            | ISO 8601 timestamp in UTC (e.g. `2026-07-22T01:02:36Z`)                      |


## Stellplatzart

| Key                                       | Mapping              |
|-------------------------------------------|----------------------|
| ANLEHNBUEGEL                              | `STANDS`             |
| FAHRRADBOX                                | `LOCKERS`            |
| VORDERRADANSCHLUSS                        | `WALL_LOOPS`         |
| VORDERRADANSCHLUSS_SICHERUNGSBUEGEL       | `SAFE_WALL_LOOPS`    |
| VORDERRADANSCHLUSS MIT SICHERHEITSBUEGEL  | `SAFE_WALL_LOOPS`    |
| DOPPELSTOECKIG                            | `TWO_TIER`           |
| FAHRRADPARKHAUS                           | `BUILDING`           |
| SAMMELANLAGE                              | `SHED`               |
| SCHLIESSFACH                              | `LOCKBOX`            |
| KEINE ANGABEN                             | `OTHER`              |
| AUTOMATISCHES PARKSYSTEM                  | `OTHER`              |
| ABSTELLFLAECHE                            | `OTHER`              |
| SONSTIGE                                  | `OTHER`              |

Note: the real feed uses underscore-separated enum strings (e.g. `VORDERRADANSCHLUSS_SICHERUNGSBUEGEL`, `KEINE_ANGABEN`, `AUTOMATISCHES_PARKSYSTEM`); both spellings are accepted.


## Ueberwachung

| Key              | Mapping     |
|------------------|-------------|
| KEINE            | `NO`        |
| UNBEKANNT        | *(not set)* |
| VIDEO            | `VIDEO`     |
| VOR-ORT-PERSONAL | `ATTENDED`  |


## AbstellanlagenOrt

| Key                      | Mapping                    |
|--------------------------|----------------------------|
| OEFFENTLICHE_EINRICHTUNG | `Öffentliche Einrichtung`  |
| BIKE_AND_RIDE            | `Bike and Ride`            |
| SCHULE                   | `Schule`                   |
| STRASSENRAUM             | `Straßenraum`              |
| BILDUNGSEINRICHTUNG      | `Bildungseinrichtung`      |
| UNBEKANNT                | *(not set)*                |
| SONSTIGES                | *(not set)*                |


## OrganizationType

| Key       |
|-----------|
| GEMEINDE  |
| KREIS     |
| BUNDESLAND |


## Status

| Key            | Mapping                      |
|----------------|------------------------------|
| AKTIV          | imported                     |
| KEINE ANGABEN  | imported (treated as active) |
| GEPLANT        | skipped                      |
| AUSSER BETRIEB | skipped                      |

Note: the real feed uses `AUSSER_BETRIEB` (underscore); both spellings are accepted.


## ParkingSiteRestriction

| Key                        | Mapping                          |
|----------------------------|----------------------------------|
| anzahl_lademoeglichkeiten  | `ParkingAudience.CHARGING`       |
| kapazitaet_lastenraeder    | `ParkingAudience.CARGOBIKE`      |

Restrictions are only added when the corresponding count is greater than `0`. The count is used as the restriction `capacity`.


## Description

`description` is built from `beschreibung` and `weitere_information`:

* both set: `"{beschreibung} {weitere_information}"`
* only one set: that value
* neither set: `description` stays unset
