---
title: "Week 3 Deliverable Plan"
subtitle: "AISIMS Data Structure — To-Do List & Cautions"
author: "Daffa"
date: "September 2026"
geometry: margin=2.2cm
fontsize: 10pt
---

# 1. Purpose

This document consolidates the Week 3 to-do list derived from the *Week 2 Review & Week 3 Assignment Instruction* (Sections 7–14), cross-referenced against working discussions on hierarchy, revision modeling, and identity design. It is organized into deliverable categories and a set of cautions to review before execution and submission.

---

# 2. To-Do List per Deliverable Header

## 2.1 Written Deliverables (Tulisan)

| # | Item | Notes | Source |
|---|------|-------|--------|
| 1 | ERD / schema diagram — Draft v0.1 | Concept discussed; must be self-authored first (see Caution 1) | Sec 8.2, 8.9 |
| 2 | Data Dictionary for all entities | Field name, meaning, type, required/optional, unit, example, source, relationship, validation note | Sec 8.4 |
| 3 | Identity & Revision Note | Define Stable Internal ID, Member Code/Mark, IFC GlobalId, Revision ID separately. Include two worked examples: (a) a beam whose section changes, (b) a beam whose location changes | Sec 8.3 |
| 4 | Key Relationship Description | One-to-many, reusable-reference, and revision relationships | Sec 8.4 / 10 |
| 5 | Geometry Representation Note | Axis-point representation for column/beam vs. ordered boundary points for wall/slab; units, point order, closure, local/global coordinates, member orientation, limitations | Sec 8.5 |
| 6 | Training Revision Model write-up | Explain snapshot approach; how the same member links across Revision A and B; how changed attributes are represented; how added/deleted members are handled. Must be labeled "Training Proposal," not a production rule | Sec 8.7 |
| 7 | Candidate Validation Rules (10–15) | Each with Rule ID, Object/Field, Condition, Expected Result, Severity/Review Status, Rationale. Must also cover the 14-item minimum coverage list | Sec 8.8, Sec 9 |
| 8 | Updated Outstanding Questions | Assign a status to every question — OPEN / ASSUMPTION FOR TRAINING ONLY / RESOLVED FROM DOCUMENT / OUT OF CURRENT WEEK SCOPE — including new questions raised by identity, revision, hierarchy, and geometry decisions | Sec 8.10 |
| 9 | AI Tool Usage Log | Continuous log. Must include at least one AI suggestion that was rejected or modified, not only accepted ones | Sec 10 |

## 2.2 Presentation (Presentasi)

| # | Item | Notes | Source |
|---|------|-------|--------|
| 10 | Short explanation / presentation, 5–10 minutes | Explain the model and identity/revision decisions in own words. No polished UI demo required | Sec 10 |

## 2.3 Codebase (Codebase Baru)

| # | Item | Notes | Source |
|---|------|-------|--------|
| 11 | Create Week 3 branch from the accepted Week 2 baseline | Must happen before any development work begins | Sec 8.1 |
| 12 | Implement new tables: `Project`, `Building`, `Revision`, `ReinforcementBar` (conceptual), `Quantity` (conceptual) | Conceptual scope only — no detailed rebar algorithm or BOQ calculation | Sec 8.6 |
| 13 | Update existing tables: `Floor` (+ `building_id`), `Member` (+ `revision_id`) | From working discussion |  |
| 13b | Decide identity model structure: separate `MemberIdentity` table (`stable_id`, `ifc_global_id`) vs. columns directly on `Member` | **Open — still forming up**, see Section 4 | Working discussion |
| 14 | Alembic migration with backfill | Existing 12 seed rows need default values for new columns before they are locked to NOT NULL | From working discussion |
| 15 | Enforce validation rules as real database constraints where feasible | CheckConstraint, UniqueConstraint, ForeignKey | From working discussion |
| 16 | Update `main.py` (query params: project, building, revision) and `schemas.py` | From working discussion |  |
| 17 | Repository evidence | Commits follow branch → test → PR/CI → merge discipline; CI must remain green | Sec 10 |

---

# 3. Things to Be Cautious About

**1. ERD Draft v0.1 must be self-authored, without AI.**
The instruction is explicit: *"Create ERD/Data Model Draft v0.1 without asking Claude/Codex to design it for you. After your draft is complete, you may ask AI to critique it."* Discussions held so far (Project/Building/Revision structure, reinforcement approach, etc.) are useful as learning input, but copying them directly into Draft v0.1 without redrawing it independently would not satisfy this requirement. The safe path: draw an independent v0.1 first, then request AI critique, and record that process in the AI Tool Usage Log.

