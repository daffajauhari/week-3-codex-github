---
title: "Week 3 Deliverable Plan"
subtitle: "AISIMS Data Structure — To-Do List & Cautions"
author: "Daffa"
date: "September 2026"
geometry: margin=2.2cm
fontsize: 10pt
---

# 1. Purpose

This document consolidates the Week 3 to-do list derived from the *Week 2 Review & Week 3 Assignment Instruction* (Sections 7–14), cross-referenced against working discussions on hierarchy, revision modeling, and identity design. Section 4 (Design Decisions Log) has been consolidated to reflect only the current, superseding state of each decision — entries that were fully replaced by a later decision have been merged or removed rather than kept as historical pointers.

---

# 2. To-Do List per Deliverable Header

## 2.1 Written Deliverables (Tulisan)

| # | Item | Notes | Source |
|---|------|-------|--------|
| 1 | ERD / schema diagram — now at v1.0 | Self-authored first per Sec 8.9, then iterated with AI critique through multiple versions | Sec 8.2, 8.9 |
| 2 | Data Dictionary for all entities | Field name, meaning, type, required/optional, unit, example, source, relationship, validation note | Sec 8.4 |
| 3 | Identity & Revision Note | Define Stable ID, obj_mark, IFC GlobalId, Revision ID separately. Include two worked examples: (a) a beam whose section changes, (b) a beam whose location changes | Sec 8.3 |
| 4 | Key Relationship Description | One-to-many, reusable-reference, and revision relationships | Sec 8.4 / 10 |
| 5 | Geometry Representation Note | Axis-point representation for column/beam vs. ordered boundary points for wall/slab; units, point order, closure, local/global coordinates, member orientation, limitations | Sec 8.5 |
| 6 | Training Revision Model write-up | Explain snapshot approach; how the same object links across revisions; how changed attributes are represented; how added/deleted objects are handled. Must be labeled "Training Proposal," not a production rule | Sec 8.7 |
| 7 | Candidate Validation Rules (10–15) | Each with Rule ID, Object/Field, Condition, Expected Result, Severity/Review Status, Rationale. Must also cover the 14-item minimum coverage list | Sec 8.8, Sec 9 |
| 8 | Updated Outstanding Questions | Assign a status to every question — OPEN / ASSUMPTION FOR TRAINING ONLY / RESOLVED FROM DOCUMENT / OUT OF CURRENT WEEK SCOPE | Sec 8.10 |
| 9 | AI Tool Usage Log | Continuous log. Must include at least one AI suggestion that was rejected or modified, not only accepted ones | Sec 10 |

## 2.2 Presentation (Presentasi)

| # | Item | Notes | Source |
|---|------|-------|--------|
| 10 | Short explanation / presentation, 5–10 minutes | Explain the model and identity/revision decisions in own words | Sec 10 |

## 2.3 Codebase

| # | Item | Notes | Source |
|---|------|-------|--------|
| 11 | Create Week 3 branch from the accepted Week 2 baseline | Done — `feat/week-3-deliverables` | Sec 8.1 |
| 12 | Implement schema: `Project`, `Building`, `Revision`, `Identity`, `Object` (replaces `Member`), `Reinforcement`, `Quantity`, `Section` (replaces `Dimension`), `BarSpec`, `Grid` | Full implementation, not conceptual-only — in progress via Codex commits | Sec 8.6 |
| 13 | Alembic migrations, one per schema change, `sa.text()` for raw SQL | Week 2 data wiped and reseeded, not backfilled (project decision) | Working discussion |
| 14 | Enforce validation rules as real database constraints where feasible | CheckConstraint, UniqueConstraint, ForeignKey | Working discussion |
| 15 | Implement the three revision workflows (Stable ID Assignment, Change Status Determination, Active Status Sync) and the Pre-Validation Gate | New service module, no prior service layer existed in the Week 2 codebase | Working discussion |
| 16 | API endpoints: POST for all Project Configuration entities, POST for Bulk Upload / Interactive Edit revisions, GET for browsing the full hierarchy | Fully nested URLs (`/projects/{id}/buildings/{id}/...`) | Working discussion |
| 17 | Frontend: browsing UI matching Week 2's existing style/components | Read-only (list + detail); creation/editing stays `/docs`-driven | Working discussion |
| 18 | Repository evidence | Commits follow branch → test → PR/CI → merge discipline; CI must remain green | Sec 10 |

---

# 3. Things to Be Cautious About

