# AISIMS Data Dictionary

Generated from ERD v0.1.

## projects

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| project_id | varchar | Required | System-Generated | Primary Key |
| project_name | varchar | Optional | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## buildings

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| building_id | varchar | Required | System-Generated | Primary Key |
| building_name | varchar | Optional | Human Input | None |
| project_id | varchar | Required | Human Input | FK -> projects.project_id |
| created_at | timestamp | Required | System-Generated | None |

## revisions

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| rev_id | varchar | Required | System-Generated | Primary Key |
| building_id | varchar | Required | Human Input | FK -> buildings.building_id |
| rev_number | integer | Required | System-Assigned | Unique with building_id. 0 for a buildings first revision; otherwise previous rev_number + 1 within the same building |
| created_at | timestamp | Required | System-Generated | None |

## floors

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| floor_id | varchar | Required | System-Generated | Primary Key |
| floor_name | varchar | Required | Human Input | None (required, see D32) |
| elevation | integer | Required | Human Input | None |
| building_id | varchar | Required | Human Input | FK -> buildings.building_id |
| created_at | timestamp | Required | System-Generated | None |

## grid

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| grid_id | varchar | Required | System-Generated | Primary Key |
| building_id | varchar | Required | Human Input | FK -> buildings.building_id |
| grid_label | varchar | Required | Human Input | Unique with building_id + grid_axis |
| grid_axis | varchar | Required | Human Input | Unique with building_id + grid_label |
| grid_coord | jsonb | Required | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## zones

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| zone_id | varchar | Required | System-Generated | Primary Key |
| pour_seq | integer | Required | Human Input | None |
| building_id | varchar | Required | Human Input | FK -> buildings.building_id |
| created_at | timestamp | Required | System-Generated | None |

## materials

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| mat_id | varchar | Required | System-Generated | Primary Key |
| mat_name | varchar | Optional | Human Input | None |
| mat_type | varchar | Required | Human Input | None |
| mat_strength | integer | Required | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## sections

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| sect_id | varchar | Required | System-Generated | Composite Primary Key (with obj_type) |
| obj_type | varchar | Required | Human Input | Composite Primary Key (with sect_id) |
| dimension | jsonb | Required | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## barspec

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| barspec_id | varchar | Required | System-Generated | Primary Key |
| barspec_dia | integer | Required | Human Input | None |
| barspec_type | varchar | Required | Human Input | None |
| barspec_grade | varchar | Required | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## identities

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| stable_id | varchar | Required | System-Calculated | Primary Key |
| ifc_global_id | varchar | Optional | External Input | Unique |
| is_active | bool | Required | System-Calculated | None |
| created_at | timestamp | Required | System-Generated | None |

## objects

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| obj_id | varchar | Required | System-Generated | Primary Key |
| obj_mark | varchar | Required | Human Input | None |
| stable_id | varchar | Required | System-Calculated | FK -> identities.stable_id |
| rev_id | varchar | Required | System-Assigned | FK -> revisions.rev_id |
| change_status | varchar | Required | System-Calculated | None |
| obj_type | varchar | Required | Human Input | Composite FK (with sect_id) -> sections.(sect_id, obj_type) |
| floor_id | varchar | Required | Human Input | FK -> floors.floor_id |
| zone_id | varchar | Required | Human Input | FK -> zones.zone_id |
| sect_id | varchar | Required | Human Input | Composite FK (with obj_type) -> sections.(sect_id, obj_type) |
| mat_id | varchar | Required | Human Input | FK -> materials.mat_id |
| geometry_points | jsonb | Required | Human Input | None |

## reinforcements

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| bar_id | varchar | Required | System-Generated | Primary Key |
| obj_id | varchar | Required | System-Assigned | FK -> objects.obj_id |
| barspec_id | varchar | Required | Human Input | FK -> barspec.barspec_id |
| bar_role | varchar | Required | Human Input | None |
| bar_count | integer | Required | Human Input | None |
| bar_len | integer | Required | Human Input | None |
| bar_space | integer | Optional | Human Input | None |
| bar_hook_type | varchar | Optional | Human Input | None |

## quantity

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| qty_id | varchar | Required | System-Generated | Primary Key |
| obj_id | varchar | Required | System-Assigned | FK -> objects.obj_id |
| qty_sect | integer | Required | System-Calculated | None |
| qty_bar | integer | Required | System-Calculated | None |