**2. Ten Review Questions must be answerable without AI (Section 11).**
Example: *"Why can B1.02.A1A2 be a useful member code but a poor stable primary identity?"* Practice answering these independently before submission, since they are likely to be asked directly.

**3. The AI Tool Usage Log must record at least one rejected or modified AI suggestion.**
Not only accepted ones. Several open design choices from this preparation phase (e.g., full-snapshot vs. diff-only revisioning, cross-table validation approaches) are good candidates if any get revised or rejected.

**4. The revision model must be explicitly labeled "Training Proposal."**
It should not be presented as a finalized or production-ready design (Sec 8.7).

**5. Reinforcement and Quantity are conceptual entities only (Sec 8.6).**
Avoid building a detailed bar-bending-schedule algorithm or real BOQ computation — that is outside Week 3 scope.

**6. The Geometry Representation Note is a separate written deliverable not yet addressed.**
Easy to overlook given how much discussion has focused on revision and identity.

**7. Outstanding Questions require an explicit status.**
Do not leave any unstated, and do not silently treat an open question as a final decision.

---


# 4. Design Decisions Log

Status tags: **✅ Decided** = explicitly stated, confirmed, or built upon consistently without objection. **🔶 Proposed — pending confirmation** = an assistant recommendation not yet explicitly confirmed. Numbering is sequential within topic groups and has been reset from earlier drafts as items were merged or removed.

## 4.1 Naming & Terminology

| # | Decision | Status |
|---|---|---|
| D1 | `Storey` renamed to `Floor` | ✅ **Decided.** Matches the wording used in the source document; requires updating all references (foreign keys, endpoints, seed data) |
| D2 | `Dimension` renamed to `Section`, primary key renamed to `sect_id` | ✅ **Decided.** Avoids confusion with the "dimension table" concept from data warehousing terminology; refers to a structural cross-section (e.g. a 400x400 column section) |
| D3 | `member_code` renamed to `member_mark` | ✅ **Decided.** Matches the terminology used in the source document's own identifier table (Member Mark / IFC GlobalId / Stable ID / Revision ID) and avoids implying it is a database-internal field |

## 4.2 Identity Model

| # | Decision | Status |
|---|---|---|
| D4 | Identity structure: separate `MemberIdentity` table vs. columns directly on `Member` | ✅ **Decided — separate table.** Necessary because the change-status/active-status workflow depends on identity being tracked independently from per-revision fact rows. If stable_id lived directly on Member, it would be duplicated across every revision row for the same object, with no guarantee those copies stay in sync |
| D5 | `Section` composite key `(sect_id, member_type)` retained instead of collapsing to `sect_id` alone | ✅ **Decided — keep composite.** Relying on a naming convention (e.g. sect_id always starting with "C" for column) instead of an enforced schema rule risks a silent mismatch between a section's prefix and its declared member_type. The composite key makes the database reject that mismatch structurally rather than trusting the prefix |
| D6 | Stable ID assignment when IFC GlobalId is absent | ✅ **Decided — manual, human-declared** (via an `is_new` input flag). Marked **ASSUMPTION FOR TRAINING ONLY** — no source document specifies this mechanism explicitly; it is the product of reasoning built during this preparation phase. Without an external IFC identifier to match against, there is no way for the system to determine automatically whether an uploaded member is new or a continuation of an existing one — a human declaring it is the only option when that anchor is missing |
| D7 | Duplicate/error detection during stable_id assignment | ✅ **Decided — designed, not built for Week 3.** `stable_id` assignment is treated as predetermined and correct by assumption; human error is an accepted risk. A robust check would require fuzzy-matching logic (e.g. for a member that both shifted position and changed section but is still logically the same object), which is outside this week's scope |
| D8 | Should `building_id` be duplicated onto `Member` for query convenience? | ✅ **Decided — no.** Building context is already derivable transitively via `Member.floor_id → Floor.building_id`. Duplicating it risks two sources of truth disagreeing (e.g. floor_id pointing to a floor in Building A while a redundant building_id column says Building B). Querying "all members in Building X" is answered with a JOIN, not a stored field |

## 4.3 Revision Model