**1. ERD Draft v0.1 was self-authored, without AI.**
Later versions (v0.2 onward) incorporate AI critique and the person's own subsequent fixes — this progression itself is a good AI Tool Usage Log entry (see the historical DBML versions retained separately).

**2. Ten Review Questions must be answerable without AI (Section 11).**
Example: *"Why can B1.02.A1A2 be a useful engineering mark but a poor stable primary identity?"* Practice answering these independently before submission.

**3. The AI Tool Usage Log must record at least one rejected or modified AI suggestion.**
Several candidates exist already: the ERD v0.1 critique log, and this consolidation itself (which reverses the earlier "obj_mark is system-generated" assumption).

**4. The revision model must be explicitly labeled "Training Proposal."**
It should not be presented as a finalized or production-ready design (Sec 8.7).

**5. Reinforcement and Quantity are now fully implemented, not conceptual-only.**
This exceeds the original Week 3 scope note in Sec 8.6 — worth stating explicitly in the write-up as a deliberate extension, not an oversight of the "conceptual only" guidance.

**6. The Geometry Representation Note is a separate written deliverable.**
Distinct from the Quantity calculation logic now implemented in code — the write-up should still cover representation (points, order, closure), not just restate the quantity formulas.

**7. Outstanding Questions require an explicit status.**
Do not leave any unstated, and do not silently treat an open question as a final decision.

---

# 4. Design Decisions Log

Status tags: **✅ Decided** = explicitly stated, confirmed, or built upon consistently across many later turns without ever being contradicted. **🔶 Proposed — pending confirmation** = an assistant recommendation not yet explicitly confirmed. This log has been consolidated: entries fully superseded by a later decision are merged into that later entry rather than kept as separate historical rows, and terminology has been updated throughout to the current naming (`Object`/`obj_id`/`obj_mark`, `Identity`, `Reinforcement`, `BarSpec`, `Section`).

## 4.1 Naming & Terminology

| # | Decision | Status |
|---|---|---|
| D1 | `Storey` renamed to `Floor` | ✅ **Decided.** Matches the wording used in the source document; requires updating all references (foreign keys, endpoints, seed data) |
| D2 | `Dimension` renamed to `Section`, primary key renamed to `sect_id`, composite with `obj_type` | ✅ **Decided.** Avoids confusion with the "dimension table" concept from data warehousing terminology; refers to a structural cross-section (e.g. a 400x400 column section) |
| D3 | The fact table and its identifier fields use `objects` / `obj_id` / `obj_mark` / `obj_type` naming, matching the ERD authored independently, rather than `members` / `member_id` / `member_mark` used earlier in design discussion | ✅ **Decided.** `obj_mark` is the human-readable engineering mark (e.g. "C1.02.001"), matching the source document's own identifier table concept, kept separate from `obj_id` (the surrogate key, see D4) |

## 4.2 Identity Model

| # | Decision | Status |
|---|---|---|
| D4 | Identity structure: separate `Identity` table (table name: `identities`) vs. columns directly on `Object` | ✅ **Decided — separate table.** Necessary because the change-status/active-status workflow depends on identity being tracked independently from per-revision fact rows. If `stable_id` lived directly on `Object`, it would be duplicated across every revision row for the same real-world object, with no guarantee those copies stay in sync |
| D5 | `Section` composite key `(sect_id, obj_type)` retained instead of collapsing to `sect_id` alone | ✅ **Decided — keep composite.** Relying on a naming convention (e.g. `sect_id` always starting with "C" for column) instead of an enforced schema rule risks a silent mismatch between a section's prefix and its declared `obj_type`. The composite key makes the database reject that mismatch structurally |
| D6 | Stable ID assignment when IFC GlobalId is absent | ✅ **Decided — manual, human-declared** (via an `is_new` input flag). Marked **ASSUMPTION FOR TRAINING ONLY** — no source document specifies this mechanism explicitly. Without an external IFC identifier to match against, there is no way for the system to determine automatically whether an uploaded object is new or a continuation of an existing one |
| D7 | Duplicate/error detection during stable_id assignment | ✅ **Decided — designed, not built for Week 3.** `stable_id` assignment is treated as predetermined and correct by assumption; human error is an accepted risk. A robust check would require fuzzy-matching logic, outside this week's scope |
| D8 | Should `building_id` be duplicated onto `Object` for query convenience? | ✅ **Decided — no.** Building context is derivable transitively via `Object.floor_id → Floor.building_id`. Duplicating it risks two sources of truth disagreeing. Querying "all objects in Building X" is answered with a JOIN, not a stored field |

