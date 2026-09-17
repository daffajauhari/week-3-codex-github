# AISIMS Data Dictionary

Generated from ERD v1.0 (cross-checked against the person own Data Dictionary + Commit 16-26 corrections).

## projects

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| project_id | varchar | Required | System-Generated (Triggered by project creation by user) | Primary Key |
| project_name | varchar | Optional | Human Input | Unique |
| created_at | timestamp | Required | System-Generated | None |

## buildings

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| building_id | varchar | Required | System-Generated | Primary Key |
| building_name | varchar | Optional | Human Input | Unique |
| project_id | varchar | Required | System-Assigned (from URL path) | Foreign key to projects.project_id |
| created_at | timestamp | Required | System-Generated | None |

## revisions

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| rev_id | varchar | Required | System-Generated | Primary Key |
| building_id | varchar | Required | System-Assigned (from URL path) | Foreign Key to buildings.building_id |
| rev_number | integer | Required | System-Assigned | Unique for one building |
| created_at | timestamp | Required | System-Generated | None |

## floors

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| floor_id | varchar | Required | System-Generated | Primary Key |
| floor_name | varchar | Required | Human Input | Unique for one building |
| elevation | integer | Required | Human Input | None |
| building_id | varchar | Required | System-Assigned (from URL path) | Foreign Key to buildings.building_id |
| created_at | timestamp | Required | System-Generated | None |

## grid

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| grid_id | varchar | Required | System-Generated | Primary Key |
| building_id | varchar | Required | System-Assigned (from URL path) | Foreign Key to buildings.building_id |
| grid_label | varchar | Required | Human Input | Unique together with building_id + grid_axis |
| grid_axis | varchar | Required | Human Input | Unique together with building_id + grid_label |
| grid_coord | jsonb | Required | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## zones

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| zone_id | varchar | Required | System-Generated | Primary Key |
| zone_label | varchar | Required | Human Input | Unique for one building |
| pour_seq | integer | Required | Human Input | None |
| building_id | varchar | Required | System-Assigned (from URL path) | Foreign Key to buildings.building_id |
| created_at | timestamp | Required | System-Generated | None |

## materials

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| mat_id | varchar | Required | System-Generated | Primary Key |
| mat_name | varchar | Required | Human Input | Unique |
| mat_type | varchar | Required | Human Input | None |
| mat_strength | integer | Required | Human Input | None |
| mat_weight | integer | Required | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## sections

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| sect_id | varchar | Required | System-Generated | Composite Primary Key (with obj_type) |
| sect_label | varchar | Required | Human Input | Unique |
| obj_type | varchar | Required | Human Input | Composite Primary Key with sect_id |
| dimension | jsonb | Required | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## barspec

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| barspec_id | varchar | Required | System-Generated | Primary Key |
| barspec_label | varchar | Required | Human Input | Unique |
| barspec_dia | integer | Required | Human Input | None |
| barspec_type | varchar | Required | Human Input | None |
| barspec_grade | varchar | Required | Human Input | None |
| barspec_weight | integer | Required | Human Input | None |
| created_at | timestamp | Required | System-Generated | None |

## identities

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| stable_id | varchar | Required | System-Calculated (generated through the is_new input flag) | Primary Key |
| ifc_global_id | varchar | Optional | External Input | Unique |
| is_active | bool | Required | System-Calculated | None |
| created_at | timestamp | Required | System-Generated | None |

## objects

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| obj_id | varchar | Required | System-Generated | Primary Key |
| obj_mark | varchar | Required | Human Input | None |
| stable_id | varchar | Required | System-Calculated | Foreign Key to identities.stable_id |
| rev_id | varchar | Required | System-Assigned | Foreign Key to revisions.rev_id |
| change_status | varchar | Required | System-Calculated | None |
| obj_type | varchar | Required | Human Input | Composite FK with sect_id to sections.(sect_id, obj_type) |
| floor_id | varchar | Required | Human Input (accepted as floor_name at the API layer, resolved to floor_id server-side — D44) | Foreign Key to floors.floor_id |
| zone_id | varchar | Required | Human Input (accepted as zone_label at the API layer, resolved to zone_id server-side — D44) | Foreign Key to zones.zone_id |
| sect_id | varchar | Required | Human Input (accepted as sect_label + obj_type at the API layer, resolved to sect_id server-side — D44) | Composite FK with obj_type to sections.(sect_id, obj_type) |
| mat_id | varchar | Required | Human Input (accepted as mat_name at the API layer, resolved to mat_id server-side — D44) | Foreign Key to materials.mat_id |
| geometry_points | jsonb | Required | Human Input | None |

## reinforcements

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| bar_id | varchar | Required | System-Generated | Primary Key |
| obj_id | varchar | Required | System-Assigned | Foreign Key to objects.obj_id |
| barspec_label | varchar | Required | Human Input (resolved to barspec_id server-side, same pattern as D44) | Foreign Key to barspec.barspec_id |
| bar_role | varchar | Required | Human Input | None |
| bar_count | integer | Required | Human Input | None |
| bar_len | integer | Required | Human Input | None |
| bar_space | integer | Optional | Human Input | None |
| bar_hook_type | varchar | Optional | Human Input | None |

## quantity

| Field Name | Data Type | Req./Opt. | Source | Relationship |
|---|---|---|---|---|
| qty_id | varchar | Required | System-Generated | Primary Key |
| obj_id | varchar | Required | System-Assigned | Foreign Key to objects.obj_id |
| qty_sect | decimal(10,2) | Required | System-Calculated | None |
| qty_bar | decimal(10,2) | Required | System-Calculated | None |