| # | Decision | Status |
|---|---|---|
| D9 | Revision strategy: full snapshot vs. diff-only | ✅ **Decided — full snapshot.** Confirmed against the *AISIMS & AIVISTA System Orientation Brief*, Section 6: a revision is a snapshot, not an edit; each new revision regenerates its own complete data set from the base revision, which continues to exist afterward, unaltered |
| D10 | Revision lifecycle and the role of staging | ✅ **Decided.** A staging step exists conceptually: incoming data can be diffed against the previous revision before being committed as an official new revision. Staging is explicitly a **pre-system stage** — it happens *before* data is considered part of the system's revision history at all, not a state within it. Because of this, staging leaves no record on the `Revision` table; a `Revision` row is only created once data is actually committed |
| D11 | Linear vs. branching revision history | ✅ **Decided — out of scope for branching, linear by default.** Consequence of D10: since committing a revision is deliberately made "expensive" (requires staging/approval first), exploring multiple design alternatives happens outside the system entirely; only the final chosen version is ever uploaded. *Enforcement mechanism refined in D30.* |
| D12 | Which revision counts as "current" | ✅ **Decided — latest by default.** Consistent with the Orientation Brief principle that "the current design is always a named thing" (unambiguous), and a direct consequence of D10+D11. *(Sourcing caveat: this specific mechanism is not a literal quote from the pack, but a reasonable inference built on top of it.)* |
| D13 | Revision provenance (who created it, and why) | ✅ **Decided — out of scope for Week 3.** The system accepts a valid input without recording authorship or rationale behind a revision |
| D14 | Trigger condition for a new `revision_id`: any data change vs. only Project Design changes | ✅ **Decided — Project Design only.** Adding a Floor, Material, or Reinforcement Spec entry does not itself create a new revision; only Member data (added/modified/deleted/restored) does, since Project Configuration is set up independently of any revision cycle (see D23) |
| D15 | Revision trigger mode: bulk upload vs. interactive edit | ✅ **Decided — both, with different mechanics.** *Bulk Upload* (external data, full re-submission) requires the full attribute comparison in D19 to determine each member's status, since the incoming data carries no information about what was deliberately touched. *Interactive Edit* (UI-driven) determines status directly from which members the user actually touched — an untouched member is carried forward as `unchanged` without needing comparison, since the UI already knows what was and wasn't edited |
| D16 | Member mark on restore: keep the pre-deletion mark vs. recalculate | ✅ **Decided — recalculated from current attributes.** Consistent with member_mark being derived from location/section/storey rather than being part of the member's permanent identity — a restored member's mark reflects its latest uploaded attributes, not whatever it happened to be before deletion |
| D17 | Change status values and the "repeated deletion" guard | ✅ **Decided.** Five values: `added` / `modified` / `unchanged` / `deleted` / `restored`. A member missing from the current upload is only flagged `deleted` once, checked via two conditions together: (1) it existed in the previous baseline, and (2) its `MemberIdentity.is_active` flag is currently `true`. Checking existence alone would cause the `deleted` row to be regenerated in every subsequent revision, since a deleted row itself "exists" in the previous baseline |
| D18 | Three-workflow structure per revision | ✅ **Decided.** (1) *Stable ID Assignment* — determines which stable_id an incoming row belongs to, new or reused; (2) *Change Status Determination* — a per-row loop assigning added/modified/unchanged/restored; (3) *Active Status Sync* — an end-of-batch pass assigning `deleted` and flipping `is_active` to false for anything missing from the upload. `restored` belongs in Workflow 2, not Workflow 3, since it applies to a row present in the current upload |
| D19 | Comparison logic for Change Status Determination, and reinforcement's place in it | ✅ **Decided — two levels.** Must compare both the Member's own columns (geometry, section, material, floor, zone) AND every associated `ReinforcementBar` row against the previous revision's baseline. Comparing Member columns alone would misclassify a reinforcement-only change as `unchanged`. This does **not** require `stable_id` to be duplicated onto `ReinforcementBar`: since `ReinforcementBar` already carries `member_id`, the lookup path is `stable_id → (previous) Member.member_id → ReinforcementBar.member_id` — a two-hop join through Member, consistent with the same transitivity principle used in D8 and D22 |

| D30 | Enforcing linearity (D11): self-referencing `rev_base_id` vs. a computed `rev_number` | ✅ **Decided — replace `rev_base_id` with `rev_number` (integer, unique per `building_id`).** A self-referencing `rev_base_id` column only checks that its target exists, not that the target is the latest revision — a row could still be inserted pointing at an old revision, which is a branch in every way that matters, even though D11 rules branching out. `rev_number` closes this: "based on" is never stored as a free choice, it is always `rev_number - 1` within the same building, computed rather than input. This also resolves the earlier "REV-00 collision across buildings" concern from the ERD v0.1 critique, since uniqueness is enforced on `(building_id, rev_number)`, leaving `rev_id` itself free to use any format |