## 4.3 Revision Model

| # | Decision | Status |
|---|---|---|
| D9 | Revision strategy: full snapshot vs. diff-only | ✅ **Decided — full snapshot.** Confirmed against the *AISIMS & AIVISTA System Orientation Brief*, Section 6: a revision is a snapshot, not an edit; each new revision regenerates its own complete data set from the base revision, which continues to exist afterward, unaltered |
| D10 | Revision lifecycle and the role of staging | ✅ **Decided.** A staging step exists conceptually: incoming data can be diffed against the previous revision before being committed. Staging is explicitly a **pre-system stage** — it happens before data is considered part of the system's revision history at all. It leaves no record on the `Revision` table |
| D11 | Enforcing linearity (no branching) | ✅ **Decided — enforced via a computed `rev_number` (integer), not a self-referencing FK.** A self-referencing `rev_base_id` column only checks that its target exists, not that the target is the latest revision — a row could still be inserted pointing at an old revision, which is a branch in every way that matters. `rev_number` closes this: "based on" is never stored as a free choice, it is always `rev_number - 1` within the same `building_id`, computed rather than input, enforced by a unique constraint on `(building_id, rev_number)`. This also means `rev_id` itself is free to use any format, since uniqueness no longer depends on it |
| D12 | Which revision counts as "current" | ✅ **Decided — latest by default** (highest `rev_number` per building). Consistent with the Orientation Brief principle that "the current design is always a named thing," and a direct consequence of D10+D11 |
| D13 | Revision provenance (who created it, and why) | ✅ **Decided — out of scope for Week 3.** The system accepts a valid input without recording authorship or rationale |
| D14 | Trigger condition for a new `revision_id`: any data change vs. only Project Design changes | ✅ **Decided — Project Design only.** Adding a Floor, Material, or BarSpec entry does not itself create a new revision; only Object data (added/modified/deleted/restored) does |
| D15 | Revision trigger mode: Bulk Upload vs. Interactive Edit | ✅ **Decided — both, with different mechanics**, realized as two separate API endpoints (see D33). *Bulk Upload* requires the full two-level comparison in D19, since the incoming data carries no information about what was deliberately touched. *Interactive Edit* determines status directly from which objects the user actually touched |
| D16 | `obj_mark` on restore: preserved vs. recalculated | ✅ **Decided — neither, by design.** Since `obj_mark` is Human Input (uploaded with each submission, not derived — see D3), a restored object's mark is simply whatever the person uploads at restoration time. There is no automatic preservation and no recalculation step; this follows the same rule as any other Human Input field |
| D17 | Change status values and the "repeated deletion" guard | ✅ **Decided.** Five values: `added` / `modified` / `unchanged` / `deleted` / `restored`. An object missing from the current upload is only flagged `deleted` once, checked via two conditions: (1) it existed in the previous baseline, and (2) its `Identity.is_active` flag is currently `true`. Checking existence alone would regenerate the `deleted` row every subsequent revision |
| D18 | Three-workflow structure per revision | ✅ **Decided.** (1) **Stable ID Assignment** — determines which `stable_id` an incoming row belongs to, new or reused; (2) **Change Status Determination** — a per-row loop assigning added/modified/unchanged/restored; (3) **Active Status Sync** — an end-of-batch pass assigning `deleted` and flipping `is_active` to false for anything missing from the upload. `restored` belongs in Workflow 2, not Workflow 3 |
| D19 | Comparison logic for Change Status Determination | ✅ **Decided — two levels.** Must compare both the Object's own columns (geometry, section, material, floor, zone) AND every associated `Reinforcement` row against the previous revision's baseline. Comparing Object columns alone would misclassify a reinforcement-only change as `unchanged`. Does not require `stable_id` duplicated onto `Reinforcement`: the lookup path is `stable_id → (previous) Object.obj_id → Reinforcement.obj_id`, consistent with the transitivity principle in D8 and D22 |

## 4.4 Reinforcement & Quantity

| # | Decision | Status |
|---|---|---|
| D20 | Identity/tracking for Reinforcement and Quantity | ✅ **Decided.** Reinforcement is treated as an attribute of the Object (like Section or Material) — a change makes the Object `modified`, with no separate stable identity of its own. Quantity is a derived/calculated output, not an input |
| D21 | Direction of the foreign key between `Reinforcement` and `Object` | ✅ **Decided — `reinforcements.obj_id` points to `objects.obj_id`,** not the reverse. Reinforcement can only exist once its object exists — unlike Material or BarSpec, which can be defined in the catalog ahead of any object using them |
| D22 | `Reinforcement` does not carry its own `rev_id` or `stable_id` | ✅ **Decided.** Both are derivable transitively via `Reinforcement.obj_id → Object.rev_id` / `Object.stable_id`. A direct consequence, combined with full-snapshot (D9): every `Reinforcement` row is rebuilt alongside its Object on every revision, even for objects that are themselves `unchanged` — an accepted storage cost |
| D23 | Quantity calculation formula | ✅ **Decided.** `qty_sect` (section/concrete volume, mm³): for `column`/`beam`, `width × depth × extent` where width/depth come from `Section.dimension` and extent is the 3D Euclidean distance between the object's two `geometry_points`; for `slab`/`wall`, `thickness × polygon_area` where thickness comes from `Section.dimension` and polygon_area is computed using the general 3D planar polygon method (not a naive 2D shoelace formula, since a wall's polygon is not necessarily horizontal). `qty_bar` (total reinforcement length, mm): sum of `bar_count × bar_len` across every `Reinforcement` row belonging to the object |

## 4.5 Project Configuration vs. Project Design

| # | Decision | Status |
|---|---|---|
| D24 | Overall input architecture | ✅ **Decided — split into two groups.** *Project Configuration* (Building, Floor, Zone, Material, Section, BarSpec, Grid) is set up independently, ahead of any revision cycle, and now has its own POST endpoints (see D38). *Project Design* (Object, Reinforcement, and derived output like Quantity) flows through the revision workflow |
| D25 | Floor elevation: editable vs. append-only | ✅ **Decided — append-only**, same treatment as Material. If elevation could be edited directly, an Object left `unchanged` in a later revision could silently shift position with no revision trail recording it |
| D26 | `Section` / `Grid` also append-only | ✅ **Decided.** Follows directly from the snapshot principle (D9) — the old row is retained untouched, a new row is created for any change |
| D27 | Propagation of freely-editable fields (e.g. `Building.building_name`, `Floor.floor_name`, `Zone.pour_seq`) to Objects created in earlier revisions | ✅ **Decided — propagates automatically, by design.** `objects` stores only the referencing ID, never a copy of the descriptive value — editing the Config row directly is reflected for every Object referencing it, in any revision, the moment it's displayed via a join. Deliberate opposite of append-only fields like `elevation` |
| D28 | `Floor.floor_name` — nullable vs. required | ✅ **Decided — required.** The only field guaranteed to carry human-readable positional meaning for a floor, since `floor_id` is a surrogate key not meant to convey meaning (e.g. `"FL-002"` is not guaranteed to mean "the 2nd floor") |
| D29 | `Section.sect_label` — nullable vs. required | ✅ **Decided — required, unlike other cosmetic name fields** (`Building.building_name`, `Material.mat_name`, which stay optional). A section must reliably communicate its actual cross-section identity to an engineer, and `sect_id` cannot be relied on for that (D5 — its prefix is not a guaranteed indicator of `obj_type`) |
| D41 | `Zone.zone_label` — new required field | ✅ **Decided.** Zone previously had no human-readable identifier at all — `zone_id` is an opaque surrogate key and `pour_seq` is a plain ordering integer, neither of which lets an engineer identify a zone by name. Same reasoning as D28/D29 |
| D42 | `Project.project_name` / `Building.building_name` — nullable vs. required | 🔶 **Proposed — pending confirmation.** Same gap identified in the D41 audit: each currently has exactly one descriptive field, and it's optional — no fallback exists if left blank |
| D43 | `Material.mat_name` — nullable vs. required | 🔶 **Proposed — pending confirmation.** Borderline case: unlike Project/Building/Zone, `Material` has two other required fields (`mat_type`, `mat_strength`) whose combination already conveys meaningful information (e.g. "concrete, 250"), even without a name |

## 4.6 Geometry & Location

| # | Decision | Status |
|---|---|---|
| D30 | `floor_id` kept as explicit human input, not derived from `geometry_points` | ✅ **Decided.** Auto-assignment is unambiguous for horizontal objects but ambiguous for vertical ones (a column spans two floors; which one it "belongs to" is an engineering convention, not a computable fact). A validation warning flags a mismatch without blocking input |
| D31 | Relationship between `Grid` and `Object` | ✅ **Decided — none, by design.** `Grid` stores only `grid_label`, `grid_axis`, and `grid_coord`, used solely for generating drawings by overlaying grid lines and object geometry on the same coordinate space — never joined against Object data in a query, the same way a grid line and a column simply occupy the same drawing canvas without any database relationship connecting them |