## 4.4 Reinforcement & Quantity

| # | Decision | Status |
|---|---|---|
| D20 | Identity/tracking for Reinforcement and Quantity | ✅ **Decided.** Reinforcement is treated as an attribute of the Member (like Section or Material) — a change makes the Member `modified`, with no separate stable identity of its own. Quantity is a derived/calculated output, not an input — it follows whatever the Member's revision produces, rather than having its own added/modified/deleted lifecycle |
| D21 | Direction of the foreign key between `ReinforcementBar` and `Member` | ✅ **Decided — `ReinforcementBar.member_id` points to `Member`,** not the reverse. Reinforcement can only exist once its member exists — unlike Material or Reinforcement Spec, which can be defined in the catalog ahead of any member using them. Putting the foreign key on Member instead would incorrectly imply reinforcement can be defined independently and then attached, contradicting this dependency |
| D22 | `ReinforcementBar` does not carry its own `revision_id` or `stable_id` | ✅ **Decided.** Revision context is derivable transitively via `ReinforcementBar.member_id → Member.revision_id`, and identity context via that same path to `Member.stable_id` (see D19) — adding either as a redundant column risks disagreement with what `member_id` actually resolves to. A direct consequence of this, combined with the full-snapshot principle (D9): because every revision generates a new `member_id` for every Member row (including unchanged ones), every associated `ReinforcementBar` row is rebuilt alongside it on every revision — an accepted storage cost, not a defect, and not something requiring a dedicated workflow of its own |

## 4.5 Project Configuration vs. Project Design

| # | Decision | Status |
|---|---|---|
| D23 | Overall input architecture | ✅ **Decided — split into two groups.** *Project Configuration* (Building, Floor, Zone, Material, Section, Reinforcement Spec, Grid) is set up independently, ahead of any revision cycle. *Project Design* (Member, ReinforcementBar, and derived output like Quantity) flows through the revision workflow. Design input references/assigns configuration IDs rather than redefining them inline — analogous to setting up a catalog once in ETABS before members are assigned to it |
| D24 | Floor elevation: editable vs. append-only | ✅ **Decided — append-only**, same treatment as Material. If elevation could be edited directly, a Member left `unchanged` in a later revision could silently shift position with no revision trail recording it, undermining the snapshot guarantee established in D9 |
| D25 | `Section` / `Grid` also append-only | ✅ **Decided.** Follows directly from the snapshot principle (D9): append-only means the old row is retained untouched, never edited or deleted, with a new row created for any change — the same guarantee already given to Material and Floor elevation |
| D31 | Propagation of freely-editable fields (e.g. `Building.building_name`, `Floor.floor_name`, `Zone.pour_seq`) to Objects created in earlier revisions | ✅ **Decided — propagates automatically, by design.** `objects` stores only the referencing ID (`floor_id`, `zone_id`, etc.), never a copy of the descriptive value itself. Because these fields are not append-only, editing them directly is automatically reflected for every object referencing that row, in any revision, the moment it is displayed via a join — no separate propagation mechanism is needed. This is the deliberate opposite of append-only fields like `elevation` (D24/D25), which must stay frozen to their historical value instead |
| D32 | `Floor.floor_name` — nullable vs. required | ✅ **Decided — required (`not null`).** Direct consequence of rejecting a separate `floor_number` field: `floor_id` is a surrogate key not meant to convey meaning (e.g. `"FL-002"` is not guaranteed to mean "the 2nd floor" — it could just as easily be the ground floor of the second building processed). Without a `floor_number`, `floor_name` becomes the only field guaranteed to carry human-readable positional meaning, so unlike `Building.building_name`/`Project.project_name`/`Material.mat_name` (which stay optional as pure bonus labels), it cannot be left optional |

## 4.6 Geometry & Location

| # | Decision | Status |
|---|---|---|
| D26 | `floor_id` kept as explicit human input, not derived from `geometry_points` | ✅ **Decided.** Auto-assignment is unambiguous for horizontal members (a beam sits at exactly one elevation) but ambiguous for vertical ones (a column spans two floors, and which one it "belongs to" is an engineering convention, not a computable fact). A validation warning flags a mismatch between geometry and the selected Floor without blocking the input |
| D27 | Grid as a formal FK on `Member` | **Resolved — see D28.** D28 goes further than "not built yet": Grid is never related to Member at all, by design |
| D28 | Eliminate any relationship between `Grid` and `Member` entirely | ✅ **Decided.** `Grid` stores only `grid_label`, `axis` (X or Y), and `coord`, used solely for generating drawings by overlaying grid lines and member geometry on the same coordinate space — never joined in a query, the same way a grid line and a column simply occupy the same drawing canvas without any database relationship connecting them. `member_mark` drops its grid segment entirely, becoming a pure function of `sect_id` + `floor_id` + a sequence number, fully system-generatable with no manual component |