## 4.7 Pre-Validation Gate

| # | Decision | Status |
|---|---|---|
| D32 | Two-check pre-validation gate | ✅ **Decided.** (1) *Referential Existence*: every reference to Project Configuration in the upload must already exist — resolved by natural name, scoped appropriately (see D44), not by raw ID. (2) *Contextual Completeness*: required fields evaluated conditionally (see VR-06, VR-07, VR-10). On failure, the entire batch is rejected with a complete list of every problem found |

## 4.8 API & Endpoint Design

| # | Decision | Status |
|---|---|---|
| D33 | Bulk Upload and Interactive Edit as two separate endpoints, rather than one endpoint that infers intent | ✅ **Decided.** "Absent from the payload" means opposite things in each mode — in Bulk Upload it means *deleted*, in Interactive Edit it means *untouched*. A single endpoint cannot safely tell these apart |
| D34 | The Interactive Edit endpoint handles add, change, and delete in a single request, not three separate endpoints | ✅ **Decided.** `changed_objects` covers both additions and modifications (via the `is_new` flag). `deleted_stable_ids` covers deletions explicitly. Everything else is carried forward unchanged automatically |
| D35 | Nested vs. flat structure for `reinforcements` in the request body | ✅ **Decided — nested inside each object**, not a separate top-level array. Workflow 2's comparison (D19) treats an object and its reinforcement as one unit; a flat array would need re-matching with no benefit |
| D36 | Input mechanism for both endpoints | ✅ **Decided — plain JSON request body**, no custom upload form or CSV parser. `/docs` (Swagger UI) serves as the interface for manual testing |
| D37 | URL structure: fully nested (`/projects/{id}/buildings/{id}/...`) vs. building-scoped only | ✅ **Decided — fully nested.** Requires validating that the given `building_id` actually belongs to the given `project_id` on every request (404/400 on mismatch) |
| D38 | POST endpoints for Project Configuration | ✅ **Decided — all entities get one** (Project, Building, Floor, Zone, Material, Section, BarSpec, Grid), so initial setup can happen from user input rather than only seed scripts. No new synthetic data is generated alongside this — existing seeded rows are left as-is |
| D39 | GET endpoints for browsing the hierarchy | ✅ **Decided.** `Project → Building → Revision → Object`, with list/detail responses resolving foreign keys to their descriptive values (floor name, zone, section, material) rather than returning bare IDs — the "Combined View" pattern |
| D40 | Frontend display and UI investment level | ✅ **Decided.** Matches the existing Week 2 UI style and component patterns (not restricted to bare-minimum) for browsing only — project/building/revision selectors, an object list showing `obj_mark` (labeled "Member ID" for continuity with Week 2) plus `stable_id` and resolved details, and an object detail view adding geometry, reinforcement, and quantity. Creation/editing remains `/docs`-driven (D36), not built into this UI |
| D46 | ID generation scheme for system-generated primary keys | ✅ **Decided — prefixed, sequential IDs** (e.g. `OBJ-001`, `RBAR-0001`, `FL-001`), backed by a real Postgres `SEQUENCE` per entity (not a naive `SELECT MAX+1`, which is race-prone under concurrent writes). Rejected the initially-implemented `uuid4()` scheme: a database record still needs to be readable by the developers maintaining it, not only machine-consumable. `stable_id` is the sole exception, remaining a UUID (D6) — its purpose is to be an internal, opaque, revision-proof anchor, not a human-facing reference. `Reinforcement.bar_id` uses prefix `RBAR-`, kept distinct from `BarSpec.barspec_id`'s `BAR-` prefix to avoid the two colliding in logs/debugging |
| D47 | `obj_type` enumeration: abbreviated 4-type list vs. full 6-type list | ✅ **Decided — full names, full list.** The Week 2-inherited `('col', 'beam', 'wall', 'slab')` is corrected to `('column', 'beam', 'wall', 'slab', 'footing', 'stair')`, matching the member types named in the source documents and already implied by VR-10/D19. Point-representation classification: `column`, `beam`, `footing` are axis-point (2 `geometry_points`); `wall`, `slab`, `stair` are boundary-point (≥3 `geometry_points`) |
| D44 | `ObjectInput` field resolution: raw IDs (`floor_id`, `zone_id`, `sect_id`, `mat_id`, `barspec_id`) vs. natural/human-readable identifiers | ✅ **Decided — natural identifiers.** A structural engineer will never manually look up an opaque database row ID to know which floor or section they mean — not through a future frontend, and not even for a bulk CSV-style upload, where the natural engineering property (a floor's name, a section's label) is what's actually on hand. `ObjectInput` therefore takes `floor_name`, `zone_label`, `sect_label` (+`obj_type`), `mat_name`, and `barspec_dia`+`barspec_type`+`barspec_grade` (BarSpec has no single label — see D-series on BarSpec identity). Resolution to the underlying ID happens server-side during the Pre-Validation Gate, using the `building_id`/`project_id` already present in the URL path (D37) — no new field is added to `Object` or `ObjectInput` to carry building context, since it was never missing to begin with |
| D45 | Uniqueness constraints required to make D44 safe | ✅ **Decided — confirmed and broadened.** `Floor.floor_name` unique per `building_id` (Option A: scoped, not global — two different buildings may each have their own "Level 2"); `Zone.zone_label` unique per `building_id`; `Section.sect_label` unique globally; `Material.mat_name` unique globally; `BarSpec.barspec_label` unique globally (a new field added directly in the person's own Data Dictionary — BarSpec previously had no single label field, identified only by the `barspec_dia`+`barspec_type`+`barspec_grade` combination; `barspec_label` supplements rather than replaces that combination). Extended further, beyond D44's original scope: `Project.project_name` and `Building.building_name` are also unique globally, so that `building_id`/`project_id` each resolve to exactly one unambiguous name — supporting a future frontend that may display buildings by name alone (e.g. for selecting which building to edit a revision under), and CSV-style input that refers to a building by name. This also resolves the previously open D43: `Material.mat_name` is `not null` (a nullable field cannot function as a lookup key) |

---

# 5. Validation Rules (Draft)

| Rule ID | Field | Condition | Severity | Status |
|---|---|---|---|---|
| VR-01 | `Building.building_name` | Freely editable | *(no rule needed)* | ✅ Decided |
| VR-02 | `Floor.elevation` | Append-only once referenced | Warning | ✅ Decided |
| VR-03 | `Material.compressive_strength_kg_cm2` | Append-only once referenced | Warning | ✅ Decided |
| VR-04 | `BarSpec` (diameter, grade) | Append-only once referenced | Warning | ✅ Decided |
| VR-05 | `Zone.pour_seq` | Freely editable | *(no rule needed)* | ✅ Decided |
| VR-06 | `reinforcements.bar_space`, `bar_hook_type` | Required when `bar_role='transverse'`, optional otherwise | Error | ✅ Decided — built into the Pre-Validation Gate (D32) and relied on since |
| VR-07 | `objects.geometry_points` | Exactly 2 points for column/beam; ≥3 for wall/slab | Error | ✅ Decided — built into the Pre-Validation Gate (D32) and relied on since |
| VR-08 | All referenced FKs (`floor_id`, `zone_id`, `sect_id`+`obj_type`, `mat_id`, `barspec_id`) | Must exist in Project Configuration | Error | ✅ Decided |
| VR-09 | `Section.dimension`, `Grid` position fields | Same append-only treatment as VR-02/03 | Warning | **Recommended, not formally assigned** |
| VR-10 | `Section.dimension` shape, by `obj_type` | Must contain `width` + `depth` (both > 0) for rectangular `column`/`beam`; must contain `diameter` (> 0) for circular `column`/`beam`; must contain `thickness` (> 0) for `slab`/`wall`/`stair` | Error | ✅ Decided — required for the Quantity formula (D23) to be computable at all. Extended to cover the `circular` shape variant already present in seed data (`{"shape": "circular", "diameter": ...}`), which the original wording did not account for |
| VR-11 | `Object.reinforcements` array cardinality, by referenced `Material.mat_type` | If `mat_type = 'concrete'`: the object must have at least one `Reinforcement` row. If `mat_type = 'steel'`: zero `Reinforcement` rows is valid (a steel member has no embedded rebar) | Error | ✅ Decided. This is a cardinality rule (how many rows may exist), not a field-level nullability rule — every field within a `Reinforcement` row that does exist stays exactly as required/optional as already defined (VR-06 unchanged). A steel object with zero reinforcement rows naturally yields `qty_bar = 0`, not an error |

---

*End of document.*