## 4.7 Pre-Validation Gate

| # | Decision | Status |
|---|---|---|
| D29 | Two-check pre-validation gate | ✅ **Decided.** (1) *Referential Existence*: every FK referenced in the upload (floor_id, zone_id, sect_id+member_type, material_id, spec_id) must already exist in Project Configuration. (2) *Contextual Completeness*: required fields are evaluated conditionally, not as a blanket non-null check (see VR-06, VR-07). Both checks run before Workflows 1–3; on failure, the entire batch is rejected with a complete list of every problem found, not just the first one encountered |

## 4.8 API & Endpoint Design

| # | Decision | Status |
|---|---|---|
| D33 | Bulk Upload and Interactive Edit as two separate endpoints, rather than one endpoint that infers intent | ✅ **Decided.** "Absent from the payload" means opposite things in each mode — in Bulk Upload it means *deleted* (the payload is a complete restatement of the building), in Interactive Edit it means *untouched* (the payload only contains what was actually touched in the UI). A single endpoint cannot safely tell these apart, so each mode gets its own route: `POST /buildings/{building_id}/revisions/bulk` (full payload; anything absent triggers Workflow 3's `deleted` path) and `POST /buildings/{building_id}/revisions/edit` (only touched objects, plus an explicit deletion list; every other `stable_id` from the previous revision is duplicated forward automatically as `unchanged`) |
| D34 | The Interactive Edit endpoint handles add, change, and delete in a single request, not three separate endpoints | ✅ **Decided — confirmed.** `changed_objects` covers both additions and modifications, distinguished internally via the `is_new` flag (D6/D8: `is_new: true` generates a new `stable_id`, `false` reuses an existing one). `deleted_stable_ids` covers deletions explicitly. Everything not mentioned in either list is carried forward unchanged automatically |
| D35 | Nested vs. flat structure for `reinforcements` in the request body | 🔶 **Proposed — pending confirmation.** Reinforcement rows are nested inside each object in the payload, rather than sent as a separate top-level array, since Workflow 2's comparison (D19) treats "an object plus its reinforcement" as one unit to evaluate together — a flat array would need to be re-matched back to its parent object with no added benefit |
| D36 | Input mechanism for both endpoints | ✅ **Decided — plain JSON request body**, no custom upload form or CSV parser. Consistent with the Week 3 review's explicit instruction against unnecessary UI work, and with the existing FastAPI/Pydantic stack already in place. `/docs` (Swagger UI) serves as the interface for manual testing, matching the Development Foundations pack's own guidance to use it "from the first day" |

---

# 5. Validation Rules (Draft)

| Rule ID | Field | Condition | Severity | Status |
|---|---|---|---|---|
| VR-01 | `Building.building_name` | Freely editable | *(no rule needed)* | ✅ Decided |
| VR-02 | `Floor.elevation` | Append-only once referenced | Warning | ✅ Decided |
| VR-03 | `Material.compressive_strength_kg_cm2` | Append-only once referenced | Warning | ✅ Decided |
| VR-04 | Reinforcement Spec (diameter, grade) | Append-only once referenced | Warning | ✅ Decided |
| VR-05 | `Zone.pour_sequence` | Freely editable | *(no rule needed)* | ✅ Decided |
| VR-06 | `ReinforcementBar.spacing`, `hook_type` | Required when `bar_role='transverse'`, optional otherwise | Error | 🔶 Proposed — one illustrative example of "contextual completeness," not individually confirmed |
| VR-07 | `Member.geometry_points` | Exactly 2 points for column/beam; ≥3 for wall/slab | Error | 🔶 Proposed — same as VR-06 |
| VR-08 | All referenced FKs (floor_id, zone_id, sect_id+member_type, material_id, spec_id) | Must exist in Project Configuration | Error | ✅ Decided — matches the person's own proposal directly |
| VR-09 | `Section.dim`, `Grid` position fields | Same append-only treatment as VR-02/03 | Not assigned | **Recommended, not decided** |

---

*End of document.*
