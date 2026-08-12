# Mapsift PRD

> **Status:** living document, PRD v0.16 (2026-08-05). **v0.16 in one line:** the wall gained its **single deliberate exception**, the login question: a user's own `membership` rows are readable across tenants, through a second permissive policy that is `FOR SELECT` only (ADR-0005 section 8, decided with MAP-27), and T6.1 and M1 now name the exception their blanket cross-tenant sentences had contradicted in latent form since v0.11, because M1 has always required a user with two tenants to hold memberships the login path must enumerate before any tenant is bound. **v0.15 in one line:** the layer's declared geometry kind stopped being a label and became a **contract on its features** (M2), with the family admitting multipart geometry and enclaves so a legal reserve is never refused (D3), and with the refusal itself specified where it actually happens, at the flush, as a **typed error that flags and retains** rather than discards (M9), because the geometry was drawn offline in the field and a validation that drops it is preserve-not-discard broken by another name. The rule existed first in a spec-per-task that had invented it, which made its test a test with no requirement; an adversarial review found that, and the round is the correction. **v0.14 in one line:** the second migration-forced ADR landed, so **M3's Open/ADR is closed by ADR-0006**, and it closed by measurement rather than by balancing the trade the requirement described: the index locality a time-ordered identifier buys is contingent on the device clock being right, and this model distrusts that clock by construction (I10), so the identifier is a random 128-bit value. **v0.13 in one line:** the first of the migration-forced ADRs landed, so **T6.1's Open/ADR is closed by ADR-0005** (row-level security enabled and forced, per-tenant views rejected, four unprivileged roles, a transaction-scoped and parameterised binding read through a guarded cast, and a three-point contract the tile server choice inherits), and **N2's acceptance grew the cases that ADR's probes wrote for it**, including the one no reading produced: referential-integrity checks bypass the policy, so a cross-tenant foreign key and a cross-tenant unique-key collision are channels only composite keys close. **v0.12 in one line:** the operational layer stopped being implicit, so N9 gained the mechanism half of observability (structured logs carrying their correlation keys, redaction on the path rather than in each caller, vendor-neutral emission, and client telemetry as a real-device source for the N1 budgets) and a new **N12** carries availability, degradation and recovery, both under the foundation decision of the same round. **v0.11 in one line:** the SP-1 spike closed, so M10 gained the fifth version axis it had declared missing (the per-project version as the resync cursor, ratified in ADR-0004) and N1 gained the rule that a budget is a floor rather than a target. **v0.10 in one line:** the norm citations behind the legal-area rule were corrected against the live standard after verification found the cited one revoked, the legal-weight rule stopped depending on a registry's state of the moment, the native analysis core gained the five capabilities a frequency-and-centrality review found missing, J2 became a test and closed the last placeholder in this document, and regulatory content became per-jurisdiction data (M16) under the foundation decision of the same round. **All four layers are drafted:** Layer 1 (native capability floor, families A to K), the anti-requirements, and the extension catalog; Layer 2 (transversal system behaviors, T1 to T9), with A2 and A3 reconciled to the foundation v0.11 tenant model; Layer 3 (data model and contracts, M1 to M16), which paid the four debts Layer 2 left it, settled the coordinate reference rule that previously had no home and its per-purpose metric frame (M5), and narrowed B2's offline-import acceptance to the element budget so it stops contradicting foundation section 5; and Layer 4 (surfaces and platform, S1 to S10), which fixes the parity rule, the per-surface offline domain, the field surface with its capture-precision floor, and the force-upgrade path. The **non-functional block** (PRD section 8, N1 to N12) is written, with the three performance budgets separated and given a measurement protocol, and the **design system** (PRD section 9, U1 to U12) carries the visual identity the owner ratified, in normative form. **The prose is complete;** what remains is decisions, artifacts, and measurements, enumerated in the document's own gap list (PRD section 10). Layer 1 is wired to the data and tool reference catalog (`specs/data-and-tooling-references.md`): the data sources, the fixture corpus, and the per-tool expected behavior live there and are referenced, not duplicated.
> **Authority:** this document derives from `specs/mapsift-foundation.md` (foundation v0.17) and must not contradict it. Where the foundation closed a decision, this PRD transcribes it as a testable requirement and cites it; where the foundation left a question open (an OQ), this PRD marks the gap rather than inventing an answer. The foundation's non-negotiable principles win over any feature parity goal: where a MC-03 or MC-04 design choice conflicts with the foundation (for example the Rust core instead of MC-03's client model, or server-authoritative instead of local-first), Mapsift follows the foundation, not the other tool.
> **How to read:** every requirement is either a testable statement with a pass/fail acceptance test, or an explicitly marked open question. There is no third category.
> **Market references:** references to other tools in the market are cited by code (MC-01, MC-02, and so on), defined in the internal market-research document `specs/market-reserarch.md`.

---

## 0. How this PRD is organized

### 0.1 Layers

The Mapsift PRD is split into four layers so a large system stays navigable, followed by the non-functional block (PRD section 8) and the design system (PRD section 9). All of it is drafted, and PRD section 10 is the document's own gap list.

- **Layer 1, native capability floor (PRD section 1, families A to K):** what the user does in the box, with nothing downloaded.
- **Layer 2, transversal system behaviors (PRD section 5, T1 to T9):** properties holding across every capability, sync, offline, conflict resolution, idempotency, identity and authorship, tenancy, and the capability-layer discipline that keeps the SDK and the AI agent possible (foundation invariants I1 to I11 as behavioral requirements).
- **Layer 3, data model and contracts (PRD section 6, M1 to M16):** elements versus layers, identity, geometry and the coordinate reference rule, the attribute schema, the operation format, the version axes, and what crosses the serializable boundary (I5, I8).
- **Layer 4, surfaces and platform (PRD section 7, S1 to S10):** web, desktop, and mobile (the field surface), what each delivers and what differs.

### 0.2 The determinism rule

This PRD pushes non-determinism out of implementation. Every functional item carries a pass/fail acceptance test, never a description that merely "looks right." Each acceptance test is the upstream of a `testing.md` entry: the PRD criterion is the test written before the code. A sentence that admits two readings is a defect, and becomes either a sharpened criterion or a marked open question.

### 0.3 The native floor and the parity rule

Layer 1 is the **native floor**: everything in it ships in the box and is native by definition. The floor is sized so a professional works all day without downloading anything, and it is set by a hard rule that protects against the failure mode of a professional testing Mapsift, not finding a tool they had in MC-03, and leaving:

- **Every MC-03 tool that is real professional work is native in Mapsift, mandatory, never an extension.** This includes tools MC-03 gates behind its Enterprise plan: MC-03's gating is commercial packaging, not a statement that the tool is optional, and a professional coming from a paid MC-03 will miss what they used. The gating proves MC-03 considers the tool valuable enough to charge for; it does not lower the tool below the floor.
- **Extension begins only beyond MC-03:** what is past MC-03 entirely, an improved version of a native tool, or a specialization MC-03 also lacks natively. The extension catalog (PRD section 3) is where those live.
- **The four MC-04 differentials a professional actually feels are pulled into the native floor:** in-browser spatial SQL (the depth valve, run the analysis that has no button without leaving the tool), the layer-compare swipe slider (before/after deforestation), the time slider bound to temporal data, and experience-level/configurable layout (the 0.5 depth-hidden principle made real).

Because native and extension consume the same capability layer, the boundary is a movable packaging label, not a wall (foundation 9.5): a wrong call in v1 is corrected by repackaging, not a rewrite.

### 0.4 The three-tier model: native, official extension, community extension

Per foundation OQ-14 and the foundation 9.5 capability layer, extensibility has three trust tiers, and the dimension that separates them is access to legal-weight geometry, because that is where damage by an untrusted consumer is irreversible (the same gate as the I11 agent: a non-human or third-party consumer acting with permission).

- **Native:** ships in the box, the owner guarantees it.
- **Official / developer extension:** built by the Mapsift team, curated like MC-01, outside the box but under the owner's warranty. It may touch legal-weight geometry because the owner answers for it. It carries three guarantees a community extension does not: direct reliability and responsibility, long-term maintenance, and being engineered to fit Mapsift's architecture so its performance is optimized and exhaustively tested before it reaches the store (the way 8 GB on a MacBook outruns a better-specced Windows laptop because the software is tuned to the hardware).
- **Community extension:** built by a third party, sandboxed (foundation 9.5 serializable boundary, OQ-14). By default it does not write legal-weight geometry without explicit user confirmation.

AI as a whole may be treated as official-extension-exclusive; this is the owner's leaning and is not settled here.

### 0.5 Capability template

Every capability is written in one shape:

- **ID and name.**
- **Description:** one line.
- **Origin:** where it comes from and why it is on the floor (MC-03 parity, MC-03 Enterprise parity, MC-04 differential, domain, or foundation).
- **Rule:** the inherited rule, from a foundation invariant/section where one exists, or from an anti-requirement/principle where the foundation has no direct invariant (MC-03's functional surface is broader than the foundation's, which is strong on system invariants and thin on UI surface).
- **Acceptance:** pass/fail criteria, each testable.
- **Open / ADR:** the linked OQ or the deferred architecture decision, when applicable.

Everything in Layer 1 is native, so the template omits a native/extension tag; the extension catalog (PRD section 3) carries tier and legal-weight access instead.

### 0.6 Legal weight is a transversal marker

Per foundation OQ-8, the rule classifying which features carry legal weight is open and is settled with the environmental engineer. Legal weight is not a capability; it marks several (all feature editing, schema completeness, and result promotion), because it is where preserve-not-discard arms. Wherever a capability can touch legal-weight geometry, the acceptance inherits preserve-not-discard and the gap is marked OQ-8.

### 0.7 What is not a Layer 1 capability

- **Every Layer 1 capability is a named capability of foundation 9.5**, carrying a machine-readable structured description and composable output, reached only through the capability layer. The app, official extensions, community extensions, the SDK, and the AI agent are all consumers of that one layer.
- **The AI agent (I11, 9.5.1)** is a consumer, online-only, with mediation provenance and a legal-weight/bulk gate, specified in Layer 2.
- **The Field App, detailed permission matrix, and platform differences** are Layer 4 and Layer 2; capabilities below that touch them (field photos, GPS snapping, sharing roles) note the dependency.

---

## 1. Layer 1: Native capability floor

### Family A: Access, project, sharing

#### A1. Authenticate and hold a session
- **Description:** the user signs in and keeps working, including across an offline field trip.
- **Origin:** foundation (I10) plus MC-03 parity (Field App authenticated use).
- **Rule:** identity authority is the server (I10); offline runs on a long-lived refresh credential plus a renewable short-lived access token, renewed on reconnect, with interactive re-auth if the refresh credential expired or was revoked, and the offline queue persists until re-auth (foundation section 9, I10); transport is always TLS.
- **Acceptance:** a signed-in user goes offline, edits, and edits are attributed and queued without a live token; on reconnect the session renews silently and flushes; if the refresh credential expired, re-auth is prompted and queued work is still present after, not lost.

#### A2. Create and open a project
- **Description:** the user creates or opens a project within a workspace, under their tenant (a personal account, or an organization when a company exists).
- **Origin:** foundation (I4, foundation section 9).
- **Rule:** the **tenant** is the top container of the account (a personal user account, or an organization), and it is the unit of tenant isolation (I4), enforced at the SQL layer by a tenant identifier on every row; a **workspace** groups projects and a **project** holds the elements and layers, both organization and permission within the tenant, not separate isolation walls. Confidentiality between a tenant's own projects or clients is permission, not isolation (foundation section 9).
- **Acceptance:** no data, presence, or operation crosses a **tenant** boundary by any path, including the tile path; a cross-tenant access is indistinguishable from a resource that does not exist; opening a project loads only its layers and elements; within a tenant, a project the user holds no grant for is reachable only with that grant, and a revoked project is genuinely unreachable, not merely hidden from a listing.
- **ADR:** the detailed permission model (the organization role, per-resource view/comment/edit, workspace-inherited sharing) is deferred to Layer 2 T6; A2 fixes that the tenant is the top of the account and that isolation is the tenant's while permission lives below it.

#### A3. Share a project or workspace and set access
- **Description:** the user shares a project, or a whole workspace whose projects inherit the share, with others at a chosen access level, and invites collaborators.
- **Origin:** MC-03 parity (FAM-14.1/14.2) plus foundation (foundation section 9 permission model).
- **Rule:** sharing grants a per-resource permission (view, comment, edit) bounded by the recipient's license and capped by a default; sharing a workspace flows its grant and level to the projects within, and a per-project exception can only lower it, never raise it; denying access is revocation of the grant, not concealment, so a removed project is genuinely unreachable, not merely hidden (foundation section 9); sharing never crosses the tenant isolation rule (I4).
- **Acceptance:** sharing at view lets the recipient see but not edit, at edit lets them edit; sharing a workspace shares its projects at the inherited level, and an explicit per-project exception removes access by revoking the grant (the project becomes unreachable by any path, not hidden from a listing); a default caps the effective permission and cannot raise it above the license; a collaborator outside the tenant sees only what they were invited to.
- **ADR:** the full role matrix, the governance ladder, and the workspace-inheritance mechanism are Layer 2 T6; A3 fixes the act of sharing, the three access levels, and workspace-to-project inheritance with lower-only exceptions.

### Family B: Map, data sources, and import

#### B1. View and navigate the map
- **Description:** the user sees and moves around the map, with a default basemap present on first open and the ability to switch basemap.
- **Origin:** MC-03 parity (FAM-03.5) plus foundation (I6, MapLibre rendering).
- **Rule:** rendering is GPU vector via MapLibre, large data stays performant (I6); a default data source provider is active with no configuration, the best free open imagery served by Mapsift's own tiling stack (Sentinel-2 via STAC, served by TiTiler from object storage); the user can switch to other basemaps including satellite, light/dark, and labels on/off. The Sentinel-2 default source and the processing-and-egress cost this default-provider decision carries are catalogued in `specs/data-and-tooling-references.md` sections 1.4 and 1.5, and referenced here rather than restated.
- **Acceptance:** a new user with nothing configured sees recent low-cloud imagery for their region without choosing a provider; pan and zoom stay responsive on a large layer (the I6 bar); switching basemap changes the background without affecting data layers; the default source is reached through the provider interface (foundation section 6, closed v0.12) and holds no privileged path.
- **Open:** **OQ-3** gates this capability and was previously unmarked anywhere in this document. The foundation forbids offering any imagery-dependent feature as unlimited until the per-use cost is modelled, and "a default provider active with no configuration for every new user" is exactly such a feature. The intended mitigation is that imagery is pre-ingested into Mapsift's own tiling stack rather than proxied per request, which moves the cost from metered processing units to storage and egress, and **that is a cost model to write, not a cost model that exists**. Until OQ-3 closes, the acceptance above is what the surface does, not a commitment about volume.

#### B2. Import a file
- **Description:** the user brings a data file into the project.
- **Origin:** MC-03 parity (FAM-01) plus MC-04 formats plus domain (SIRGAS2000/UTM).
- **Rule:** an import is an offline-path write that appears immediately (I1) with client-generated collision-safe IDs (I3); the accepted set covers what MC-03 and MC-04 accept, built on GDAL/OGR on the server and WASM readers on the client, not hand-written parsers; SIRGAS2000 and UTM are reprojected natively with the source CRS recorded, because Brazilian environmental and cadastral data arrives in them and a silent or wrong reprojection moves a legal boundary. The fixture corpus and the format-and-CRS test matrix this capability is tested against live in `specs/data-and-tooling-references.md` Part 1 (sections 1.1, 1.3, and 1.4).
- **Acceptance:** importing a zipped Shapefile, GeoJSON, GeoPackage, KML/KMZ, GeoTIFF/COG, GeoParquet, FlatGeobuf, CSV/Excel with coordinates, and GPX each loads correctly; a Shapefile in SIRGAS2000 UTM places geometry at the correct location with the source CRS recorded and no positional precision loss; a deliberately broken fixture (a Shapefile missing a part, or a file with no .prj) raises a clear validation error rather than silently mislocating or assuming a CRS; at least one foreign national grid (ETRS89/LAEA EPSG:3035 or US State Plane, sourced per `specs/data-and-tooling-references.md` section 1.4) reprojects to the correct location in addition to SIRGAS2000 UTM, so general-purpose reprojection is proven by a test and not only asserted; drag-and-drop and a multi-dataset archive that becomes a layer group both work; **an import proceeds offline when the client can read the format and the result stays inside the element budget** (foundation section 5, qualified in v0.12; M2), appearing immediately and syncing on reconnect; an import that fails either condition (a raster, a large dataset, a format needing server-side processing) **is refused before the file is accepted, with the reason stated**, and is never queued as if it would sync; the set of client-readable formats is declared rather than discovered by trial.
- **ADR:** the long tail of additional GDAL-supported formats and the DXF/CAD path are added breadth on the same GDAL layer.

#### B3. Add a data source
- **Description:** the user connects a streaming or web data source rather than uploading a file.
- **Origin:** MC-03 parity including Enterprise (FAM-02, cloud DB and raster streaming) plus foundation (the closed pluggable-provider decision).
- **Rule:** a data source is a pluggable provider behind one interface, never a single hard-coded vendor; STAC covers global raster catalogs and adapters cover national vector services; COG and STAC stream in place without duplication; this is a capability-layer consumer like any other (9.5). Kept separate from B2 so uploaded data and transmitted data do not blur.
- **Acceptance:** changing the STAC endpoint from one provider to another changes nothing above the data-source interface; WMS/WFS/WMTS/XYZ/STAC and a PostGIS connection can each be added and rendered, with the real OGC-service add-a-source fixtures being TerraBrasilis (WFS and WMS) and the Copernicus CLMS/CORINE services catalogued in `specs/data-and-tooling-references.md` sections 1.2 and 1.4; a source-derived layer that is edited surfaces the live-versus-edit conflict explicitly rather than silently overwriting on refresh (anti-requirement); the default Sentinel-2 source is one such provider, not a privileged path.

#### B4. Manage layers
- **Description:** the user toggles visibility, reorders, groups, and reads the provenance of layers.
- **Origin:** MC-03 parity (FAM-03) plus domain (legal provenance).
- **Rule:** layers and elements are distinct (foundation section 3); layer operations are the heavy, shared, server-authoritative side; every layer carries source, attribution, and license metadata, which matters for legal data provenance.
- **Acceptance:** toggling, reordering, and grouping behave consistently and are part of project state that restores on reopen; a layer's source, attribution, and license are visible to viewers.

### Family C: Data structure and schema

> Legal weight (OQ-8) marks this family: required-field completeness is how a legal-weight feature is prevented from being born incomplete.

#### C1. Create a layer and its attribute schema
- **Description:** the user creates a new layer, choosing geometry type and defining the attribute fields, before drawing into it.
- **Origin:** MC-03 parity (FAM-04.1).
- **Rule:** what is created is the structure a feature is drawn into; the structure is a layer (foundation section 3), the features in it are elements.
- **Acceptance:** the user names a layer, picks point/line/polygon, defines attribute fields, and can then draw features that carry those fields.

#### C2. Attribute types
- **Description:** the user assigns typed attributes to features, including photos.
- **Origin:** MC-03 parity (FAM-04.2) plus domain (field photo).
- **Rule:** supported types are text, number, boolean, date/time, image (multiple per feature), and person; the image attribute is core field work, the photo attached to a feature.
- **Acceptance:** each type can be set and read; multiple photos attach to one feature and display in inspection; a person attribute references a workspace member.

#### C3. Required fields and survey dropdowns
- **Description:** the user marks fields required and defines preset dropdown values for a survey.
- **Origin:** MC-03 parity (FAM-04.3/04.4) plus domain (legal completeness).
- **Rule:** a required field blocks feature creation until filled, which enforces completeness of legal-weight data; this links the OQ-8 classification (which features are legal-weight) to the rule that they cannot be saved incomplete.
- **Acceptance:** a required field blocks creation until filled; a single-select dropdown offers only its preset values.
- **Open:** which fields are required for a legal-weight feature depends on OQ-8.

#### C4. Edit the schema
- **Description:** the user adds, renames, and removes attribute columns.
- **Origin:** MC-03 parity (FAM-04.7) plus improvement (MC-03 cannot delete columns).
- **Rule:** a schema change propagates to the table, inspection, styling, and any component bound to the attribute.
- **Acceptance:** adding, renaming, and removing a column updates the table and inspection consistently; removing a column is supported (unlike MC-03).

### Family D: Feature editing

> Legal weight (OQ-8) marks every capability in this family: where the feature is legal-weight, acceptance inherits preserve-not-discard.

#### D1. Draw a feature
- **Description:** the user creates a feature by drawing point, line, or polygon on the map.
- **Origin:** foundation (I1, I3, I9, I10) plus MC-03 parity (FAM-04.6).
- **Rule:** the draw is an offline-path write that appears immediately (I1), gets a client-generated collision-safe ID (I3), enters the queue with a per-client mutation number (I9) and an author stamped at creation (I10); what is born is an element (foundation section 3).
- **Acceptance:** offline, a polygon appears immediately with no server call; the feature gets a unique client ID with no cross-client collision; on reconnect the creation syncs without duplicating on resend (I9), attributed to the creating session's author (I10).
- **Open:** legal-weight classification is OQ-8.

#### D2. Edit geometry
- **Description:** the user moves a vertex, reshapes, and snaps to neighboring geometry.
- **Origin:** foundation (I1, I9, I10) plus MC-03 parity.
- **Rule:** an offline-path edit under I1, I9, I10; offline snapping produces a pointwise coordinate coincidence against loaded geometry, with no propagation and no guarantee it survives a later edit (live propagation is online, see D6).
- **Acceptance:** offline, a vertex move appears immediately; snapping to a loaded neighbor creates coincidence at that instant; the edit syncs idempotently (I9), attributed to its author (I10).

#### D3. Create and edit complex geometry
- **Description:** the user creates and edits multipart polygons and polygons with holes, from scratch.
- **Origin:** improvement over MC-03 (anti-requirement AR4) plus domain (multi-part reserve, enclave).
- **Rule:** complex geometry is creatable from scratch, not only editable; a legal reserve is frequently multi-part or has an enclave, so this is a domain requirement, not a nicety.
- **Acceptance:** the user creates a multipolygon and a polygon with a hole from scratch, not only by editing an imported one.

#### D4. Edit an attribute
- **Description:** the user edits a feature's attribute value.
- **Origin:** foundation (I9, I10) plus MC-03 parity.
- **Rule:** an attribute edit enters the queue under I9 and I10; conflict on a non-trivial non-geometric property resolves per the foundation section 4 granularity model.
- **Acceptance:** an offline attribute edit appears immediately and syncs idempotently; a concurrent edit to the same property resolves per the granularity rule, not silently overwritten.

#### D5. Delete a feature
- **Description:** the user deletes a feature.
- **Origin:** foundation (preserve-not-discard) plus MC-03 parity.
- **Rule:** delete of a legal-weight feature follows preserve-not-discard, never silent removal; delete-versus-edit retention semantics are open (OQ-13).
- **Acceptance:** deleting a legal-weight feature does not silently discard it; a delete conflicting with a concurrent edit is flagged for human resolution.
- **Open:** delete-versus-edit retention is OQ-13; legal-weight classification is OQ-8.

#### D6. Edit shared topology
- **Description:** the user edits a boundary shared by two features so both sides stay coincident.
- **Origin:** foundation (OQ-1).
- **Rule:** shared-edge editing with structural propagation is an online server-side operation via PostGIS Topology, multi-feature and atomic, with the conflict unit at the arc and preserve-not-discard at the arc level for legal weight; offline there is only snapping (pointwise coincidence, no propagation, no persistence under later editing); consolidation happens at reconnect, server-side. There is no offline topological editing.
- **Acceptance:** offline, the user snaps to a shared boundary but moving it does not propagate; online, moving a shared boundary propagates atomically to all faces referencing the arc; a legal-weight arc edit follows preserve-not-discard; topological propagation offline is unavailable, not silently degraded into overlap or gap.
- **Open:** the full shape of OQ-1.

#### D7. Undo and session history
- **Description:** the user undoes recent actions within the session.
- **Origin:** MC-03 parity (FAM-04.8) plus foundation (I10 authorship chain) plus anti-requirement AR5.
- **Rule:** in-session undo is a UX affordance; the permanent record of who changed legal-weight geometry is the preserved ordered authorship chain (I10), not a transient undo stack, so Mapsift does not inherit MC-03's no-permanent-history limitation.
- **Acceptance:** an in-session undo reverts the last action; the permanent authorship chain of a legal-weight feature remains inspectable independent of any user's undo stack.

#### D8. Automatic metadata fields
- **Description:** the user sees area, perimeter, and created/modified-by as fields that update automatically.
- **Origin:** MC-03 parity (FAM-04.5) plus foundation (authoritative metric, anti-requirement AR3).
- **Rule:** area and perimeter exist as auto-updating fields used for reserve and APP calculation; they are authoritative and immediate, computed in the correct metric projection, never nightly-estimated (AR3); created/modified-by derive from the authorship record (I10).
- **Acceptance:** a polygon's area and perimeter fields update immediately on edit and are computed **in the declared metric frame selected by the metric's purpose (M5), never in degrees on a geographic frame**, with the value carrying its purpose, its frame, and its authority; the legal metric reported is the authoritative value, never an estimate or a deferred recompute.

### Family E: Inspect and query

#### E1. Attribute table
- **Description:** the user opens a table of features as rows and works with it.
- **Origin:** MC-03 parity (FAM-05). Daily professional use.
- **Rule:** the table is a first-class view of the layer's features; column statistics serve area and cover validation and are authoritative, not estimated (AR3 where the figure carries legal weight).
- **Acceptance:** features appear as rows; search across columns, sort ascending/descending on every type, inline-edit a cell, add a feature, and read per-column statistics (min, max, mean, median, sum, total, unique, null) all work; selecting a row highlights the feature on the map and back.

#### E2. Feature inspection and popups
- **Description:** the user clicks a feature to see its attributes, and clicks a raster to see its pixel value.
- **Origin:** MC-03 parity (FAM-08) plus domain (raster pixel value).
- **Rule:** inspection is the most basic GIS gesture; popups are configurable (which attributes, title, header image, layout); raster pixel-value inspection shows the value at the clicked point, which for an NDVI raster is the vegetation index there.
- **Acceptance:** clicking a vector feature shows its configured attributes; clicking a raster shows the pixel value; overlapping features can be stepped through.

#### E3. Filter
- **Description:** the user filters features by attribute and by spatial relationship.
- **Origin:** MC-03 parity (FAM-06) plus improvement (spatial predicate native, which MC-03 has only as an Enterprise/viewer extension) plus domain.
- **Rule:** the attribute operator set is the small precise set (less-than, greater-than, equals, not-equals, contains, in-list, is-null, and the and/or compound nesting); on top of that, spatial predicates are a first-class editor filter, because the environmental question is spatial (inside the APP, overlaps the reserve), which is a deliberate improvement over MC-03.
- **Acceptance:** an attribute filter with compound and/or logic applies to map and table; a spatial-predicate filter (inside, overlaps, within distance of another layer) is available in the editor, not only as a viewer add-on; a filtered subset can be saved as a derived layer and fed into analysis or export.

#### E4. Spatial SQL query
- **Description:** the advanced user runs a spatial SQL query against the loaded data to answer a question that has no button.
- **Origin:** MC-04 differential (Z.1 in-browser spatial SQL) plus MC-03 Enterprise (AI SQL). The depth valve.
- **Rule:** spatial SQL is the mechanism for unbounded depth without predicting every analysis, so it is native even though it serves the advanced user; the authoritative query runs server-side against PostGIS, with a client-side path for loaded data; results are composable (feed the map, another capability, or export).
- **Acceptance:** the user writes a spatial SQL query against project layers and gets a result they can add to the map or export; the authoritative result runs in PostGIS; a query like "APPs that intersect last year's deforestation alerts and sit inside parcels without CAR" is expressible without a dedicated button.
- **ADR:** the client-side SQL engine choice (for loaded-data queries) is an implementation decision behind the capability.

### Family F: Styling and symbology

#### F1. Vector styling
- **Description:** the user styles vector layers by value.
- **Origin:** MC-03 parity (FAM-07).
- **Rule:** styling supports simple, categories, color range, size range, heatmap, and icons, with the standard classification methods (equal intervals, quantiles, standard deviation, Jenks) and labelling; an invalid style is validated and surfaced, never silently ignored (anti-requirement AR1).
- **Acceptance:** a layer can be styled by category and by a classed numeric range with a chosen classification method; labels by attribute render with the standard controls; an invalid style override raises a visible error rather than being silently dropped.

#### F2. Raster styling
- **Description:** the user styles raster layers, including vegetation indices.
- **Origin:** MC-03 parity (FAM-07.11) plus domain (vegetation).
- **Rule:** raster styling supports band combinations, hillshade, custom color ramps, and raster algebra including NDVI, which is how the vegetation professional sees cover; resampling and noData are handled explicitly.
- **Acceptance:** a multi-band raster can be styled by band combination; an NDVI visualization renders from chosen bands; a custom color ramp and hillshade apply.

#### F3. Zoom-based styling
- **Description:** the user limits visibility and interpolates style across zoom levels.
- **Origin:** MC-03 parity (FAM-07.6).
- **Rule:** visibility can be limited by zoom range and properties interpolated across zoom; the legend syncs to the current zoom.
- **Acceptance:** a layer's visibility is limited to a zoom range; line width or opacity interpolates across zoom; the legend reflects the current zoom.

#### F4. Expression and declarative styling
- **Description:** the user styles by expression through a declarative style contract.
- **Origin:** MC-03 parity (its declarative style language, DEV-C) plus foundation (capability layer).
- **Rule:** style is expressible as a declarative document that is the single source of truth and round-trips with the UI editor; this declarative style contract is how styling is exposed on the capability layer, so an extension or the agent can style by the same contract the UI uses.
- **Acceptance:** a style set in the UI is readable and editable as a declarative document and vice versa; an expression-driven style (data-driven color, NDVI raster algebra) is expressible in the contract.

### Family G: Measurement and analysis

> Expected per-tool behavior and the level-two acceptance checklist (a distance or area is computed in a projected CRS and never in degrees on EPSG:4326; non-touching inputs return empty, not an error; a closed-formula tool like NDVI matches a hand-computed value) live in `specs/data-and-tooling-references.md` Part 2; the acceptance criteria in this family reference that per-tool entry rather than restate it.

#### G1. Measure area, perimeter, and distance
- **Description:** the user measures a polygon's area or perimeter and a line's distance.
- **Origin:** MC-03 parity (FAM-10.6) plus foundation (authoritative metric, AR3).
- **Rule:** computed metrics are authoritative and immediate, rejecting nightly recompute and estimate behaviors; the light preview runs in the client core for offline immediacy, the authoritative value runs in PostGIS with the correct metric projection.
- **Acceptance:** measuring shows an immediate client preview offline; the authoritative server value is computed **in the metric frame the metric's purpose selects (M5)**, never in degrees on a geographic frame, so a large-area measurement is not distorted; the authoritative value, not the preview, is what a legal-weight metric reports.

#### G2. Run an analysis
- **Description:** the user runs a spatial analysis over one or more layers.
- **Origin:** MC-03 parity (FAM-09) plus domain (environmental core) plus OQ-5.
- **Rule:** the native analysis kit is the recurring core, with depth held one step away as extensions (9.5 native-kit rule); light analysis previews in the client core, the authoritative result runs in PostGIS with the correct projection. The native vector core is buffer, clip, intersect, difference, union, dissolve, centroid, spatial and attribute join, and count points; the native raster core is NDVI/band algebra, zonal stats, reclassify, change detection between two classifications with its class-by-class cross-tabulation, and the terrain kernel (slope, with aspect and hillshade from the same elevation model); reprojection is exposed as an invokable tool rather than living only inside the import path (M5). Buffer is central because the preservation-area buffer is how a preservation area is defined in law; intersect and difference are central because overlap of clearing with a reserve is the daily work. **Five of those were promoted into the core in v0.10, each on frequency and centrality and none on parity** (foundation 9.5): change detection and cross-tabulation are the operation that defines the anchor domain, vegetation cover between two instants, which the core had somehow omitted, and they now have a second and non-obvious buyer in the compliance chain, where a lender or an exporter must confront a holding against a deforestation baseline; slope feeds a legal category directly, since restricted-use and preservation-area classes are defined by inclination bands, so every property diagnosis passes through it, and aspect and hillshade ride the same kernel at near-zero cost; union completes an overlay family the core already carried in half, since dissolve is grouped union underneath; and exposing reprojection costs almost nothing because the authoritative transformation is already an obligation of the import path. Analysis can take a filtered layer (E3) as input.
- **Acceptance:** each native tool runs end-to-end and returns a composable result and meets the level-two criterion in its catalog Part 2 entry (correct projected CRS, non-touching inputs return empty not error, a closed-formula tool like NDVI matches a hand-computed value); a buffer/intersect/difference chain produces a correct authoritative result in the metric frame its purpose selects (M5); an APP-versus-legal-reserve overlap analysis runs end-to-end and exports without precision loss.
- **Open:** which environmental-specific analyses beyond the core matter, including any Brazilian-workflow analysis neither MC-03 nor MC-04 carries, is OQ-5, settled with the engineer.

#### G3. Promote a result to an element
- **Description:** the user turns an analysis result into a persistent element.
- **Origin:** foundation plus OQ-6.
- **Rule:** a promoted result becomes an element that persists and syncs like any element; if legal-weight it follows preserve-not-discard.
- **Acceptance:** an analysis result can be promoted to a persisting, syncing element; a promoted legal-weight element follows preserve-not-discard.
- **Open:** promoted-element lifecycle is OQ-6.

### Family H: Collaboration

#### H1. See presence and live edits
- **Description:** the user sees who else is in the project and their edits in real time.
- **Origin:** MC-03 parity (FAM-12.11) plus foundation (foundation section 4, C9).
- **Rule:** sync is server-ordered with gap detection and resync (C9); presence and live fan-out are online; the transport is not trusted for correctness (versioning and gap detection carry correctness, not delivery).
- **Acceptance:** an online edit appears to other online users; a missed message is recovered by gap detection and resync; presence is scoped to the tenant (I4).

#### H2. Comments
- **Description:** the user leaves comments pinned to a map location or a feature, in threads, with mentions.
- **Origin:** MC-03 parity (FAM-12). Daily professional collaboration.
- **Rule:** a comment is anchored to a location or a feature, supports threads and replies and mentions, and can be resolved; this is distinct from live presence, it is the asynchronous "this boundary here is wrong" pinned to the map.
- **Acceptance:** a comment pins to a location or a tagged feature and is visible to collaborators; threads, replies, mentions, and resolve/reopen work; clicking a comment restores its map view; comments are exportable georeferenced.

#### H3. Resolve a conflict
- **Description:** the user resolves a flagged conflict between two versions.
- **Origin:** foundation (preserve-not-discard).
- **Rule:** conflict resolves by granularity (foundation section 4); a legal-weight geometry collision is flagged with both versions preserved for a human, never silently discarded.
- **Acceptance:** a legal-weight geometry collision presents both versions and applies neither silently; a trivial collision resolves by the granularity rule without bothering the user; an authorization-failed or authorship-divergent operation surfaces here per I10/I11, not silently dropped.

### Family I: Insight components

#### I1. Layer-compare slider
- **Description:** the user swipes between two layers to compare them.
- **Origin:** MC-04 differential plus MC-03 (FAM-11.8) plus domain (deforestation before/after).
- **Rule:** a swipe slider compares two layers in place, which for the domain is one year of imagery against another; cheap to build, high environmental value, and not buried in a component as MC-03 does.
- **Acceptance:** the user picks two layers and swipes a divider to reveal one over the other across the map.

#### I2. Time slider
- **Description:** the user scrubs a timeline bound to temporal data.
- **Origin:** MC-04 differential plus MC-03 (FAM-11.5) plus domain (deforestation over time).
- **Rule:** a time slider binds to a date attribute or temporal layers and animates change over time, which for the domain is deforestation progression.
- **Acceptance:** a layer with a date attribute can be scrubbed across a timeline; the map updates to the selected time.

#### I3. Statistic and chart components
- **Description:** the user adds a statistic, bar chart, or histogram bound to layer data.
- **Origin:** MC-03 parity (FAM-11, selective).
- **Rule:** the selective dashboard components are statistic (count or numeric aggregate), bar chart by category, and histogram; they update on view or on filter; figures are authoritative, not estimated (AR3 where legal-weight).
- **Acceptance:** a statistic, a bar chart, and a histogram each bind to a layer and update when the view or a filter changes.

### Family J: Output and sharing

#### J1. Export data
- **Description:** the user exports project data to an interchange format.
- **Origin:** MC-03 parity (FAM-14.6).
- **Rule:** export interoperates with MC-02 (the desktop GIS the environmental team lives in), built on the same GDAL/OGR layer as import; a legal-weight metric in an export is the authoritative server value (G1, D8) rather than a preview. On top of the generic formats, export supports **receiving-body presets**: a named bundle fixing the format, the CRS, the encoding, the field-name convention, the one-theme-per-layer split, and the file naming that a given body requires. A preset is an entry in the jurisdiction package (M16) and never a branch in export code, because the bodies differ per regime and their requirements change on their own schedule.
- **Acceptance:** export to Shapefile, GeoJSON, GeoPackage, and GeoTIFF produces files that open correctly in MC-02; an exported area or perimeter is the authoritative metric value; a filtered subset exports as the subset; a named receiving-body preset produces a package that satisfies that body's published requirement without hand editing, and adding a preset is a package entry that touches no export code; a preset that a body has changed is a new dated version of that entry, and re-exporting an old project under the old version still reproduces what was delivered.

#### J2. Work output and report
- **Description:** the user produces a report or work product from the project.
- **Origin:** domain plus MC-03-adjacent; serves the deliverable, not marketing or story-map presentation (foundation section 12 excludes those by purpose).
- **Rule:** the work output is the professional's deliverable, and it is two artifacts rather than one: a document that a technical author signs, and a data package in the format the receiving body requires. Both are **generated from the project rather than assembled by hand**, because the failure this capability exists to remove is the stale number that survives a late geometry edit in a document someone retyped. Every figure in the document is the authoritative value of M5, carrying its purpose, frame, and authority; the content and the attestation block are template entries of the jurisdiction package (M16) and are never fixed schema fields, since what a deliverable must contain and how it is attested differ by regime.
- **Acceptance:** from a project holding a property and its themes, the product generates (a) a map layout carrying numeric and graphic scale, a coordinate grid, north, legend, and a title block with the technical author, their professional registration and attestation reference, the datum, the zone, the date, the scale, the sheet, and each source with its date; (b) a table of areas in which every figure is the authoritative M5 value with its purpose, frame, and authority, none of it retyped or recomputed by hand; (c) a descriptive memorial as a table of vertices with coordinates, azimuths, distances, and abutters, computed by the rule the applicable norm sets; (d) an export package per receiving-body preset (J1). **The test that closes it:** edit one vertex, regenerate, and every figure in every artifact matches the new authoritative value, with no stale number surviving anywhere in the document, the table, the memorial, or the package.
- **Provenance:** the acceptance was a placeholder from the first Layer 1 draft through v0.9 and is settled in v0.10 from a domain round grounded in published receiving-body requirements (`specs/domain-questions.md` Q3). This closes the last non-falsifiable acceptance criterion in this document (section 10.2).
- **Open:** which analyses feed the deliverable beyond the decided core is OQ-5; the per-regime template content is the jurisdiction package's (M16), with the Brazilian entries still to be filled from a real delivered exemplar, which sharpens the wording and the ordering rather than the test above.

#### J3. Duplicate and template
- **Description:** the user duplicates a project or map, and reuses templates for repeatable workflows.
- **Origin:** MC-03 parity (FAM-14.8).
- **Rule:** a duplicate copies everything except comments; a template captures a repeatable workflow setup.
- **Acceptance:** duplicating a map reproduces its layers, styling, and configuration without comments; a template can be instantiated into a new project.

### Family K: Workspace and layout

> This family makes the foundation 0.5 principle real: depth exists but the surface does not overwhelm. It is how the professional gets the full cockpit without the beginner drowning, the way Unity, Blender, and Premiere ship a simple default layout but let a professional reshape and save their own.

#### K1. Configurable layout
- **Description:** the user shows, hides, moves, and resizes panels and tools, switches between layout modes, and saves their own.
- **Origin:** the owner requirement (Unity/Blender/Premiere/Photoshop layout systems) plus MC-04 (Z.9 UI profiles) plus foundation (0.5 depth hidden until needed).
- **Rule:** the default layout is deliberately simple, the common path obvious and the depth one step away; a professional can reveal more tools, move and resize panels, switch to a denser professional layout mode, and save custom layouts as named presets; Mapsift aims for configurable, not as dense as Photoshop by default.
- **Acceptance:** the default layout is simple with the common path visible; a user can show or hide a tool or panel, move and resize it, switch to a professional layout mode, and save and restore a named custom layout.
- **ADR:** the set of preset layout modes and which panels exist is a design decision refined with the engineer and real use.

#### K2. Experience level and onboarding
- **Description:** a new user gets a simple guided start; an experienced user goes straight to the standard or professional layout.
- **Origin:** MC-04 (Z.9) plus the owner requirement (Unity-style onboarding) plus foundation (0.5).
- **Rule:** onboarding opens in a simple layout with step-by-step guidance alongside; skipping it drops the user into the standard layout; a professional can switch to a denser layout from a single control; the experience level tailors which tools and panels are visible, honoring depth-hidden-until-needed.
- **Acceptance:** a first-time user sees a simple guided layout; skipping guidance lands in the standard layout; a single control switches to the professional layout; the chosen level persists across sessions.

---

## 2. Anti-requirements

These are behaviors Mapsift deliberately rejects. MC-03 is the market reference and does each of these; the foundation's legal-weight-geometry principle forbids them. They are listed so an implementer does not reintroduce one while copying the leader.

- **AR1. No silent style or override discard.** An invalid or mismatched style property is validated and surfaced as an error, never silently ignored (MC-03 silently ignores invalid MapLibre overrides). Foundation basis: never silently discard.
- **AR2. No estimate where exact is expected.** A figure that carries weight is exact, not an estimate (MC-03's filtered H3 is an estimate). Foundation basis: legal-weight correctness.
- **AR3. No deferred or nightly recompute of metrics.** Area, perimeter, statistics, and symbology are authoritative and immediate, never recalculated nightly (MC-03 recomputes nightly). Foundation basis: authoritative legal metrics.
- **AR4. Complex geometry is creatable from scratch.** Multipolygons and polygons with holes are created, not only edited (MC-03 cannot create them from scratch). Domain basis: multi-part reserves and enclaves.
- **AR5. Permanent history for legal-weight, not session-only undo.** The record of who changed legal-weight geometry is the preserved authorship chain (I10), not a transient session undo stack (MC-03 has no permanent history). Foundation basis: I10 authorship chain, preserve-not-discard.

---

## 3. Extension catalog (post-native roadmap)

This catalog is the planning map for what comes after the native floor, in two stores on the Notion model (recommended/official and community), with a third distinction the legal weight forces. Each extension carries a tier and a legal-weight access level. This is a roadmap, not a Layer 1 requirement; it is here so the post-native plan is mapped now.

### 3.1 Official / developer extensions (curated, may touch legal weight under warranty)

- **AI imagery segmentation:** SamGeo-style extraction of vegetation, clearings, or features from imagery to vectors by prompt or automatically (MC-04 Z.5). High domain value for deforestation and vegetation. Likely AI-exclusive-official.
- **3D and point-cloud visualization:** LiDAR, 3D tiles, point clouds, Gaussian splats (MC-04). Important per the owner, especially for visual simulation of climate change and terrain change, even though the daily Brazilian environmental workflow touches them less often.
- **Heavy geoprocessing toolbox:** a Whitebox-style large tool library run on a server sidecar (MC-04 Z.2). The depth library, plugged not bundled.
- **Depth analysis tools:** Voronoi, Delaunay, convex hull, kriging, IDW, network analysis. Beyond the daily core, used occasionally.
- **Dedicated MC-02 bidirectional plugin:** beyond the native GeoPackage round-trip (J1), a live two-way MC-02 bridge (MC-03 FAM-14.9).
- **AI agent and natural-language assistant:** the I11 consumer surface as an official extension; possibly part of the AI-exclusive-official leaning.

### 3.2 Community extensions (sandboxed, no legal-weight write by default)

- Third-party tools, additional format readers, specialized visualizations, and regional data packs built on the capability layer.
- By default a community extension is sandboxed (9.5 serializable boundary) and does not write legal-weight geometry without explicit per-action user confirmation (the I11 gate applied to an untrusted consumer).

### 3.3 The official-versus-community distinction

The trust frontier between native and extension is the legal-weight gate. The distinction between the two extension tiers rests on three guarantees an official extension carries and a community one does not:

- **Reliability and direct responsibility:** the owner answers for an official extension.
- **Long-term maintenance:** an official extension is maintained across versions.
- **Engineered to fit Mapsift, so optimized and exhaustively tested before the store:** an official extension is tuned to Mapsift's architecture the way software tuned to its hardware outperforms better-specced but untuned hardware, and is performance-tested before release.

A community extension is sandboxed and legal-weight-gated precisely because it carries none of these guarantees by construction.

---

## 4. Open questions touched by Layer 1

Foundation OQs that Layer 1 marks rather than closes, gathered so the functional layer's dependencies are visible in one place.

- **OQ-5 (import formats and analysis tools):** formats and the analysis core are decided; what remains is the engineer confirming which environmental-specific analyses matter (G2, J2). The Brazilian deforestation and registry sources the engineer weighs these against (PRODES and DETER, CAR, SIGEF) are catalogued in `specs/data-and-tooling-references.md` section 1.2; the OQ stays open and owned by the engineer.
- **OQ-3 (Copernicus cost model):** B1, the default imagery provider active for every new user with no configuration. The foundation forbids offering an imagery-dependent feature as unlimited until the per-use cost is modelled; pre-ingesting into Mapsift's own tiling stack moves the cost from processing units to storage and egress and does not by itself close the question. The quota and egress reality is catalogued in `specs/data-and-tooling-references.md` section 1.5.
- **OQ-6 (promoted-element lifecycle):** the lifecycle of a promoted result (G3).
- **OQ-8 (legal-weight classification):** the rule classifying legal weight, arming preserve-not-discard across Families C, D, and G3. Highest-priority gap, since nearly every editing and completeness capability touches it. The registry detail the engineer will draw on to close it, what CAR and SIGEF actually record as the legal anchor (CAR's registration code and status, SIGEF's certification code), is catalogued in `specs/data-and-tooling-references.md` section 1.2; the rule itself stays open and is not decided here.
- **OQ-13 (delete-versus-edit retention):** the retention semantics of a delete (D5).
- **OQ-1 (shared topology):** the snapping-plus-PostGIS approach and the online-only propagation exception (D6).
- **OQ-14 (extension governance):** the three-tier model and the legal-weight gate (PRD section 0.4, PRD section 3), where the official and community store governance and the community sandbox are settled.

---

> End of Layer 1 draft (native floor), anti-requirements, and extension catalog. Layer 2 (transversal system behaviors) batch 1 follows below; Layer 2 batch 2 (T6 to T9) and its open-questions subsection, Layer 3 (data model and contracts), and Layer 4 (surfaces and platform, including the Field App) follow after, and the file may be split per layer once the material is complete.

---

## 5. Layer 2: Transversal system behaviors

> **Scope.** Layer 2 turns the foundation invariants into behavioral requirements that hold across every Layer 1 capability. This draft covers the collaboration, data, identity, and capability spine: the requirements driven by invariants I1, I2, I3, I8, I9, I10, I11 and foundation sections 4, 9, and 9.5 to 9.6.7. The non-functional block (performance and the I6 per-tile budget, security and sandboxing, privacy and LGPD per OQ-16 and OQ-17, accessibility, internationalization, observability, reliability, device support) is written separately and is not in this section. End-to-end type safety (I5) is a build-and-contract discipline carried in Layer 3 and the non-functional block, not here.
>
> **Batches.** Layer 2 lands in two batches so the review unit stays small. Batch 1 (here): T1 offline write path, T2 sync and convergence, T3 conflict resolution and history, T4 conflict-rule equivalence, T5 identity and authorship. Batch 2 (to follow): T6 tenancy and the permission model, T7 the capability-layer discipline, T8 the AI agent, T9 operation and schema versioning, and the open questions touched by Layer 2.

### 5.0 How a transversal requirement is written

Every requirement uses one shape, adapted from the Layer 1 template for behavior rather than feature:

- **ID and name.**
- **Requirement:** what must always hold.
- **Basis:** the foundation invariant and section it derives from, plus the CLAUDE.md C-test or anti-requirement where that is the direct trail to the pass/fail already on disk.
- **Provenance:** the dated foundation decision that closed it (for example closed v0.7, refined v0.8), because provenance is history and is not re-derivable.
- **Acceptance:** one pass/fail test, the behavior asserted, never the implementation.
- **Open / ADR:** the linked open question or deferred decision, when applicable.

A C-test of CLAUDE.md is the compressed digest of one or more of these; Layer 2 is the full specification the digest stands for.

### T1. Offline write path and persistence

The offline-first spine: an element edit is local and durable before the network, with collision-safe identity. Heavy data (layers) is out of this path (foundation section 3); the offline domain limits are foundation section 5.

#### T1.1 Local commit before any network round-trip
- **Requirement:** an edit to an element (draw, move a vertex, edit an attribute, style) is applied locally and shown to the user before any network call; within the foundation section 5 offline domain limits the app stays fully usable offline.
- **Basis:** I1; C1.
- **Provenance:** closed v0.1 (foundation section 2 thesis), framing fixed v0.2.
- **Acceptance:** with the network disabled, drawing or editing an element shows the result immediately with no server call, the edit persists across an app restart, and it flushes on reconnect.
- **Open / ADR:** the web store choice (IndexedDB or OPFS) is an ADR behind the storage interface (foundation section 5).

#### T1.2 Persistent operation queue behind one storage interface
- **Requirement:** every offline edit is appended to a local operation queue that survives an app or tab restart, behind one storage interface; closing the app never loses unsynced work, and the sync engine is platform-agnostic (pure functions over the operation log) with the store behind the interface.
- **Basis:** I1, foundation section 4, foundation section 5; C1.
- **Provenance:** closed v0.1, one persistence layer behind a storage interface fixed v0.2.
- **Acceptance:** edits made offline, then the app force-closed and reopened, are still present and still flush on reconnect; a desktop SQLite adapter, if built, sits behind the same interface with no second sync surface.

#### T1.3 Client-generated collision-safe identity
- **Requirement:** every feature gets a globally unique client-generated ID at creation, so an offline-created feature needs no server pre-allocation and never collides with another client's.
- **Basis:** I3; C3.
- **Provenance:** closed v0.1 (foundation section 4, client-generated IDs).
- **Acceptance:** features created offline on two clients sync without ID collision; no creation waits on the server for an identifier. The same identifier mechanism is reused for the per-installation clientID (I9, T2.3), which is distinct from the user (foundation section 9).

### T2. Sync, convergence, and idempotent recovery

Server-ordered sync over PostgreSQL, with versioning, gap detection, resync, and idempotent partial-failure recovery; Channels carries transport and presence only.

#### T2.1 Convergence under server order
- **Requirement:** after reconnect, all clients reach one identical state, and the order is the one PostgreSQL defines via a monotonic per-feature version; no client diverges permanently.
- **Basis:** I2, foundation section 10; C2.
- **Provenance:** closed v0.1, sync-tier role corrected v0.2.
- **Acceptance:** concurrent edits from two clients, replayed in server order, converge to one identical state on both.

#### T2.2 Ordering authority and transport separation
- **Requirement:** the op-queue flush is a transactional API call the database orders; Channels carries WebSocket transport and presence only, and the sync protocol uses versioning, gap detection, and resync rather than trusting at-most-once delivery; authoritative document state never lives in the Channels tier.
- **Basis:** I2, foundation section 10; C9.
- **Provenance:** corrected v0.2 (the sync tier's role).
- **Acceptance:** a dropped change notification is recovered by gap detection and resync from the database, not lost; no authoritative state is read from the WebSocket tier.
- **Open / ADR:** the Postgres-ordered sync is validated by the OQ-10 spike before spec is built on top of it.

#### T2.3 Idempotency and partial-failure recovery
- **Requirement:** every operation carries a per-client monotonic mutation number; the server tracks the per-client last-applied number and ignores any operation at or below it, so a resent flush is idempotent; the server echoes the last-applied number in the flush response and the client advances its cursor only from that echo; a client is a persistent installation (a clientID, generated as in I3), not the user, so the same user on two devices is two clients with non-colliding streams.
- **Basis:** I9, foundation section 4; C12.
- **Provenance:** closed v0.7, echo and clientID-per-installation closed v0.8.
- **Acceptance:** interrupt a flush after the server applies part of the queue, resend the full queue, and the final state is identical with no duplicated feature and no lost edit; the client advances its cursor from the echoed last-applied; and two clients of the same user (distinct clientIDs) do not collide and neither loses an operation to false dedup. **Added 2026-08-11 at the MAP-12 pickup:** an operation the server already holds, resent and surviving the dedup filter because it arrived under a different mutation number, is **answered as applied rather than refused**, so the flush succeeds and echoes. C12 exists to make the retry path safe, and a refusal there turns a legitimate resend into an error a client cannot tell apart from a real one, which is the fragility this requirement is against.
- **Open / ADR:** the expiry and collection of the per-clientID cursor. **Corrected 2026-08-11:** through this line's first form the whole policy was recorded as open, while **M4 had already settled its floor** in the same PRD round (retention is at least the maximum supported offline window) and says so in its own Provenance. What is open is the **mechanism** and the **length of the window**, both of which M4's own Open / ADR holds, together with the offline credential lifetime (T5.2) and the compatibility window (T9.4, OQ-15). This line points at M4 and states nothing of its own.

### T3. Conflict resolution, preservation, and history

Conflict resolves by granularity, with preserve-not-discard for legal-weight geometry, additive history, and a bounded editable working set.

#### T3.1 Resolution by granularity
- **Requirement:** conflicts resolve by granularity, not by session: different features never conflict, different properties of one feature never conflict, a trivial property or trivial-feature geometry resolves last-writer-wins, and a collision on a non-trivial property is flagged.
- **Basis:** I2, foundation section 4; C2.
- **Provenance:** inverted and closed v0.2 (granularity model).
- **Acceptance:** two clients editing different features, or different properties of one feature, both apply with no conflict; a concurrent edit to the same trivial property resolves last-writer-wins; a collision on a non-trivial property is flagged, never silently overwritten.

#### T3.2 Preserve-not-discard for legal-weight geometry
- **Requirement:** a conflict on the geometry of a legal-weight feature is detected and both versions are retained for human resolution; silent discard is prohibited, and a legal-weight feature never vanishes or resurrects without a record. Legal-weight classification may be dynamic (it can derive from an external, time-varying registry status), so the server is authoritative over whether a feature is legal-weight at flush and the client's classification is an optimistic preview, like its conflict resolution.
- **Basis:** foundation section 4; C7. Anti-requirement basis: never silently discard.
- **Provenance:** closed v0.2 (preserve-not-discard); dynamic-classification consequence noted v0.11 (the OQ-8 grounding in registry status).
- **Acceptance:** two offline geometry edits to the same legal-weight feature produce a flagged conflict with both versions retained, never a silent overwrite; a feature the server classifies legal-weight at flush is treated as legal-weight even if the offline client did not.
- **Open / ADR:** the legal-weight classification rule, including whether and how it changes over a feature's life and what becomes of prior last-writer-wins history when a feature becomes legal-weight, is OQ-8 (the environmental engineer's); the registry grounding is catalogued in `specs/data-and-tooling-references.md` section 1.2.

#### T3.3 No sub-geometric merge
- **Requirement:** when two users redraw the same feature's geometry, the system never fuses the two into one invented geometry; it presents both whole geometries and the user picks one or redraws.
- **Basis:** foundation section 4.
- **Provenance:** closed v0.2 (hard merge limit).
- **Acceptance:** two whole conflicting geometries are presented side by side; no third, un-drawn geometry is produced.

#### T3.4 Delete versus edit on legal weight
- **Requirement:** a delete colliding with a concurrent edit of the same legal-weight feature does not silently win; the collision is flagged and both the deletion intent and the surviving edited geometry are retained for human resolution.
- **Basis:** foundation section 4; C7.
- **Provenance:** closed v0.2 (delete-versus-edit).
- **Acceptance:** a delete conflicting with a concurrent edit on a legal-weight feature is flagged with both retained, never a silent removal or resurrection.
- **Open / ADR:** the trivial-feature rule and the precise retention semantics are OQ-13.

#### T3.5 Additive history and the immutable legal-weight trail
- **Requirement:** per-user undo touches only the acting user's operations; user-created version snapshots are restorable, and restoring a snapshot creates a new current version with that content and never deletes work that came after. Separately, the change history of a legal-weight feature is **immutable and survives deletion of the user who authored it**, retaining the minimum identification needed for audit, with a legal basis in the terms of use rather than consent (a retention obligation, not a preference); this applies the I10 preserved authorship chain to the user-deletion case. **The mechanism that makes that survivable in a regime with a right to erasure (settled v0.10):** the author on a chain entry is a **stable opaque identifier, resolvable to a person through a separate correspondence record**, so honouring an erasure request removes the correspondence and leaves the chain intact, ordered, and still able to prove that two distinct authors acted and in what order. That is what "the minimum identification needed for audit" concretely is, and it is what lets the same design hold in a regime that demands erasure and in one whose environmental liability does not prescribe (foundation OQ-16, OQ-20).
- **Basis:** foundation section 4, I10; C8, C13. LGPD posture: OQ-16.
- **Provenance:** additive history closed v0.2; the immutable legal-weight trail surviving user deletion settled this PRD round (grounded in the team's environmental-ERP practice), the legal basis confirmed under OQ-16.
- **Acceptance:** restoring an older snapshot leaves all later versions still retrievable; an undo reverts only the acting user's last action; deleting a user does not erase the legal-weight change history they authored, which stays inspectable with the minimum identification retained.
- **Open / ADR:** whether an entire legal-weight project can be physically deleted (physical delete erases the immutable trail, so likely archive-with-retention) and the retention-versus-storage-cost policy are OQ-20, owned across the engineer, the LGPD posture (OQ-16), and the performance-and-data-economy ADR.

#### T3.6 Bounded editable working set
- **Requirement:** only the small set of elements under live edit lives in the client-side editable source; a whole layer is never promoted to live editing, and the editable working set is capped. The cap is a measured budget, not a fixed count, because the cost is the MapLibre GeoJSON-source re-serialization and re-tiling on each edit plus the editing-marker count (foundation section 8), a budget distinct from the I6 per-tile render budget.
- **Basis:** foundation section 7, foundation section 8 (I6 is a separate budget; the three budgets are separated in N1).
- **Provenance:** closed v0.2 (the MapLibre editing restriction); the cap framed as a measured budget v0.11.
- **Acceptance:** on the named reference device, promoting the working set to live edit renders its first frame within the promotion-latency budget; a continuous vertex drag holds the per-update latency and frame-rate budgets with no main-thread task over the long-task line and no unbounded heap growth over a sustained drag; the editable working set is capped and a whole-layer promotion is refused. The cap is the largest set that holds all these budgets.
- **Open / ADR:** the named reference device (a specific field tablet plus a laptop, with OS, browser, and MapLibre versions pinned) and the concrete budget numbers are set by measurement; the starting hypothesis is on the order of a few hundred editable features and roughly ten thousand editable vertices, with a per-feature vertex ceiling. A diff-based editing adapter using MapLibre `updateData` with the stable I3 feature IDs is an ADR that can raise the cap, so the cap is stated as given the stock editing adapter, not as a fixed physical ceiling.

### T4. Conflict-rule equivalence and server authority

One rule specification, two golden-tested runtimes, the server the sole resolution authority, the rule versioned.

#### T4.1 One rule, two runtimes, golden-tested
- **Requirement:** the conflict-resolution rule has one specification, implemented in the client Rust core and the Python server, verified identical by golden tests in CI (canonical vectors run against both; divergence fails the build) with a defined tolerance where the rule consults a geometric predicate.
- **Basis:** I8, foundation section 9.6.6; C10.
- **Provenance:** closed v0.6 (supersedes the v0.4 PyO3 decision).
- **Acceptance:** the golden vectors resolve identically within tolerance on both runtimes; a deliberate divergence fails CI.

#### T4.2 Server-exclusive authority, optimistic client preview
- **Requirement:** resolution authority is the server's alone; the client's resolution is an optimistic preview reconciled on sync; legal-weight data is never decided on the client; authoritative geometry runs in PostGIS, with no Rust core on the server.
- **Basis:** I8, foundation section 9.6.6; C10.
- **Provenance:** closed v0.6.
- **Acceptance:** a client preview that diverges from the server is reconciled by resync, not trusted; no legal-weight resolution is finalized client-side; no Rust runs on the server.

#### T4.3 Rule versioned in the protocol
- **Requirement:** the conflict rule is versioned in the sync protocol so an old client meeting a new server is detected and reconciled, not silently trusted; this is the leading edge of the broader versioning principle (T9, foundation section 9.6.7).
- **Basis:** I8, foundation section 9.6.7; C10.
- **Provenance:** closed v0.6, generalized to the versioning principle v0.11.
- **Acceptance:** an old-client/new-server case is detected by rule version and reconciled, not lost.

### T5. Identity, authorship, and authorization

Authorship proved from the session, authorization validated server-side at flush, the legal-weight authorship chain preserved.

#### T5.1 Authorship stamped at creation, proved by session material
- **Requirement:** every operation is attributed to an author whose authoritative identity is the authenticated session that created it, proved by verifiable server-signed session material that travels with the operation and is normalized by the server at flush, not a free client field and not the flush session's identity; a divergence between claimed and provable author is normalized to the proven identity or rejected and retained for inspection.
- **Basis:** I10, foundation section 9; C13.
- **Provenance:** author stamped at creation closed v0.7; authoritative session-proved authorship closed v0.8.
- **Acceptance:** an operation whose claimed author diverges from the session-material identity is normalized to the proven identity or rejected, never accepted as claimed.
- **Open / ADR:** the offline authorship-proof mechanism is OQ-18.

#### T5.2 Authorization validated at flush
- **Requirement:** the server validates the author's authorization at flush (tenant isolation I4 plus the permission model); an operation whose author lost authorization while offline is flagged, never silently applied and never silently discarded.
- **Basis:** I10, foundation section 9; C13.
- **Provenance:** closed v0.7.
- **Acceptance:** an operation by an author who lost write permission while offline is flagged at flush, not applied and not dropped.
- **Open / ADR:** the offline-authenticated lifetime, the refresh-rotation policy, and the authorization-failed resolution UI are PRD decisions.

#### T5.3 Legal-weight authorship is the preserved ordered chain
- **Requirement:** the authorship of a legal-weight feature is the preserved ordered chain of attributed operations, each with its authoritative applied-at, never collapsed to a single stamp; created-at (the untrusted client clock) and applied-at (the server's authoritative stamp) are distinguished, applied-at authoritative.
- **Basis:** I10, foundation section 9; C13. Anti-requirement basis: AR5 (permanent history, not session-only undo).
- **Provenance:** closed v0.8 (authoritative authorship in three levels).
- **Acceptance:** a legal-weight feature edited by two authors in distinct sessions preserves both authors' chain, inspectable and in order, without collapsing to a single stamp.
- **Open / ADR:** the exact legal-weight audit-trail shape under Brazilian norm is OQ-12.

---

### T6. Tenancy and the permission model

The tenant is the hard isolation wall; above it a two-axis permission model (a governance role and a per-resource access level) capped by license, with workspace-inherited sharing and denial as revocation. Isolation and permission are different mechanisms (foundation section 9).

#### T6.1 Tenant isolation at the SQL layer
- **Requirement:** the tenant is the top container of the account (a personal user account or an organization), carried as a tenant identifier on every row and enforced at the SQL layer (row-level security or per-tenant views), so cross-tenant read or write is impossible by construction, including for direct-to-PostGIS readers such as the tile server; the workspace and project below the tenant are organization and permission, not isolation. The single deliberate exception is the authenticated user's own membership rows, readable across tenants for the login question, `FOR SELECT` only: they reveal nothing but the reader's own places (I4 as revised v0.17.1; ADR-0005 section 8).
- **Basis:** I4, foundation section 9; C4.
- **Provenance:** reopened and closed v0.11 (tenant as the top of the account tree); the login-question exception decided 2026-08-05 with MAP-27.
- **Acceptance:** a cross-tenant read or write, including a tile request, is impossible by construction and is indistinguishable from a resource that does not exist; the tile role connects non-privileged and sets the tenant on its session, never with RLS bypassed. The single exception: the authenticated user's own membership rows for the login question, readable with no tenant bound and `FOR SELECT` only (ADR-0005 section 8).
- **Open / ADR: CLOSED in v0.13 by ADR-0005.** The choice is row-level security, enabled **and forced**, with per-tenant views rejected; the roles are four and none of them privileged; the tenant is bound transaction-scoped and parameterised and read through a guarded cast; and the tile path carries a three-point contract that the tile server choice inherits rather than negotiates. The BYPASSRLS hazard this field named as the load-bearing caveat was **measured rather than argued** (a role owning the tables without FORCE, a role holding BYPASSRLS, and a SECURITY DEFINER function owned by the owner each saw every tenant), and it is now the N2 test rather than a caveat. What the same measurement added, and what no reading had produced, is that **referential integrity checks bypass the policy**, so a cross-tenant foreign key and a cross-tenant unique-key collision are channels no policy closes; composite keys close them and are part of that ADR.

#### T6.2 Two axes plus a ceiling: governance role, per-resource access, license
- **Requirement:** permission resolves over two orthogonal axes plus a ceiling: a per-tenant **governance role** (owner, admin, member), a **per-resource access level** (view, comment, edit, from A3), and a **license/seat ceiling**, with effective capability = min(license, per-resource grant, applicable default). The access level is never raised above the license, and the governance role is not a fourth access level.
- **Basis:** foundation section 9 (the permission model deferred to the PRD); the A3 three levels and the license ceiling.
- **Provenance:** the two-axis model and the license ceiling are the PRD's per foundation section 9, settled this round (foundation v0.11).
- **Acceptance:** a user on a view-only license granted edit on a resource still cannot edit it until upgraded; a per-resource grant never exceeds the license or the applicable default; the governance role is independent of the view/comment/edit grant; a user without a full editing license cannot hold the admin or owner role.
- **Open / ADR:** the concrete license/seat tiers (beyond a full editing tier and a read-plus-comment viewer tier) are a product and pricing decision (OQ-7), not fixed here.

#### T6.3 Governance is not content editing, and no legal-weight resource is ever ownerless
- **Requirement:** the governance role (admin, owner) governs the tenant (manage members, assign licenses, settings, billing, security) but grants no content override: an admin has no power over a project's content that an editor lacks, and deletion or alteration of a legal-weight feature stays under preserve-not-discard for every role, the admin included; the admin and owner roles require a full editing license. Ownership is single-owner with transfer, and **a legal-weight resource is never ownerless**: removing an owner transfers ownership in the same act (no ownerless interval), and an owner who disappears without being removed (an inactive or departed account) is reclaimed by an admin (the empty-team pattern); there is never a silent orphan state.
- **Basis:** foundation section 9 (governance subordinate to preserve-not-discard); I10, I11; C7, C13.
- **Provenance:** the no-content-override constraint settled in foundation v0.11 (foundation section 9 Decision); single-owner-with-admin-reclaim and the no-ownerless rule settled this PRD round.
- **Acceptance:** an admin without an edit grant on a project cannot edit its content; an admin attempting to delete a legal-weight feature goes through preserve-not-discard, never a silent removal; removing an owner transfers ownership synchronously with no ownerless interval; an owner who disappeared is reclaimable by an admin and the reclaim is recorded; a legal-weight resource is never in an ownerless state.
- **Open / ADR:** the ownership-transfer and reclaim mechanism (the trigger detection and the recorded handover) is deferred to the detailed permission model.

#### T6.4 Sharing: workspace inheritance plus standalone and per-project controls
- **Requirement:** there are three sharing operations and Mapsift offers all three. (1) **Workspace inheritance:** sharing a workspace flows its grant and level to every project within (the default-with-override shape), and a per-project or per-person exception can only lower or revoke the inherited level, never raise it. (2) **Standalone project share:** a project can be shared directly, outside the workspace inheritance, so a recipient sees only that project and not the rest of the workspace (the comment-only-for-one-client case). (3) **Workspace inheritance control:** the workspace admin decides, in the workspace settings, which projects participate in the workspace's shared package and which are excluded from inheritance, an organization-level control. The workspace admin always reaches every project in the workspace; an editor or commenter can have a project revoked.
- **Basis:** foundation section 9 (workspace-inherited sharing deferred to the PRD); A3.
- **Provenance:** the PRD's per foundation section 9; the three sharing modes settled this PRD round.
- **Acceptance:** sharing a workspace at edit makes every project in it editable for the recipient at most; a per-project or per-person exception lowers or revokes but never raises; a project shared standalone is visible to its recipient without exposing the rest of the workspace; a project excluded from inheritance in the workspace settings does not enter the workspace share; a workspace admin reaches every project, and an editor with a revoked project cannot reach it.
- **Open / ADR:** the UI and the precedence rules when the modes overlap (a project both excluded from inheritance and shared standalone) are the detailed permission model and Layer 4.

#### T6.5 Access denial is revocation, not concealment, and listings derive from the isolation layer
- **Requirement:** denying access removes the grant so the resource is genuinely unreachable by any path (direct link, API, tile, search, and any listing or enumeration), never hidden from a listing while remaining fetchable; within a tenant a denied access returns an explicit denial with a resolution path (contact the workspace admin), and across tenants the resource is indistinguishable from one that does not exist (the I4 wall). Every project listing or enumeration **derives from the same isolation-and-permission layer that serves the data** (the RLS-filtered query), never from a client cache or a search index that can diverge; where a search index exists it is treated as derived and re-filtered by the same layer on read, not trusted as a source, so a listing card cannot exist without the grant behind it.
- **Basis:** foundation section 9 (access denial is revocation, not concealment); I4; C4, C7.
- **Provenance:** principle closed v0.11 (foundation section 9); the listing-derives-from-isolation refinement settled this PRD round; the mechanism is the PRD's.
- **Acceptance:** a user without a grant who fetches a resource URL within their tenant gets an explicit access-denied with a contact path and the data never leaves the database; a cross-tenant fetch returns not-found, indistinguishable from an invented URL; a revoked project does not appear in the workspace listing, and the listing is proven to derive from the isolation layer (the RLS-filtered query), not from a cache or a search index, so a card never appears without the grant behind it.
- **Open / ADR:** the per-surface denial response (the within-tenant denial-with-resolution versus the cross-tenant not-found-indistinguishable) and the search-index re-filtering are mechanism, an ADR detail; the visual sharing-scope warning ("all projects here will be shared together") is a Layer 4 concern.

### T7. The capability layer

Every data operation is a named capability on one layer the app, extensions, the SDK, and the agent all consume; the boundary passes serializable data only, every capability respects the invariants by construction, and each carries a machine-readable description and composable output.

#### T7.1 Named, asynchronous, serializable-boundary capabilities
- **Requirement:** data operations are expressed as named, asynchronous capabilities that exchange serializable data and never live references (no live map object or DB connection across the boundary); the app is the first consumer of its own public capability layer, not a set of buried internal calls.
- **Basis:** foundation section 9.5; the serializable-boundary principle shared with foundation section 9.6.4 (C11).
- **Provenance:** closed v0.3 (the capability layer).
- **Acceptance:** a capability is invoked by name with serializable input and returns serializable output; no live handle crosses the boundary; the app reaches a tool only through the capability layer.

#### T7.2 Invariant-respecting by construction
- **Requirement:** every capability respects tenant isolation (I4) and the conflict-resolution model (foundation section 4) by construction; there is no privileged internal shortcut that bypasses an invariant, so a capability that writes legal-weight geometry goes through the same detect-and-preserve path a human does.
- **Basis:** foundation section 9.5; C4, C7.
- **Provenance:** closed v0.3.
- **Acceptance:** a capability cannot read or write across a tenant boundary; a capability writing legal-weight geometry triggers preserve-not-discard exactly as a human edit does; no capability has an invariant-bypassing path.

#### T7.3 Machine-readable description and composable output
- **Requirement:** every capability carries a machine-readable structured description (what it does, its parameters, preconditions, effects, when to use it, the MCP tool-description-plus-input-schema pattern) and returns composable output (structured data a next capability can consume), so an autonomous consumer can choose and chain capabilities.
- **Basis:** foundation section 9.5.1.
- **Provenance:** closed v0.10 (the two enabling properties).
- **Acceptance:** a capability exposes a structured description sufficient for a non-human consumer to select it; one capability's output is a valid readable input to a next capability (a buffer result feeds an intersect).

### T8. The AI agent

The agent is one more capability-layer consumer, online-only, acting with the user's permission, its writes mediated and gated.

#### T8.1 A capability-layer consumer, online-only, inheriting the user's permission
- **Requirement:** the AI agent is a consumer of the capability layer (T7), not a privileged path; it is online-only (server-orchestrated, consuming the layer server-side) and acts with the permission of the user it acts for, seeing only what that user sees and writing only what that user may write.
- **Basis:** I11, foundation section 9.5.1; C14.
- **Provenance:** closed v0.10 (the agent as a first-class consumer, online-only).
- **Acceptance:** the agent reaches data only through the capability layer under the acting user's permission; offline, the agent is unavailable while the rest of the client keeps working; the agent cannot read or write anything the acting user cannot.

#### T8.2 Mediation provenance
- **Requirement:** an agent-originated write carries mediation provenance (the user through the identified agent), distinct from a direct human write by the same user and preserved in the trail.
- **Basis:** I11, foundation section 9.5.1; C14.
- **Provenance:** closed v0.10.
- **Acceptance:** an agent-originated operation is recorded as user-through-agent, distinguishable in the trail from a direct human write by the same user.

#### T8.3 Legal-weight and bulk gate
- **Requirement:** an agent action on a legal-weight feature or a bulk write requires human confirmation before it is applied, all under authorship and authorization (I10) and preserve-not-discard.
- **Basis:** I11, foundation section 9.5.1; C14, C7, C13.
- **Provenance:** closed v0.10.
- **Acceptance:** an agent attempting to delete or edit a legal-weight feature triggers human confirmation and is never applied directly.
- **Open / ADR:** the bulk threshold, the gate UX, how the trail materializes mediation, and the agent's per-capability permission posture are OQ-19; the exposure protocol (for example MCP) is an ADR.

### T9. Operation and schema versioning

The mechanism implementing the foundation's bidirectional versioning principle (foundation section 9.6.7): additive by default, a versioned operation envelope, a server-side upcaster, and a typed force-upgrade in both directions.

#### T9.1 Additive-by-default evolution
- **Requirement:** operation and schema changes are additive by default (new optional fields, new operation types), never renaming, repurposing, or changing the meaning of an existing field; an unknown or additive field is read tolerantly only where it does not bear on the conflict rule, on legal-weight geometry, or on authorship.
- **Basis:** foundation section 9.6.7 (the principle, with the moral-line carve-out).
- **Provenance:** principle closed v0.11; the mechanism is the PRD's (OQ-15).
- **Acceptance:** an additive field is ignored safely by an older runtime; a change touching the conflict rule, legal-weight geometry, or authorship is not absorbed by tolerant reading but routed through versioning.

#### T9.2 Versioned operation envelope
- **Requirement:** every operation carries an envelope with its operation type and an operation-schema version, an axis independent of the per-feature version (which orders and detects conflict), the per-client mutation number (which gives idempotency), and the conflict-rule version (T4.3); the envelope is the generated cross-language contract.
- **Basis:** foundation section 9.6.7; I8, I9.
- **Provenance:** mechanism, this PRD round (OQ-15).
- **Acceptance:** an operation is tagged with its type and schema version; the four versions (op-schema, per-feature, mutation number, rule version) are distinct and do not collide.

#### T9.3 Server-side upcaster, no downcaster
- **Requirement:** when a breaking change cannot be additive, the server upcasts an old operation to the current schema on the way in, before it reaches the conflict rule; upcasting is server-side only (no client upcaster, no Rust on the server, so the C10 golden-test surface does not grow), and the server never downcasts authoritative state on the way out.
- **Basis:** foundation section 9.6.7 (upcast in, never downcast out); C10.
- **Provenance:** mechanism, this PRD round (OQ-15).
- **Acceptance:** an operation in an older schema is upcast on the server and resolved by the current rule; no downcaster exists; no upcasting runs on the client.

#### T9.4 Typed force-upgrade in both directions
- **Requirement:** a minimum-supported-version window bounds compatibility; below it, the server rejects an old client's flush with an explicit typed payload that forces an upgrade, and on resync or pull an old client that cannot read a breaking change to correctness-relevant state (the rule, legal-weight geometry, authorship) force-upgrades before rendering rather than silently downcasting; a legal-weight feature an old client cannot interpret is surfaced as needing an upgrade, never silently omitted from the view.
- **Basis:** foundation section 9.6.7 (bidirectional, typed rejection, never silent); C7, C10.
- **Provenance:** mechanism, this PRD round (OQ-15).
- **Acceptance:** a too-old client flushing receives a typed force-upgrade, not a silent break; a too-old client pulling new-schema legal-weight state force-upgrades before rendering and never shows it wrong or silently drops it.
- **Open / ADR:** the compatibility-window length (how many versions or how much time) and whether to add handshake version negotiation beyond client-sends-versions-server-accepts-or-rejects are OQ-15 mechanism parameters.

---

### 5.9 Open questions touched by Layer 2

Foundation OQs and PRD-level open choices that Layer 2 marks rather than closes, gathered so the transversal layer's dependencies are visible in one place (mirroring the Layer 1 foundation section 4 structure).

- **OQ-8 (legal-weight classification, possibly dynamic):** T3.2 marks that classification may derive from an external, time-varying registry status, so it is server-authoritative, and the retroactive-history question (what happens to prior last-writer-wins history when a feature becomes legal-weight) is open; owned by the environmental engineer; the registry grounding is in `specs/data-and-tooling-references.md` section 1.2.
- **OQ-10 (Postgres-ordered sync spike):** T2.2; validate ordered op-flush, per-feature version, gap detection, and resync before spec is built on top.
- **OQ-12 (Brazilian audit-trail norm):** T5.3; the exact legal-weight authorship-trail shape under the georeferencing and environmental norms.
- **OQ-13 (delete-versus-edit retention):** T3.4; the trivial-feature rule and the precise retention semantics.
- **OQ-14 (extension governance and sandbox):** T7; the capability layer enables extensions, whose three-tier governance and sandbox are settled in PRD section 3 and OQ-14.
- **OQ-15 (operation and schema versioning mechanism):** T9; the principle is closed (foundation section 9.6.7), the mechanism here is the recommended shape, and the compatibility-window length and the handshake-negotiation question stay open.
- **OQ-18 (offline authorship-proof mechanism):** T5.1; the per-platform proof mechanism for session-material authorship.
- **OQ-19 (agent-write governance):** T8.3; the bulk threshold, the gate UX, the mediation-trail shape, and the agent's per-capability permission posture.
- **OQ-20 (legal-weight retention and project deletion):** T3.5; whether a legal-weight project can be physically deleted at all (likely archive-with-retention, since physical delete erases the immutable trail the moral line and I10 preserve) and the retention-versus-storage-cost policy (a tiered retention plus storage-tiering question), crossing the LGPD posture (OQ-16), the offline-store protection (OQ-17), and the performance-and-data-economy ADR; opened in foundation section 13, not closed here.
- **Closed this round (recorded):** the three sharing modes (per-person revocation, per-project standalone share, and the workspace-settings inheritance control) are all provided (T6.4), and ownership is single-owner-with-admin-reclaim with no ownerless state (T6.3); the remaining license/seat tiers are a product and pricing decision (OQ-7).
- **T3.6 cap measurement (PRD task):** the named reference device (a specific field tablet plus a laptop, with OS, browser, and MapLibre versions pinned) and the concrete budget numbers are set by measurement, not assumed.

---

> End of Layer 2 (T1 to T9) and its open questions. Layer 3 (data model and contracts) batch 1 follows below; Layer 3 batch 2 and Layer 4 (surfaces and platform, including the Field App) follow after, and the file may be split per layer once the material is complete.

---

## 6. Layer 3: Data model and contracts

> **Scope.** Layer 3 fixes the shapes the system persists and exchanges: the account tree, the elements-versus-layers split as persisted entities, identity, geometry and the coordinate reference rule, the attribute schema, and the legal-weight marker (batch 1); then the operation envelope and its catalog, the versioning axes, the serializable boundary payloads, the generated cross-language contracts, the conflict-rule contract with its tolerance, the editable working set, and the append-only log with its projections (batch 2). It sits above code and below the ADRs: it states the shape and the rule that shape must satisfy, never the table definition, the migration, or the wire encoding, which are the ADRs'.
>
> **IDs.** Layer 3 requirements are numbered M1 to Mn (model). The M prefix is unrelated to the MC-xx market codes.
>
> **Batches.** Layer 3 was written in two batches so the review unit stayed small, the same discipline Layer 2 used, and both have landed. Batch 1, the data model: M1 the account tree, M2 elements and layers, M3 identity, M4 the client instance and its cursor, M5 geometry and the coordinate reference rule, M6 the attribute schema, M7 the legal-weight marker. Batch 2, the contracts: M8 the operation envelope, M9 the operation catalog and the granularity rule, M10 the five version axes and the ordering rule, M11 the serializable boundary, M12 the generated contracts and type safety, M13 the conflict-rule contract and its tolerance, M14 the editable working set, M15 the append-only log and its projections, plus subsection 6.9.
>
> **The four debts Layer 2 left to Layer 3 are paid here:** the versioned operation envelope as a generated cross-language contract (M8), the conflict rule's geometry contract with a tolerance declared in metres (M13), the geometry representation in the editable source (M14), and the coordinate reference rule that previously had no home (M5).

### 6.0 How a Layer 3 requirement is written

The Layer 2 shape (ID and name, Requirement, Basis, Provenance, Acceptance, Open/ADR) with one addition: **Shape**, the fields the contract carries and what each one means, because in Layer 3 the shape is the requirement. A Shape line names fields and their meaning; it never names a type, a column, or an encoding, which belong to the ADR.

### M1. The account tree and the tenant identifier

- **Requirement:** the account tree is five entities, with the organization appearing as a tenant kind rather than as a sixth. A **user** is the global durable identity that holds the credential and may belong to several tenants. A **tenant** is the top container of an account and always exists as a record carrying a kind, personal or organization: a personal tenant is created with the user and holds exactly one owner membership, an organization tenant exists only when a company exists. A **membership** joins one user to one tenant and carries that user's governance role and license there. A **workspace** groups projects inside a tenant and is where sharing lives. A **project** holds the elements and layers. Every row that belongs to a tenant carries the **tenant identifier**, and that identifier is the key the SQL-layer isolation checks (T6.1). A workspace and a project each resolve to exactly one tenant, and the tenant of a workspace or project is immutable in the ordinary write path.
- **Shape:** user (identifier, credential identity); tenant (identifier, kind personal or organization); membership (user, tenant, governance role, license); workspace (identifier, tenant, name); project (identifier, tenant, workspace, name); tenant identifier on every tenant-owned row.
- **Basis:** I4, foundation section 9 (the tenant as the top of the account tree); T6.1, T6.2; C4.
- **Provenance:** the tree closed in foundation v0.11; the always-materialized tenant record (so a personal account and an organization take the same isolation path) settled this PRD round.
- **Acceptance:** every tenant-owned row carries a tenant identifier and no query path, including the ORM, a capability, and the tile role, reads a row whose tenant identifier differs from the session's (the single exception is the user's own membership rows, the T6.1 login question); creating a personal account creates its tenant with one owner membership and needs no organization; a user belonging to two tenants has one identity and two memberships; a workspace and a project each resolve to exactly one tenant, and an ordinary update cannot move either across tenants.
- **Open / ADR:** row-level security versus per-tenant views, and the tile role's session-tenant wiring, are the tile and data ADR (T6.1); the license and seat tiers are OQ-7; a deliberate cross-tenant transfer of a workspace or project is a distinct recorded operation and is out of Layer 3's scope until it is specified.

### M2. Elements and layers as persisted shapes, and the class that decides the path

- **Requirement:** a **layer** is the structure and its metadata (name, geometry kind or raster, attribute schema, style, provenance, legal-weight marker, storage class); a **feature** belongs to exactly one layer and carries geometry plus attribute values. Every layer declares a **storage class** that decides which path its features take, and the class is a property of the layer, never of an individual feature. An **element layer** is light: its features enter the operation queue, are editable offline, and follow the whole of Layer 2 (I1, I3, I9, I10). A **served layer** is heavy: it is server-authoritative, reaches the client as tiles, and its features never enter the operation queue. **A feature's geometry belongs to the family its layer declares**, with multipart geometry and a ring carrying an enclave inside that family rather than outside it (D3), and a geometry of another family is refused rather than stored: the declared kind is a contract on the layer's features and not a label on the layer. At import, a dataset lands as an element layer when it fits the **element budget** (feature count, total vertex count, and byte size) and as a served layer otherwise; the budget is measured, not guessed, and it is measured by the same protocol as, **and is distinct from**, the editable working-set budget (T3.6, N1).
- **Shape:** layer (identifier, tenant, project, name, kind vector or raster, geometry kind, storage class element or served, attribute schema, style, source and attribution and license, legal-weight marker); feature (identifier, tenant, project, layer, geometry, attribute values).
- **Basis:** foundation section 3 (the elements and layers frontier), foundation section 5 (the qualified offline-import rule, v0.12), foundation section 6, foundation section 7; B2, B4, C1, D1; T3.6.
- **Provenance:** the frontier closed in foundation v0.1; the storage class as the explicit carrier of that frontier, and the import classification by a measured element budget, settled in v0.9. **The geometry-family contract is settled in v0.15**, raised out of a spec-per-task that had invented it, on three consequences the next slice builds and none of which can defend itself: a paint specification is per geometry type, so a stray geometry does not render **and does not say so** (AR1); D8 makes area and perimeter automatic and authoritative on a polygon layer, and a line in one has no area, which in a product computing a legal reserve's hectares is worse than a render fault; and an interchange format carries a single shape type in its header, so a mixed layer either fails to export or exports incomplete, and J1 promises exactly that interoperability.
- **Acceptance:** a served layer's features never appear in the operation queue and an element layer's do; an import that fits the element budget is editable offline and flushes on reconnect; an import above the budget requires a connection and is refused offline with explicit feedback, never queued as if it would sync; a feature does not change path without its layer changing class or without an explicit promotion; and a geometry of the family its layer declares is stored, including a multipart one and one carrying an enclave, while a geometry of another family is refused rather than stored.
- **Open / ADR:** where a promoted analysis result lives (copied into an element layer, which the storage class makes the natural shape, versus promoted in place inside the served layer) is OQ-6, and Layer 3 does not close it; the concrete element-budget numbers are set by the same measurement that sets the T3.6 cap.

### M3. Identity of every created object

- **Requirement:** every feature, layer, group, project, workspace, comment, and operation carries an identifier generated by the client that creates it, globally unique with no coordination, opaque to every consumer (carrying no meaning, no ordering authority, and no embedded permission), stable for the object's life, and never reused after deletion. The server never allocates an identifier for an object a client can create offline, and never rewrites an identifier it received.
- **Shape:** a 128-bit identifier with one canonical textual form used identically in Rust, Python, TypeScript, and Dart.
- **Basis:** I3, foundation section 4 (client-generated identifiers); C3; T1.3.
- **Provenance:** closed in foundation v0.1; the opacity and no-reuse rules settled this PRD round.
- **Acceptance:** two clients creating features offline sync with no collision; an identifier is unchanged by a resend; no code path derives meaning, order, or authority from an identifier's content; an identifier belonging to a deleted feature is never assigned to a new one.
- **Open / ADR: CLOSED in v0.14 by ADR-0006.** The variant is a **random** 128-bit identifier, and the reasoning is measured rather than balanced: the index locality a time-ordered identifier buys is **contingent on the device clock being right**, and with one row in five minted on a clock up to thirty days out the resulting index was 2.45 times the size of the well-behaved ordered one and roughly twice the random one, with its pages half empty. The trade this requirement anticipated therefore does not exist in this product's conditions. Two properties settle the rest: a time-ordered identifier is **not opaque** (PostgreSQL reads its creation instant back out in one function call), which this requirement forbids by name; and nothing needs the identifier to sort, because ADR-0004 already gives the model a server-assigned per-project version and a per-feature version. Created-at and applied-at (T5.3) remain the only times in the trail, now because the identifier carries no third one rather than because a rule says not to read it.

### M4. The client instance and its server cursor

- **Requirement:** a **clientID** identifies a persistent installation. It is generated by the M3 mechanism, persisted in the local store, stable across restarts, distinct from the user and from the session, and never used as an author identity (authorship is T5.1). The server keeps one cursor per clientID **within one flush domain**, one tenant and one project (corrected 2026-08-11; foundation v0.18), holding the last-applied mutation number. Cursor retention is at least the maximum supported offline window, so a client that was offline for the longest supported period still meets its cursor on return. A flush arriving from a clientID **the server holds no cursor for in the flush domain that batch addresses** is treated as a new client only when it starts at the first mutation number; a flush that starts above it with no cursor is a typed reconciliation response, never applied optimistically, because applying it blindly would risk re-applying operations the server already holds.
- **Shape:** clientID (identifier, persisted locally); server cursor (clientID, last-applied mutation number, last-seen time). **Sharpened 2026-08-11 at the MAP-12 pickup, and corrected the same day at the review, which is why the correction is written here rather than folded in silently.** The cursor is keyed by **clientID, tenant and project together**, matching the flush domain exactly (M10, and ADR-0010 decision 6 for what a flush addresses). **That phrase was an assertion before it was true, and the gap is recorded rather than closed in silence:** when it was written, decision 6 partitioned a flush by tenant and project and said nothing about the clientID, so a batch of two installations was admissible and the single echo this requirement mandates had no defined answer for it. Decision 6 gained its fourth composition rule the same day, at this task's review, which is what makes "exactly" a fact. **The first form of this sentence keyed it on tenant and clientID alone and was wrong**, because ADR-0010 decision 6 had already partitioned a flush by project on 2026-08-10: two projects of one tenant would have shared one cursor and deduplicated each other's operations, and a stream spanning projects would have presented every flush with a gap the client could never fill. Two rules follow and neither is optional. **The tenant is in the key because C4 puts it on every row**, and a cursor row without it cannot be read by the tenant-bound role at all; ADR-0005 section 8's exception is `FOR SELECT` only and a cursor is written, so it does not reach here. And **the absence of the cursor row is the only representation of an absent cursor**, never a stored zero, because the first mutation number is zero (M10) and zero is therefore a legitimate applied value rather than an available sentinel.
- **Basis:** I9, foundation section 4 (the v0.8 client definition and the acknowledgement echo); C12; T2.3.
- **Provenance:** the clientID and the cursor closed in foundation v0.8; the retention floor and the missing-cursor rule settled this PRD round, closing the garbage-collection item T2.3 left open.
- **Acceptance:** reinstalling yields a new clientID whose stream starts at the first mutation number; two installations of one user hold two clientIDs and two cursors and neither loses an operation to false dedup; a client whose cursor was collected and then flushes above the first mutation number receives a typed reconciliation response rather than a silent re-apply; a cursor is never collected inside the supported offline window.
- **Open / ADR:** the length of the maximum supported offline window is a product and security decision shared with the offline credential lifetime (T5.2) and the compatibility window (T9.4, OQ-15); the collection mechanism is an ADR.

### M5. Geometry and the coordinate reference rule

- **Requirement:** five rules, and they are correctness rather than preference.
  1. **One storage frame.** All stored and interchanged geometry is in one declared geographic CRS, SIRGAS 2000 (EPSG:4674). Every dataset's original CRS is recorded at import and never discarded. Transformation to the storage frame happens once, authoritatively, on the server at import; the client never reprojects authoritative geometry.
  2. **No metric in degrees, and the frame is chosen by the metric's purpose.** No area, perimeter, or distance is ever computed in degrees on a geographic frame. Every metric is computed in a **declared metric frame selected by the metric's purpose**, from a closed named set, and the value travels with the frame it was computed in and with the authority that computed it (a client preview or the authoritative server value). There is no single correct metric frame and no global constant to hard-code: the regime that governs a number decides its frame, so the frame is a per-purpose, per-jurisdiction configuration and the formula never picks one silently. The closed set for the anchor domain is three frames, with UTM deliberately excluded as an authoritative frame:
     - **Geodesic on the SIRGAS 2000 ellipsoid**, the general-purpose default and the frame of every client preview and every non-legal figure. It needs no zone and no origin, so it is stable worldwide and cheap in the client core, which is what a general-purpose tool needs where no norm governs the number.
     - **Sistema Geodesico Local (SGL)**, the local topocentric plane, for the area of a **certified rural parcel** under the INCRA regime. This is the norm's own rule, and the norm is the **MTGIR 2nd edition** (Manual Tecnico para Georreferenciamento de Imoveis Rurais, approved by Portaria INCRA 2.502 of 22/12/2022, published 23/12/2022). Item **1.4.6**: "O calculo de area deve ser realizado com base nas coordenadas referenciadas ao Sistema Geodesico Local (SGL)", cross-referring to item **3.8.1** for the geocentric-to-local conversion; item **3.8.3** fixes the computation as the Gauss formula over the local cartesian coordinates, expressed in hectares. The same norm fixes the positional precision of the vertices that feed it (item **1.4.4**: better than or equal to 0,50 m on artificial limits, 3,00 m on natural limits, 7,50 m on inaccessible limits, plus a tolerance of at most three times that value between two credentialed surveyors measuring the same vertex). **Citation correction, v0.10:** through PRD v0.9 this requirement cited the NTGIR 3rd edition (2013), which **Portaria INCRA 629 of 05/04/2022 revoked**, together with the Manual Tecnico de Posicionamento 1st edition this requirement also pointed at. The content the rule depends on survived intact and renumbered; verified against the primary source on 2026-07-31 and recorded in `specs/domain-questions.md` section V.1.
     - **An equal-area conic on SIRGAS 2000** (the South America Albers family), for **environmental area figures** in the CAR and analysis chain (property area, APP, legal reserve, native-vegetation remnant), which is the frame the MMA and CSR CAR methodology reprojects to before computing hectares.
  3. **No silent drift.** Geometry that leaves storage to be rendered or edited and returns unedited returns identical, coordinate for coordinate. No render-path or edit-path transformation mutates a stored coordinate, and any datum transformation between the storage frame and the render frame is an explicit recorded decision, confirmed against the projection library's actual behaviour rather than assumed.
  4. **No silent precision loss.** Coordinates are carried at full double precision from the database to the boundary to the client; no serialization or display step rounds, truncates, or re-parses a coordinate into storage.
  5. **UTM is not an authoritative frame for a legal-weight area.** INCRA certified parcel areas in UTM for about ten years and abandoned it when SIGEF came into force in 2013, because the UTM distortion varies with the parcel's position inside its zone. The measured divergence between the SGL and UTM areas of the same certified parcels runs from about +0,10 percent near the zone centre to about -0,14 percent near its edges, roughly 1 to 1,4 hectares on a thousand-hectare property, a figure that lands in a legal document. UTM stays available as an interchange and display CRS, and it is not where a legal number is produced.
- **Shape:** geometry (coordinates in the storage frame, geometry kind); layer or dataset provenance (source CRS as declared, source CRS as detected, transformation applied); metric value (number, unit, purpose, metric frame, authority preview or authoritative, computed-at); metric frame (name, definition, and for the SGL the origin used, since the SGL is defined per parcel).
- **Basis:** B2, D8, G1, J1; AR2, AR3; C7 (a wrong reprojection moves a legal boundary); `specs/data-and-tooling-references.md` sections 1.2, 1.4, and 2.1.
- **Provenance:** settled this PRD round. The engineering was already recorded in the reference catalog (foundation section 2.1) and the rule had no home in a normative document; Layer 3 is that home. The frame-by-purpose rule and the three-frame set were settled against the primary norm as cited at the time (NTGIR 3rd edition items 4.6 and 4.4, corrected in v0.10 to the live MTGIR 2nd edition items 1.4.6 and 1.4.4 after that standard was found revoked) and the CAR methodology, after the first draft of this requirement had left the question open as a binary between a geodesic computation and a UTM zone, which the norm shows is the wrong binary.
- **Acceptance:** importing a SIRGAS 2000 UTM file stores geometry in EPSG:4674 with both the declared and the detected source CRS recorded, and an export round-trip reproduces the source coordinates within the declared precision; a reported area or perimeter carries its purpose, the metric frame it was computed in, and its authority, and a metric computed in degrees on a geographic frame fails the test suite by construction; the area of a certified rural parcel is computed in the SGL frame and a generic measurement in the geodesic frame, and each states which; changing the frame bound to a purpose changes the computed value with no formula edited, proving the frame is configuration rather than a constant; a feature promoted to editing and returned untouched is identical in storage, coordinate for coordinate; at least one foreign national grid reprojects to the correct location (B2), proving the rule is general and not a Brazil special case.
- **Open / ADR (the frame rule is closed; two mechanism items remain, one having closed in v0.10):** (1) how the SGL is computed on the server, either PROJ's topocentric conversion (`+proj=topocentric`, the EPSG:9836 conversion) reached through `ST_TransformPipeline` (PostGIS 3.4 and later, minding that a PROJ pipeline string skips automatic axis normalisation) or the explicit geocentric-to-local rotation the norm points at, is an ADR; (2) **CLOSED in v0.10, and it closed by reading the live norm rather than the revoked one it pointed at.** This item required INCRA's Manual Tecnico de Posicionamento to be read before the SGL frame was implemented, because the norm's general definition of the local frame speaks of a chosen vertex as the origin while the practice reported in the literature is the parcel centroid, and the difference is not cosmetic on a large parcel. That manual was revoked in 2022 by the same act that revoked the NTGIR, and its successor answers the question in writing: **MTGIR 2nd edition item 3.8.1(a) fixes the origin, for the purpose of computing area, as the mean of the coordinates of the parcel in question**, so the reported practice is now the written rule and there is no ambiguity left to resolve. Verified against the primary source on 2026-07-31 (`specs/domain-questions.md` section V.1). What remains of this item is only that the ADR in (1) implements that origin and does not invent another; (3) the concrete equal-area conic definition for the CAR frame (the South America Albers parameters, and whether it is carried as an authority code or as an explicit definition) is pinned in the same ADR. Adding a frame for a jurisdiction outside Brazil is configuration under this rule and under M16, and needs no new requirement.
- **Open (Layer 4):** how the interface presents a preview value next to the later authoritative value is a surface concern, and Layer 3 only requires that the contract carry the authority so the surface can tell them apart. One calibration for that design: the real divergence between the frames is on the order of a tenth of a percent, so the surface must not be built around a large visible jump between the preview and the authoritative number.

### M6. The attribute schema and typed values

- **Requirement:** a layer carries an ordered set of attribute fields. Each field has a **stable key** that is its identity and is never reused after removal, a **display label** that is presentation and is freely renameable, a **type** from the closed set (text, number, boolean, date and time, single-select, image, person), an optional **required** marker, and for a single-select its preset values. Three typed values carry a reference rather than a value: an **image** attribute carries a reference to an object in storage plus its metadata and never carries bytes across the capability or core boundary; a **person** attribute carries a user reference that must resolve inside the tenant; a **date and time** field declares whether it carries an instant with an offset or a date alone, and an ambiguous local string is rejected at the boundary rather than guessed. The per-layer attribute schema is **user data** and evolves freely by the user's hand (add, rename, remove, per C4); the operation and protocol schemas are **system contracts** and are additive by default (T9.1). Neither rule applies to the other: a user removing a column is not a breaking protocol change, and a protocol field is never removed because a user may remove a column. Removing a field removes it from the current projection and from new operations, and it does not rewrite the append-only log, so the values already recorded in a legal-weight feature's trail stay complete and inspectable.
- **Shape:** attribute field (key, label, type, required, preset values); image value (object reference, metadata); person value (user reference, tenant-scoped); date value (instant with offset, or date, declared per field).
- **Basis:** C2, C3, C4; I10 and AR5 (the trail is not rewritten); T9.1 (the system-contract rule this one is deliberately separated from); C13.
- **Provenance:** the types and the removable column closed in PRD Layer 1 (C2 to C4); the key-versus-label split, the reference-carrying types, and the user-schema-versus-system-schema separation settled this PRD round.
- **Acceptance:** renaming a field changes every label without breaking a filter, a style, a popup, or a component bound to it, because those bind to the key; removing a field on a legal-weight layer leaves the historical values inspectable in the trail; an image attribute never carries bytes across the capability or core boundary; a person attribute cannot reference a user outside the tenant; a date value with no declared offset on a field that requires one is rejected at the boundary, never stored as a guess.
- **Open / ADR:** the object-storage reference shape for images (and its interaction with the offline device, where the bytes may not be present) is an ADR and touches OQ-17.

### M7. The legal-weight marker as data

- **Requirement:** legal weight is a marker on the **layer** (foundation section 4), armed by the feature type's entry in the jurisdiction package (M16) or by the tenant marking the layer, and where the layer corresponds to a record in an external registry it additionally carries a **per-feature classification** with its derivation source, the observed registry status, and when that status was observed. The server is authoritative over the classification at flush and the client's classification is an optimistic preview, exactly like its conflict resolution. The classification the server applied is recorded with the applied operation, so a later audit can tell what the server considered legal-weight at the moment it resolved that operation.
- **The registry status is provenance and is never the key that arms the protection (settled v0.10).** Legal weight follows the **nature** of the feature; the registry's state of the moment is recorded, displayed, carried into exports and reports, and used to drive workflow warnings, and it never raises or lowers the protection. Three reasons, and they are the reason this is written as a rule rather than left to an implementer's judgement. A registry status is commonly assigned on submission, before any analysis, so gating on the "good" status protects the unexamined mass and says nothing about it. A record under challenge or pending correction is precisely when a boundary error is most expensive, so lowering protection by status inverts the risk exactly where the product exists to hold. And a protection that switches with an external, slowly-synchronised state opens a window in which the wrong edit passes unpreserved, which is the silent loss the whole product refuses. A status that changes is therefore a recorded observation, never a reclassification of what is already protected, and protection is never removed retroactively.
- **Shape:** layer legal-weight marker (on or off, set by default type or by the tenant); feature classification when derived (source, registry key, observed status, observed-at); applied operation (the classification in force when the server applied it).
- **Basis:** foundation section 4 (legal weight as a configurable per-layer attribute), T3.2; C7, C13; the registry grounding in `specs/data-and-tooling-references.md` section 1.2.
- **Provenance:** the per-layer marker closed in foundation v0.2; the dynamic per-feature classification noted in PRD T3.2 (v0.11); recording the classification in force with the applied operation settled this PRD round.
- **Acceptance:** a feature the server classifies legal-weight at flush is treated as legal-weight even when the offline client did not; a layer marked legal-weight arms preserve-not-discard for every feature in it with no per-feature flag required; the classification in force at application is inspectable later on the applied operation, so the trail can explain why an operation resolved the way it did.
- **Open / ADR:** the per-jurisdiction list of feature types that carry legal weight is the package's content (M16) and its Brazilian entries are OQ-8, owned by the environmental engineer; what remains genuinely open there is the list itself, since the criterion is now closed in foundation section 9. **Closed in v0.10 and no longer open:** a feature that becomes legal-weight after being born as a sketch keeps its prior history exactly as recorded, the change of classification is itself a dated attributed operation, and the reinforced protection applies from that instant forward, with no retroactive reclassification, because rewriting how past operations resolved would rewrite the trail M15 makes evidence.

---

### M8. The operation envelope

- **Requirement:** every operation travels inside one envelope that is self-describing enough for the server to route, deduplicate, order, and resolve it without inferring anything from context. The envelope is a **generated cross-language contract**, authored once and generated into the other languages the way the API types are generated from the OpenAPI schema (M12); it is never hand-written twice. The client fills the client half at creation; the server adds the server half at application and never rewrites what the client sent, so a divergence stays inspectable (T5.1).
- **Shape:** client half (operation identifier per M3, clientID per M4, per-client mutation number, operation type, operation-schema version, conflict-rule version, target address, payload, author session material, created-at as the client's untrusted claim, and mediation provenance when the operation is agent-originated per T8.2); server half (applied-at as the authoritative stamp, the resulting per-feature version, **the per-project version the flush allocated to this operation**, the rule version actually applied, the legal-weight classification in force at application per M7, and the resolution verdict).
- **Basis:** I8, I9, I10, I11, foundation section 9.6.7; T9.2, T2.3, T5.1, T5.3, T8.2; C10, C12, C13, C14.
- **Provenance:** the versioning principle closed in foundation v0.11; the envelope as the concrete generated contract is the mechanism this PRD round settles (OQ-15), and it is the first of the four debts Layer 2 left to Layer 3. **The per-project version is envelope-borne, settled 2026-08-07** at the MAP-9 pickup, and this **reverses the count written here on 2026-08-05** rather than correcting an oversight: that round deliberately narrowed this acceptance to four so it would stop counting against a five-axis M10, which reconciled the arithmetic without asking where the fifth axis travels. It travels here. ADR-0004 distributes an allocated range across the operations of a flush, so each applied operation carries one, and a resync stream is a stream of applied operations. Leaving the ordering key out of the envelope would put it in a structure parallel to the contract that exists to make an operation self-describing, and a client would then advance its resync cursor by assumption, which is the shape C12 already forbids on the mutation-number axis for the same reason. An in-place dated sharpening, no version bump; the next PRD round absorbs it.
- **Acceptance:** an operation carries its type and operation-schema version, and the five version axes (M10) are present and distinct in the envelope; the server half is added without altering the client half, and an operation whose claimed author diverges from its session material keeps both the claim and the normalized identity (T5.1); the envelope has exactly one definition in the repository and every language reads a generated form of it.
- **Open / ADR:** the wire encoding of the envelope and the batching format of a flush are an ADR; the session-material shape inside it is OQ-18.

### M9. The operation catalog and the granularity rule

- **Requirement:** operations are a **closed named catalog**, and every operation **addresses exactly one target path** (tenant, project, layer, feature, property). This is the rule that makes conflict resolution by granularity (T3.1) implementable rather than aspirational: the conflict unit **is** the target path, so an operation that spans two properties of one feature, or two features, would make the granularity ladder undecidable. An operation type outside the catalog is rejected, never applied speculatively. Two consequences follow and are part of the requirement. First, a **geometry operation carries the whole geometry**, not a vertex delta, because the conflict unit is the geometry property and preserve-not-discard requires both whole geometries to be presentable side by side (T3.3); a vertex-level delta would make the losing version unreconstructable. Second, the **named exceptions are multi-target by design and are server-side and online only**: the shared-topology arc edit (D6), whose conflict unit is the arc and which is atomic across the faces referencing it, and the transactional flush itself, which is a batch of single-target operations rather than a multi-target operation.
- **Shape:** operation catalog by family (feature create and delete, feature geometry set, feature attribute set for one key, layer create and delete and rename, layer style set, layer schema field add and rename and remove, group operations, version snapshot create and restore, comment operations), each with its target path and payload; the exhaustive enumeration lives in the generated contract (M8, M12) and is not transcribed here, because a list transcribed in prose drifts from the contract.
- **Basis:** foundation section 4 (resolution by granularity, no sub-geometric merge), foundation section 8 and OQ-1 (topology online only); T3.1, T3.3, D6; C2, C7.
- **Provenance:** the granularity ladder closed in foundation v0.2; the single-target addressing rule, the whole-geometry payload, and the named multi-target exceptions were settled in v0.9 as the mechanism that carries them. **The typed, flag-and-retain refusal of a geometry outside its layer's declared family is settled in v0.15**, with M2, and it is the half of that rule which decides whether it protects field work or destroys it. **The wire refusal of a type-to-target-kind mismatch is settled 2026-08-06**, closing the MAP-8 Window A review, because the metadata-only reading left the granularity enforceable by convention alone and the review showed a green suite shipping the defect.
- **Acceptance:** no operation in the catalog targets more than one property of one feature, except the named exceptions, and a test enumerates the catalog and asserts it; two operations on different properties of one feature resolve with no conflict, driven by the target path alone; a geometry conflict presents two whole geometries and produces no third geometry (T3.3); an unknown operation type is rejected with a typed error rather than ignored; a catalog operation addressed at a target kind other than the one its type declares is refused with a typed error, never read at a coarser or finer granularity than the catalog fixes (settled 2026-08-06, closing the MAP-8 test review); and a geometry operation carrying a geometry outside its layer's declared family is refused with a typed error and the operation is **flagged and retained for inspection**, never discarded, on the same shape T5.2 fixes for the operation whose author lost authorization, because that geometry was drawn offline in the field and a refusal that drops it is the preserve-not-discard sin wearing a validation costume (C7, C13).

### M10. The five version axes and the ordering rule

- **Requirement:** **five** version axes exist, they never substitute for one another, and each has one owner that may increment it. The fifth, the **resync cursor**, is the **per-project version**: server-assigned, monotonic per project, allocated inside the flush transaction under the project lock, and presented by a client to ask for everything that changed since it last looked. It is distinct from the per-feature version, which orders and detects conflict on one feature, and it is what makes version order equal commit order by construction, which is the whole reason the sequence trap does not reach it (ADR-0004). The **per-feature version** is server-assigned and monotonic per feature, and it orders operations and detects conflict. The **per-client mutation number** is client-assigned, monotonic and contiguous **per clientID within one flush domain, which is one tenant and one project** (settled 2026-08-11 at the MAP-12 pickup, replacing a bare "contiguous per clientID"), and it gives idempotency and dedup. The **operation-schema version** is build-time and per operation type, and it drives upcasting (T9.3). The **conflict-rule version** is build-time and per runtime, and it detects temporal skew (T4.3). On top of them one ordering rule closes the last silent-loss hole in the flush path: the server applies a client's operations **only in contiguous mutation-number order**, so an operation at or below the cursor is deduplicated and ignored, and a **gap above the cursor is a typed error that asks the client to resend from the cursor, never a silent skip**, because the client's queue is persistent and append-only and a gap means an operation was lost rather than never created. **That reason is what fixes the domain, and it was read against a second destination for the first time on 2026-08-11.** A gap means loss only while the stream has **one** destination. A flush addresses exactly one tenant and exactly one project (ADR-0010 decision 6 with its addition of 2026-08-10), so a single stream spanning destinations presents the server with holes it **cannot tell apart from loss**: the operation may have gone to another project or another tenant, and no evidence available on this side distinguishes the two. The client therefore mints one contiguous stream **per clientID, tenant and project**, the server's cursor is keyed the same way (M4), and the guarantee is exact rather than best effort. **The alternative was refused with its reason:** widening the flush to a whole tenant would let one batch span projects, and a batch spanning projects cannot allocate its range in one statement, which is ADR-0004's RANGE rule and the measurement behind it.
- **Shape:** per-project version (integer, server-owned, the resync cursor, carried on the envelope's server half per M8 as settled 2026-08-07); per-feature version (integer, server-owned); mutation number (integer, client-owned, contiguous); operation-schema version and conflict-rule version (build-time identifiers carried in the envelope). Every axis is a **distinct type rather than a distinct field name**, so the substitution the acceptance forbids is refused by the compiler and the type checker rather than by a reviewer's attention (settled 2026-08-07 at the MAP-9 pickup, on the MAP-8 precedent that refused a convention-only reading of the same kind of clause). Two runtimes carry that structurally and the third does not: `specs/dependencies.md` section 2 holds the measurement and names TypeScript as the recorded gap. **The mutation number's first value is zero, settled 2026-08-11 at the MAP-12 pickup**, which is what the generated envelope already permits (an unsigned integer with no floor above zero), so nothing in `libs/core` changes in order to say it and the freshness gate is not disturbed. What it costs is that zero cannot serve as a sentinel, which is why M4 represents an absent cursor by the absence of its row.
- **Basis:** I2, I8, I9, foundation sections 4, 9.6.6, 9.6.7, 10; T2.1, T2.3, T4.3, T9.2.
- **Provenance:** the per-feature version and the mutation number closed in foundation v0.2 and v0.7 and refined in v0.8; the rule and schema versions closed in v0.6 and v0.11; the contiguity-and-gap rule is settled this PRD round.
- **Acceptance:** the five axes are distinct fields and no code path reads one as another; a resent flush is deduplicated by mutation number with no duplicate and no loss (T2.3); a flush with a gap above the cursor returns a typed resend-from-cursor response and applies nothing from the gap onward; a per-feature version never decreases.
- **Open / ADR: CLOSED in v0.11, and this requirement is complete.** Through v0.10 this requirement described four of the axes the system needs rather than all of them, because the resync cursor was undecided and sits exactly where the PostgreSQL ordering trap lives. The **SP-1 spike** ran and **ADR-0004** ratifies the answer: the cursor is a fifth axis of its own, the per-project version, rather than an existing axis doing double duty. Two mechanism rules come with it and are the ADR's, binding here: a flush allocates its whole range in **one** statement rather than one per operation, and the allocation is the **last** thing before commit so that validation, dedup, contiguity, feature versions and the conflict rule all run outside the critical section. The batch bound of N10 is the declared knob between flush speed and interactive latency.

### M11. What crosses the serializable boundary

- **Requirement:** the boundary between the UI and the shared core, and the boundary of the capability layer, carry **serializable data only and never a live reference** (no map object, no database handle, no callback into a live object), which is the one property that keeps the core portable across WASM and FFI and keeps a future sandbox possible (C11, T7.1). Three shaping rules follow. **One declared geometry encoding** crosses the boundary, the same one for WASM and for FFI, so a platform never gets its own dialect. **Identifiers and deltas by default**, with whole geometry crossing only where the consumer must render or edit it, because the boundary crossing is the known bottleneck of this architecture (foundation 9.6.2). **Bytes never cross**: an image or a raster is a reference (M6), and the payload that would carry pixels is fetched by the platform layer, not marshalled through the core.
- **Shape:** boundary message (operation identifier or target address, typed payload, no handles); geometry payload (one declared encoding); asset payload (reference plus metadata, never bytes).
- **Basis:** foundation sections 9.5 and 9.6.4; C11; T7.1, T7.2.
- **Provenance:** the principle closed in foundation v0.3 and v0.4; the three shaping rules are settled this PRD round.
- **Acceptance:** the core compiles to WASM and to a native FFI library from one source and both consume the identical message contract; no UI object or live handle appears in any boundary signature, asserted by a test over the generated contract; a continuous vertex drag does not cross the boundary once per vertex, asserted by a counted-crossings test against the T3.6 budget; an image attribute crosses as a reference and never as bytes.
- **Open / ADR:** the concrete geometry encoding (a compact binary such as WKB against a GeoJSON-shaped structure) is an ADR, with one constraint recorded: MapLibre consumes GeoJSON at the very edge, so that conversion belongs to the UI adapter and never to the core contract, or the renderer's format leaks into the portable layer.

### M12. Generated contracts and end-to-end type safety

- **Requirement:** every contract that crosses a language boundary is **authored once and generated**, never hand-written twice, in two directions with two sources of truth: the server contract is generated from the API's OpenAPI schema (Python and Pydantic being its source) into TypeScript and Dart, and the core contract is generated from the Rust types (M8, M11) into TypeScript and Dart. CI regenerates and fails on any difference, so a stale generated file is a red build rather than a silent drift. Type checking blocks the build on every side (mypy strict with django-stubs, TypeScript strict, the Rust and Dart equivalents), and no boundary value is untyped. **One duplication is deliberate and is not a generation failure:** the conflict-resolution rule exists in the Rust core and in the Python server on purpose (T4.1), guarded by golden tests rather than by generation, because generating it would put the Rust core on the server and reopen a decision the foundation closed (foundation 9.6.6). Nobody should "fix" that duplication by generating it.
- **Basis:** I5, I8, foundation sections 9.6.2, 9.6.6, 10; C5, C10; T4.1.
- **Provenance:** type safety and generated contracts closed in foundation v0.1 and foundation section 10; the two-generator shape and the deliberate-duplication carve-out are settled this PRD round.
- **Acceptance:** changing a Rust type or an API schema without regenerating fails CI; a hand-written declaration of a generated type is rejected; CI blocks on any type-check violation on any of the four languages; the conflict rule remains two implementations under golden tests and no generator emits it.

### M13. The conflict-rule contract and its tolerance

- **Requirement:** the conflict rule is a **pure function over a declared contract**, so it can be golden-tested identically in two runtimes (T4.1): its input is the target path, the authoritative state of that target with its per-feature version, the incoming operation, and the concurrent state or operation; its output is a verdict from a closed set (apply, last-writer-wins with the named winner, flag and preserve both). The golden corpus is a set of data files in that contract, run against both runtimes in CI. Where the rule consults a **geometric predicate** (whether two geometries are materially the same), the comparison is evaluated against a **tolerance declared in metres**, never in degrees, because a degree tolerance changes meaning with latitude and would make the rule behave differently in the north and the south of the country. The safety rule that governs the tolerance band is the moral line applied to floating point: **where the two runtimes could disagree because the difference sits inside the tolerance band, the verdict for a legal-weight feature falls to the preserving side**, flag and preserve, never to the discarding side. A doubt resolves toward keeping both versions.
- **Shape:** rule input (target path, authoritative state and version, incoming operation, concurrent state or operation, legal-weight classification in force); rule output (verdict, winner where applicable, both versions retained where applicable); tolerance (a distance in metres, declared and versioned with the rule).
- **Basis:** I8, foundation sections 4 and 9.6.6; T4.1, T4.2, T3.2; C7, C10.
- **Provenance:** the golden-tested equivalence closed in foundation v0.6, which already flagged that the golden test is not trivial where the rule consults a geometric predicate; the metre-denominated tolerance and the fall-to-preserving rule are settled this PRD round, and this is the second of the four debts Layer 2 left to Layer 3.
- **Acceptance:** the golden corpus resolves identically within tolerance on both runtimes and a deliberate divergence fails the build; a legal-weight case constructed to sit inside the tolerance band resolves to flag-and-preserve on both runtimes rather than to either discarding verdict; the tolerance is expressed in metres and changing it changes the corpus outcome in a declared, tested way.

### M14. The editable working set representation

- **Requirement:** only the promoted working set crosses into the client-side editable source, and it crosses under three rules. Each editable feature carries its **stable identifier (M3) as the identifier in the edit source**, so a diff-based update path stays open and the editing adapter is not forced to replace the whole source on every change (the ADR that can raise the T3.6 cap depends on this). The edit source holds geometry in whatever frame the renderer requires, and **the storage frame is untouched**: a feature promoted and released without editing returns identical in storage, coordinate for coordinate (M5 rule 3). The working set is bounded by the measured budget (T3.6, M2), a whole-layer promotion is refused with explicit feedback, and releasing a feature returns it to the rendered and tiled path.
- **Shape:** edit source entry (stable feature identifier, geometry in the render frame, the minimum attributes the editing surface needs); working-set membership (which features are promoted, and the budget in force).
- **Basis:** foundation sections 7 and 8 (the MapLibre editing restriction and the capped working set); T3.6, M2, M5; I6 as a separate budget.
- **Provenance:** the editing restriction closed in foundation v0.2 and the cap framed as a measured budget in v0.11; the representation rules are settled this PRD round, the third of the four debts Layer 2 left to Layer 3.
- **Acceptance:** promoting and releasing a feature without editing leaves storage identical coordinate for coordinate; every feature in the edit source is addressable by its stable identifier; a whole-layer promotion is refused with explicit feedback rather than silently truncated to the budget; the budgets of T3.6 hold on the named reference device.

### M15. The append-only operation log and its projections

- **Requirement:** the operation log is **append-only**. An operation is never mutated in place and never rewritten; a correction is a new operation. The current state that the application reads is a **projection of that log**, and for a **legal-weight feature the projection is reproducible**: replaying its ordered chain of attributed operations in server order reproduces the current authoritative geometry. That reproducibility is the testable form of the foundation's rule that a legal-weight feature's authorship **is** the chain rather than a stamp (I10, T5.3), and it is what makes the chain evidence rather than decoration. The log carries what the other requirements put in it: the authorship and the two times (T5.3), the legal-weight classification in force at application (M7), and the mediation provenance of an agent-originated write (T8.2). Deleting a user does not remove the operations they authored on a legal-weight feature (T3.5).
- **Shape:** log entry (the M8 envelope as applied, immutable); projection (current features and layers, derived); legal-weight chain (the ordered attributed subset for one feature).
- **Basis:** I10, foundation sections 4 and 9 (the append-only operation log the sync already produces); T3.5, T5.3, T8.2; C7, C13, AR5.
- **Provenance:** the chain closed in foundation v0.8; the append-only-and-reproducible-projection rule is settled this PRD round. **The enforcement of append-only is sharpened 2026-08-07** at the MAP-10 pickup, from a property a test watches to a property the database holds: an in-place rewrite is refused by privilege, not by convention. An in-place dated sharpening, no version bump; the next PRD round absorbs it.
- **Acceptance:** replaying a legal-weight feature's attributed chain in server order reproduces its current authoritative geometry exactly; **the runtime role holds `SELECT, INSERT` and no `UPDATE, DELETE, TRUNCATE` on the log, so an in-place rewrite is refused by the database on the runtime path rather than avoided by the code paths somebody covered (ADR-0005 section 2, addition of 2026-08-07, whose correction of the same date records that the owner profile is outside this guarantee and why extending it is a separate decision), and the test asserts that refusal while distinguishing it from a statement that matched no rows**; deleting a user leaves their operations on a legal-weight feature inspectable with the minimum identification retained; an agent-originated operation is distinguishable in the log from a direct human write by the same user.
- **Open / ADR:** retention, archival, and whether a legal-weight project can be physically deleted at all are OQ-20; the projection's materialization strategy (a maintained current-state table against replay on read) is an ADR, bounded by the reproducibility requirement above.

### M16. The jurisdiction package

- **Requirement:** every rule that comes from a regime is **data in a versioned, dated jurisdiction package**, and no engine carries a regulatory value of its own (foundation section 9, closed v0.13). A package declares its jurisdiction, its version, the date each entry was verified, and the authority each entry cites, so a figure the product produces can be traced to the rule that produced it and to the source of that rule. Four kinds of content live in a package and nothing else does. **Legal-weight feature types:** which layer types the package marks legal-weight, each with the authority that makes it so, applied through the jurisdiction-neutral criterion the foundation fixes. **Regulatory geometry parameters:** a width, a threshold, or a band that a rule fixes in law, carried with the conditions that select it (the buffer width that depends on the width of the watercourse is the anchor case, and it is a table with its selecting conditions rather than a constant). **Deliverable and attestation templates:** what a work product must contain and how a professional attests to it, which differs by regime and is never a fixed schema field (J2). **Retention policy:** the period and the disposal rule per data class, which foundation OQ-20 makes per-jurisdiction. The **metric frames of M5 are the first instance of this rule and are not restated here**; a frame bound to a purpose in a jurisdiction is a package entry like any other. A regulatory value appearing as a literal in a function is a defect, the same way a raw colour in a component is a defect under U1.
- **Shape:** package (jurisdiction, version, effective-from, entries); entry (kind, key, value or table, selecting conditions, cited authority, verified-at); project binding (which package version a project resolves against, recorded with the project so a later reading reproduces the same rule).
- **Basis:** foundation section 9 (regulatory content is per-jurisdiction data, closed v0.13), foundation sections 1.3 and 12 (not capped to one national market); M5, M7, J2; OQ-8, OQ-16, OQ-20.
- **Provenance:** the shape was practised by M5 in v0.9 for the metric frame alone; generalized into a foundation decision and into this requirement in v0.10, after a compliance research round showed the same shape was needed for legal-weight marking, regulatory geometry, deliverables, and retention.
- **Acceptance:** a project resolves its rules against a named package version recorded with the project, and re-reading an old project reproduces the rule that was in force rather than today's; adding a second jurisdiction adds a package and edits no engine, proven by a test that runs the same capability under two packages and gets two correct and different answers; a regulatory literal in engine code fails review; every package entry carries its cited authority and its verification date, and an entry with neither fails review; changing a package version changes the figures a project produces in a declared and tested way, with the old figures still explicable from the old version.
- **Open / ADR:** the Brazilian package's content is the open work and it splits by owner, with the legal-weight list at OQ-8 (the engineer), the retention policy at OQ-16 and OQ-20 (legal review), and the regulatory geometry table pending the verbatim primary-source reading recorded in `specs/domain-questions.md` section V.3; the packaging mechanism (how a package is distributed, versioned, and pinned to a project) is an ADR.

### 6.9 Open questions touched by Layer 3

Foundation OQs and PRD-level open choices that Layer 3 marks rather than closes, gathered so the model layer's dependencies are visible in one place (mirroring foundation section 4 and subsection 5.9).

- **OQ-6 (promoted-element lifecycle):** M2 makes copying a promoted result into an element layer the natural shape, since the storage class is what decides the path, and it does not close the question.
- **OQ-8 (legal-weight classification):** M7 carries the marker, the derived per-feature classification, and the record of the classification in force at application; the rule itself stays the engineer's.
- **OQ-15 (operation and schema versioning mechanism):** M8 and M10 settle the envelope and the axes; the compatibility-window length and the handshake question stay open from T9.4.
- **OQ-18 (offline authorship proof):** M8 carries the session material as a field and does not decide its mechanism.
- **OQ-20 (legal-weight retention and project deletion):** M15 makes the log append-only and the legal-weight projection reproducible, which sharpens the question rather than answering it: physical deletion erases exactly the evidence M15 requires.
- **OQ-1 (shared topology):** M9 names the topological arc edit as a multi-target, server-side, online-only exception to the single-target rule; its full shape is still OQ-1.
- **The metric frame beyond Brazil (PRD-level):** M5 fixes the frame-by-purpose rule and the three frames the anchor domain needs. Adding a frame for another jurisdiction is configuration under the same rule, and the frames themselves are pinned per jurisdiction when a jurisdiction is served.
- **The Manual Tecnico de Posicionamento (PRD task):** the SGL conversion and its origin must be read from INCRA's manual before the SGL frame is implemented (M5).
- **Measurement tasks (PRD):** the element budget (M2), the editable working-set budgets and the named reference device (T3.6, M14), and the cursor retention window bound to the maximum supported offline window (M4) are all set by measurement, not assumed.

---

> End of Layer 3 (M1 to M16) and its open questions. Layer 4 (surfaces and platform, including the Field App) follows below, and after it the non-functional block (performance and the I6 budget, security and sandboxing, privacy and LGPD, accessibility, internationalization, observability, reliability, device support) and the design-system section. The file may be split per layer once the material is complete.

---

## 7. Layer 4: Surfaces and platform

> **Scope.** Layer 4 says what each surface delivers and what differs between them: the web app, the desktop app (Tauri), and the mobile app (Flutter, tablet-first for the field). It does not restate a capability that Layer 1 already fixed and it does not design a screen, which is the design-system section's job. It fixes the surface matrix, the per-surface offline domain, what the field surface adds and what it must refuse, the interaction floor, the update path that makes the versioning force-upgrade real, and the properties that are never allowed to differ by surface.
>
> **IDs.** Layer 4 requirements are numbered S1 to Sn (surface).
>
> **The rule the whole layer serves:** the UI is rewritten per platform and the logic core is not (foundation 9.6.4, C11), so a surface is a presentation of the same capabilities rather than a different product. Every difference between surfaces is therefore a **declared** difference with a reason, and an undeclared one is a defect.

### S1. The surface matrix and the parity rule

- **Requirement:** the three surfaces are the **web app** (Angular, core as WASM), the **desktop app** (Tauri shell of the same Angular UI, core as WASM), and the **mobile app** (Flutter, core as a native FFI library, tablet-first for field work). **Capability parity is the default:** every Layer 1 capability is available on every surface unless this layer declares an exception, and every exception names a reason from a closed set: it needs the server and the surface is in a state that has no server; it needs hardware the surface does not have; it needs an input modality the surface does not have; or it is gated behind a named open question. Convenience, effort, and delivery order are not reasons, because delivery order is roadmap and roadmap is out of scope (foundation section 0). A capability with no declared exception is available everywhere, and a difference a user meets that this layer did not declare is a defect rather than a platform quirk.
- **Basis:** foundation 9.6.1, 9.6.2, 9.6.3, 9.6.4; C11; PRD Layer 1 as the capability set.
- **Provenance:** the multi-platform target closed in foundation v0.4; the parity-by-default rule with a closed reason set is settled this PRD round.
- **Acceptance:** a capability-by-surface matrix exists and covers every Layer 1 capability; every cell that is not "available" carries one of the four reasons; a capability absent on a surface with no declared reason fails review.

### S2. The web surface

- **Requirement:** the web app carries the whole native floor with no install. Its offline is **session-scoped** (foundation section 5): what the session loaded stays editable and the browser never held the whole project, with the operation queue and the working copy in the single client store behind the storage interface (T1.2). The surface states its offline scope rather than implying more, so a user never discovers the limit by losing work.
- **Basis:** foundation section 5, foundation section 9.6.2; T1.1, T1.2; I1.
- **Provenance:** session-scoped web offline closed in foundation v0.1 and refined in v0.2.
- **Acceptance:** every Layer 1 capability is reachable on the web surface subject to the S1 matrix; offline the surface keeps working within the session scope, tells the user what is unavailable and why, and never silently degrades; the store choice is invisible above the storage interface.
- **Open / ADR:** IndexedDB against OPFS is the ADR behind that interface (T1.1).

### S3. The desktop surface

- **Requirement:** the desktop app is the same Angular UI and the same WASM core inside a Tauri shell, so it inherits the web surface's capabilities rather than reimplementing them. What it adds is operating-system integration (native file open and save for import and export, local paths, and the file associations a desktop tool is expected to have). **Until the project-scoped offline mode is designed (OQ-9), desktop offline is the same session-scoped mode as web**, and the surface must not imply otherwise anywhere in its wording, its settings, or its behaviour, because a desktop GIS user arrives expecting the whole project offline and an implied promise here is a promise of lost work.
- **Basis:** foundation sections 5 and 9.6.1; OQ-9; T1.1, T1.2.
- **Provenance:** desktop as a Tauri shell closed in foundation v0.4; the no-implied-offline constraint is settled this PRD round.
- **Acceptance:** a capability available on web is available on desktop unless the S1 matrix says otherwise; desktop offline behaves exactly as session-scoped and says so; no desktop affordance suggests whole-project offline before OQ-9 lands.
- **Open / ADR:** the project-scoped offline mode, its local store, and its relation to the storage interface are OQ-9, and the SQLite adapter, if built, sits behind the same interface with no second sync surface (T1.2).

### S4. The field surface (mobile, tablet-first)

- **Requirement:** the mobile app is the **field surface**: capture, verification, and correction in place, on a tablet, frequently with no network. It carries the capabilities the field work needs, each already fixed in Layer 1 and not redefined here: authenticate and hold a session across a trip (A1), view the map and layers as tiles (B1, B4), draw and edit features offline (D1, D2), create and edit complex geometry (D3), fill a survey with required fields and preset dropdowns (C3), attach photos to a feature (C2), inspect features and read the attribute table (E1, E2), measure (G1), comment and see presence when online (H1, H2), and resolve or defer a flagged conflict (H3). It adds two things no other surface has, and both are hardware: **the device position**, so a vertex can be captured at where the person is standing rather than digitized against imagery, and **the camera**, so a photo is attached and geotagged at capture. Heavy work stays where it already is by architecture rather than by surface policy: analysis and imagery are server-side and online (foundation section 5), and the agent is online-only (T8.1).
- **Basis:** foundation 9.6.1 and 9.6.3 (mobile as a first-class target, Flutter, tablet-first), foundation section 5; Layer 1 A1, B1, B4, C2, C3, D1, D2, D3, E1, E2, G1, H1, H2, H3; T1, T8.1.
- **Provenance:** the mobile target and Flutter closed in foundation v0.4; the field surface's capability set is assembled here from Layer 1 this PRD round.
- **Acceptance:** a field crew with no network draws, edits, fills a required survey, attaches photos, and measures, and all of it survives an app restart and flushes on reconnect (T1); a vertex is capturable from the device position; a photo attaches to a feature with its capture position; the capabilities that need the server are refused with explicit feedback rather than failing silently.

### S5. Capture provenance and the precision floor for legal-weight geometry

- **Requirement:** every captured vertex records **how it was captured** (digitized against imagery, device positioning, external receiver, or imported) and **the precision estimate of that capture**, and the record travels with the geometry the way a metric travels with its frame (M5). On top of that, a hard refusal: **a geometry whose vertices do not meet the positional accuracy the applicable regime requires is never presented as satisfying that regime.** For the certified rural parcel the norm settles it: **MTGIR 2nd edition item 1.4.4** requires positional precision better than or equal to 0,50 m on artificial limits, 3,00 m on natural limits, and 7,50 m on inaccessible limits, and a consumer tablet's built-in positioning does not reach the first of those. The same item sets a **tolerance of at most three times that value** between the certified coordinates and the value another credentialed surveyor obtains for the same vertex, which is the norm's own bar for when two measurements of one corner disagree. The surface may still capture it, because a sketch, a check, and a field note are legitimate work; what it must not do is let that geometry be labelled, exported, or reported as certification-grade. The system states what a capture is good for instead of leaving the professional to assume.
- **Basis:** MTGIR 2nd edition items 1.4.4 and 1.4.6 (via M5 and `specs/data-and-tooling-references.md` section 1.2); C7 and the preserve-not-discard moral line applied to precision; AR2 (no estimate where exact is expected); M5, M7, M16.
- **Provenance:** settled in PRD v0.9 on the norm as then cited; the citation corrected to the live standard in v0.10 after verification found the prior one revoked (`specs/domain-questions.md` section V.1). The requirement itself did not change, which is the point of recording the correction rather than silently editing it.
- **Acceptance:** a vertex carries its capture method and precision estimate through storage, export, and the trail; a geometry captured by device positioning is not presentable as meeting the artificial-limit accuracy, and the refusal is explicit rather than a silent downgrade; a mixed-capture geometry reports the worst precision among its vertices, not the best.
- **Open / ADR:** support for an external GNSS or RTK receiver is the path that makes field capture reach the certification floor, and its integration (protocol, pairing, how the precision estimate is read from the receiver) is an ADR; whether Mapsift ships that support natively or as an official extension is a packaging call under the movable native-versus-extension boundary (foundation 9.5).

### S6. The offline domain per surface

- **Requirement:** the offline domain is declared per surface and the surface tells the user its edges. Web and desktop are session-scoped until OQ-9 (S2, S3). The field surface is the one that must survive the longest disconnection, so its offline scope is what the trip loaded, and the loading act is explicit: the user prepares the work before leaving signal rather than discovering in the field that a layer was never cached. On every surface the rule is the foundation's: what is loaded keeps working, what needs the server is blocked **with clear feedback**, and the agent is unavailable while the rest of the client keeps working (T8.1). No surface silently degrades a capability into a worse one; it is either available, or refused and said.
- **Basis:** foundation section 5; T1.1, T8.1; I1.
- **Provenance:** the two-dimension offline model closed in foundation v0.1 and v0.2; the per-surface declaration and the explicit preparation act are settled this PRD round.
- **Acceptance:** each surface declares its offline domain and honours it; an unavailable capability is refused with a reason naming what is missing; a field trip prepared with a set of layers has exactly those available offline, and a layer that was not prepared is absent rather than blank; the offline queue survives a restart on every surface (T1.2).
- **Open / ADR:** what "prepared" means concretely for tiles and layers on the field surface (the region and zoom range downloaded, the storage ceiling, the eviction rule) is an ADR bounded by the I6 budget and by the on-device protection question OQ-17.

### S7. Interaction floor per surface

- **Requirement:** each surface is fully usable with its own primary input. On the field surface every capability is reachable **by touch alone**, with hit targets and vertex handles sized for a finger under field conditions, so no capability hides behind a keyboard the tablet does not have. On web and desktop the pointer is primary and keyboard shortcuts accelerate but never gate: a capability reachable only by a shortcut is a capability the beginner cannot find, which contradicts the foundation's depth-hidden-until-needed rule (foundation 0.5) rather than serving it.
- **Basis:** foundation 0.5 (professional yet simple, the common path obvious); Layer 1 K1, K2.
- **Provenance:** settled this PRD round.
- **Acceptance:** every capability on the field surface is reachable by touch with no external keyboard; no capability on any surface is reachable only by a keyboard shortcut; vertex editing is operable by touch on the reference field tablet.

### S8. Layout and experience level per surface

- **Requirement:** the configurable layout and the experience level (K1, K2) exist per surface with defaults appropriate to that surface: a reshapeable cockpit on web and desktop, a field-appropriate default on the tablet where the map is the screen and the panels are transient. A **saved layout belongs to a surface family** and is not applied blindly across families, because a layout tuned for a wide monitor is not a layout for a tablet held in one hand.
- **Basis:** Layer 1 K1, K2; foundation 0.5.
- **Provenance:** the layout family closed in PRD Layer 1; the per-surface scoping is settled this PRD round.
- **Acceptance:** each surface opens in its own sensible default; a user's saved layouts are offered within the surface family that produced them and are not force-applied across families; the experience level persists per user across sessions and surfaces.
- **Open / ADR:** the concrete preset layouts and the panel inventory are the design-system section's, refined with the engineer and real use, and they are not decided here.

### S9. Distribution and the force-upgrade path

- **Requirement:** each surface declares how it updates, and each is capable of presenting a **blocking upgrade state**, because the versioning mechanism depends on it: T9.4 requires a typed force-upgrade in both directions, and a force-upgrade with nowhere to land is a dead end rather than a protection. The mobile surface is the hard case the whole rule exists for, since store review and a user who never updates keep an old core alive for months (foundation 9.6.6, the temporal skew). The web surface must not serve a stale client indefinitely: assets are versioned so a reload lands on the current build. On every surface, a client below the minimum supported version stops and asks to be upgraded, and it **never renders correctness-relevant state it cannot interpret**, which for a legal-weight feature means surfacing it as needing an upgrade rather than omitting it or showing it wrong (T9.4, foundation 9.6.7).
- **Basis:** foundation 9.6.6 and 9.6.7; T9.4, T4.3; C7, C10.
- **Provenance:** the bidirectional versioning principle closed in foundation v0.11 and its mechanism in PRD T9 and M10; the surface obligation is settled this PRD round.
- **Acceptance:** a client below the minimum supported version shows a blocking upgrade state with the upgrade path for its surface; a too-old client pulling new-schema legal-weight state force-upgrades before rendering and never omits the feature silently; a web client reloading after a deploy lands on the current build rather than a cached stale one.
- **Open / ADR:** the compatibility-window length is OQ-15; the store-release cadence and whether the desktop shell self-updates are an ADR.

### S10. What never differs by surface

- **Requirement:** the invariants are not surface-configurable. No surface has weaker tenant isolation (I4), a different conflict rule or a privileged resolution path (I8, and resolution authority stays the server's on every surface), weaker authorship and authorization (I10), a weaker agent gate (I11), or a shortcut around the capability layer (T7). A surface never gets a private path into the data, and the same golden vectors and the same C-tests apply to every surface's build of the core.
- **Basis:** I2, I4, I8, I9, I10, I11; C4, C7, C10, C11, C12, C13, C14; T4, T5, T7, T8.
- **Provenance:** the invariants are the foundation's; their non-negotiability by surface is stated here so a platform port cannot quietly relax one.
- **Acceptance:** the conflict-rule golden vectors run against the WASM build and the FFI build and resolve identically within tolerance (M13); no surface reaches data except through the capability layer; a capability behaves identically on every surface except where the S1 matrix declares a difference with a reason.

### 7.9 Open questions touched by Layer 4

- **OQ-9 (desktop project-scoped offline):** S3, and until it lands desktop offline is session-scoped and must not imply more.
- **OQ-17 (protection of the offline store on the device):** the field tablet is the exposure vector, and S4 and S6 put real legal-weight geometry and owner data on it; the per-platform protection stays open.
- **OQ-1 (shared topology):** propagation is online and server-side on every surface (D6), so no surface offers offline topological editing.
- **OQ-15 (versioning mechanism):** S9 depends on the compatibility window.
- **OQ-19 (agent-write governance):** the gate's shape reaches every surface that can trigger an agent action; the agent itself is online-only (T8.1).
- **External GNSS integration (ADR):** S5, the path that lets field capture reach the certification-grade accuracy floor.
- **Field preparation semantics (ADR):** S6, what a prepared trip downloads and how it is bounded.
- **The reference field tablet (PRD measurement task):** the same named device that sets the T3.6 budgets is the one S7 and S4 are validated on.

---

> End of Layer 4 (S1 to S10) and its open questions.

---

## 8. Non-functional requirements

> **Scope.** The properties the whole system must hold that are not a capability and not a surface: performance and its budgets, security and isolation, extension sandboxing, privacy and the device as an exposure vector, accessibility, internationalization, observability, reliability and resync, and the supported environments. Several of these sit on open questions the foundation deliberately left open (OQ-14, OQ-16, OQ-17); where that is the case this section states what is already binding and marks the open part rather than inventing an answer.
>
> **IDs.** N1 to Nn (non-functional).
>
> **The rule this block serves:** the foundation's fluidity goal is explicitly not decoration and not subjective (foundation 0.5), so it is written here as budgets with a measurement protocol. A performance requirement without its device, its versions, and its date is a number with no meaning.

### N1. The three performance budgets and the measurement protocol

- **Requirement:** three budgets exist, they are distinct, and conflating them is an error, because each guards a different path and each has a different trigger. **I6, the per-tile render budget:** the feature count per tile at which dynamic MVT from PostGIS stops being responsive; crossing it is the architectural gate to pre-generated tiles plus merge-on-demand (foundation section 6), and it belongs to the served path. **The editable working-set budget (T3.6, M14):** what the client-side editing source holds while a vertex drag stays responsive; it belongs to the element path. **The element budget (M2):** how large an import may be to land as an element layer rather than a served layer; it belongs to classification. Three budgets, three names, three triggers. On top of them, two interaction rules make all three testable rather than subjective, and they are the industry's standard definitions rather than invented ones: a main-thread task over **50 milliseconds** is a long task and blocks input, and an interaction whose response exceeds about **200 milliseconds** at the 75th percentile is perceived as lag (the Interaction to Next Paint threshold). Mapsift's rule is that during pan, zoom, and a continuous vertex drag there is **no long task and no interaction above the 200 millisecond threshold at the 75th percentile**, on the named reference devices. Every budget is recorded with the device, the operating system, the browser, the MapLibre version, the fixture used, and the date, because a budget without its conditions cannot be re-measured or falsified.
- **Basis:** I6, foundation sections 0.5, 6, 8; T3.6, M2, M14; the fixture corpus in `specs/data-and-tooling-references.md` Part 1.
- **Provenance:** I6 reframed as a measured per-tile budget in foundation v0.2; the three-budget separation and the interaction rules are settled this PRD round.
- **Acceptance:** each of the three budgets has a recorded value with device, versions, fixture, and date; pan, zoom, and a continuous vertex drag hold the no-long-task and 200 millisecond rules at the 75th percentile on the reference devices; crossing the I6 budget triggers the tiling-gate decision rather than a silent slowdown; the three budgets are named distinctly in code and in tests, so no test asserts one while claiming another.
- **Open / ADR:** the concrete values are set by measurement (a PRD task, listed in PRD section 10.5), not assumed here. **A budget is a floor and never a target (foundation section 10, closed v0.15):** meeting it is the bar below which the product is defective, and the standing obligation is to research the established technique and take the structural version of it, which is free at design time, rather than to stop at the first implementation that fits inside the budget.

### N2. Tenant isolation is a tested surface, not a convention

- **Requirement:** the isolation wall is proven by tests that run in CI, and its coverage is **by construction rather than by diligence**: a test enumerates every tenant-owned table and asserts that row-level security is both **enabled and forced**, so a table added later without the policy fails the build instead of quietly opening a hole. The known defeat conditions are explicit test cases rather than review notes: a role that owns the table and therefore bypasses a non-forced policy, a role holding the bypass privilege, and the tile role connecting privileged or failing to set the tenant on its session. A cross-tenant read through the tile path is a test, because that path is the one an ORM-level filter never covered (I4's scar).
- **Basis:** I4, foundation section 9; C4; T6.1, T6.5.
- **Provenance:** SQL-layer isolation closed in foundation v0.2 and rekeyed to the tenant in v0.11; the by-construction test coverage is settled this PRD round.
- **Acceptance:** a new tenant-owned table without row-level security enabled and forced fails CI; a tile request for another tenant's data returns nothing and is indistinguishable from a resource that never existed; a test proves the tile role cannot bypass the policy; every direct-to-PostGIS reader is covered by the same test; **no application role holds BYPASSRLS and no application role owns a tenant-owned table**, asserted from the catalogue rather than reviewed; a query with no tenant binding in force returns nothing **and** raises in the application, since the policy's silence is indistinguishable from an empty tenant; and **a write bound to one tenant cannot reach another tenant's row through a foreign key or discover it through a unique-key collision**, which is the channel referential-integrity checks leave open because they bypass the policy by design (ADR-0005).

### N3. Secrets, transport, and the production boundary

- **Requirement:** transport is TLS on every surface and every path, production data is encrypted at rest, and **no production credential or production data exists in any non-production environment** (I7), checked automatically rather than promised. Secrets never enter the repository and never enter a client bundle, and the built client bundle is scanned for them, because a secret shipped to the browser is public.
- **Basis:** I7, foundation section 9 (the security posture); C6.
- **Provenance:** the posture closed in foundation v0.7.
- **Acceptance:** an environment carrying a production secret or production data outside production fails its check; a client bundle containing a secret fails the build; a non-TLS path anywhere fails review.

### N4. Extension sandboxing and capability permissions (bounded by OQ-14)

- **Requirement:** what is **binding now** is the property that keeps the door open: the capability layer passes serializable data and never live references (T7.1, C11), which is precisely what makes a later sandbox a decision rather than a rewrite, and a community extension does not write legal-weight geometry without explicit per-action confirmation (foundation section 0.4). What is **open** is the execution model (a client worker with a message contract, a server-side isolated container with a network allowlist and a resource ceiling) and the consent model where a capability declares what it needs, both OQ-14. Until OQ-14 closes, **no third-party code executes inside Mapsift**, because shipping an extension path before its sandbox is decided is how a permission model gets retrofitted onto running code, which is exactly the retrofit foundation 9.5 exists to avoid.
- **Basis:** foundation 9.5, OQ-14; C11; T7.1, T7.2; foundation section 0.4.
- **Provenance:** the capability layer closed in foundation v0.3 with OQ-14 opened alongside it; the no-execution-before-the-model rule is settled this PRD round.
- **Acceptance:** no capability signature accepts or returns a live reference; no third-party execution path exists in the product while OQ-14 is open; a community extension attempting a legal-weight write is gated by explicit confirmation.

### N5. Privacy, multi-regime (bounded by OQ-16)

- **Requirement:** the technical posture is enforced now: collection is minimized to what environmental analysis needs, provenance of who edited what is retained, production data never leaves production, and data is encrypted in transit and at rest (N3). The **legal** posture is not asserted: the basis for processing, the retention and disposal policy, the data-subject rights, and whether a data protection officer is required are OQ-16, settled with qualified review, and **no compliance claim appears anywhere in the product, its interface, or its material while that question is open**, because a badge is a claim. One consequence is already settled and it constrains the rest: the change history of a legal-weight feature is immutable and survives deletion of the user who authored it, retaining the minimum identification needed for audit, on a retention obligation rather than consent (T3.5). A deletion request is therefore honoured everywhere except that trail, and **the exception is stated to the person** rather than applied silently, with T3.5's opaque-author mechanism being what keeps the exception as narrow as it can be.

  **The posture is designed against the strictest regime served, not against the local one (v0.10, foundation OQ-16 reframed in v0.13).** Writing it against one regime and adding the others when a foreign client appears is the retrofit this document avoids everywhere else. Two engineering consequences bind now, ahead of any legal answer. **Data residency is a deployment dimension per tenant**, so a tenant that must keep data in a territory can, which is a shape decided before the first migration rather than after a contract demands it. And **the position of a person is a different kind of data from the position of a parcel**, a distinction the product must carry rather than blur: a parcel vertex is the subject matter of the work, while the **continuous position trail of the field device is a person's whereabouts**, potentially an employee's, which several regimes treat as sensitive and one treats as employment data with its own rules. So the capture path retains the precision estimate and the capture method S5 requires and **does not retain a continuous device track beyond what the captured geometry needs**; a background trail is collected only where a user has asked for it and it carries its own retention entry (M16).
- **Basis:** foundation section 9 (privacy posture, and the per-jurisdiction data rule closed v0.13), OQ-16, OQ-20; T3.5, S5, M16; I10.
- **Provenance:** the technical posture closed in foundation v0.7; the trail-survives-deletion consequence settled in PRD T3.5; the no-claim-while-open rule is settled this PRD round.
- **Acceptance:** a deletion request removes personal data everywhere except the legal-weight trail, and the response states that exception explicitly; no surface or material asserts compliance while OQ-16 is open; an inventory exists naming what personal data is held, where, and why.

### N6. The device as an exposure vector (bounded by OQ-17)

- **Requirement:** the offline-first model puts the operation queue and real features on the device, and the field tablet is what gets lost, stolen, and left behind, so **no requirement anywhere may assume the device is trusted**. That assumption is already refused where it matters most: authorship is proved by session material and normalized server-side rather than believed from the client (T5.1), and resolution authority is the server's (T4.2). Two things bind now regardless of how OQ-17 resolves. The exposure is **documented per surface**, so nobody discovers it in an incident. And losing a device has a **server-side path**: revoking the credential prevents that installation from flushing and from renewing, and interactive re-auth is required. The honest limit is stated with it: server-side revocation does not protect data already at rest on the device, which is the whole reason OQ-17 exists and is open.
- **Basis:** foundation section 9 (the offline device as a distinct vector), OQ-17; T5.1, T5.2, T4.2; S4, S6.
- **Provenance:** OQ-17 opened in foundation v0.8; the trusted-device refusal and the revocation path are settled this PRD round.
- **Acceptance:** an exposure statement exists per surface; revoking a credential blocks that installation's flush and renewal and forces interactive re-auth; no requirement in this document depends on the device being trusted; the at-rest limit is stated rather than implied away.

### N7. Accessibility

- **Requirement:** the declared target is **WCAG 2.2 level AA**, the current W3C Recommendation (published October 2023, editorially updated December 2024, adopted as ISO/IEC 40500 in 2025), applied to the application chrome: keyboard operability, visible focus, contrast, correct names and roles, and no capability reachable only by pointer on web and desktop, which is the mirror of the touch rule S7 sets for the field surface. The map canvas is the honest hard case and is treated honestly: a WebGL canvas is not a document tree, so the requirement is a **declared non-visual path to the same information** rather than a pretense that the canvas is accessible. The attribute table (E1) and feature inspection (E2) are that path for feature data, and every map-only affordance has a non-map equivalent.
- **The procurement standard is a floor, never a substitute for the target (noted v0.10).** The harmonised European accessibility standard that public buyers cite in contracts currently references an **earlier** WCAG version than the target above, and a research round proposed adopting it as the target. That proposal is **rejected on the ground that it lowers an existing commitment**: the procurement standard is recorded here as the reference a contract will name, and the product's own bar stays at the version above, which satisfies the older one by construction. The reason the target exists at all, given that a business-to-business tool may sit outside the direct scope of the consumer-facing accessibility regimes, is that retrofitting accessibility is expensive, public buyers require it contractually, and the foundation's professional-yet-simple rule pushes the same way.
- **Basis:** foundation 0.5 (the common path obvious); Layer 1 E1, E2, K1, K2; S7; M16 (the procurement standard a jurisdiction cites is a package entry).
- **Provenance:** the WCAG 2.2 AA target settled in PRD v0.9; the procurement-standard note and the explicit rejection of the downgrade settled in v0.10.
- **Acceptance:** the chrome passes automated and manual level AA checks; every capability is operable by keyboard on web and desktop; every piece of information the map conveys about a feature is reachable through the table or inspection without the canvas; a map-only affordance with no equivalent fails review.

### N8. Internationalization, units, and coordinate formats

- **Requirement:** Brazilian Portuguese is the primary locale, and because the product is general-purpose and not capped to one national market (foundation 1.3 and foundation section 12), internationalization is structural rather than a translation pass: no user-facing string is hard-coded in a component, and numbers, dates, and lists format by locale. The load-bearing part for this domain is that **units and coordinate formats are data rather than formatting accidents**: a metric already carries its unit and its frame (M5), so switching a display unit (hectares, square metres, acres) or a coordinate format (decimal degrees, degrees-minutes-seconds, a projected pair) is a presentation change that **never alters a stored value**. Code, identifiers, and comments are English regardless of the interface locale.
- **Basis:** foundation 1.3, foundation section 12; M5; AR2.
- **Provenance:** settled this PRD round.
- **Acceptance:** switching locale changes every user-facing string, number, and date format with no rebuild; switching a display unit or coordinate format leaves stored values identical, asserted by a round-trip test; a hard-coded user-facing string fails lint; a locale decimal separator never enters a stored number.

### N9. Observability of the paths where silence hurts

- **Requirement:** the sync path is where a silent failure becomes lost work, so it is observable by construction: every flush records its batches, its dedup decisions, its conflict verdicts, its authorship normalizations, and its force-upgrade rejections, keyed by operation identifier and clientID, so a user report maps to a reconstructible decision trail. Logs carry identifiers and decisions and **not geometry payloads or personal data** (N5). Every refusal presented to a user is also recorded, and every recorded refusal was presented, because the product's moral line is that nothing fails silently.
- **The mechanism half, settled in v0.12 under the foundation decision of the same round, and it is three properties rather than a tool.** **Logs are structured and carry their correlation keys from the first line of code**, because the reconstruction requirement above is a join, and a join cannot be added to free-text logs later without editing every call site; the keys are the operation identifier, the clientID, the tenant, and the request or task that carried it, bound once per request and per background task rather than passed by hand. **Redaction is a property of the logging path**, not of each caller remembering: geometry payloads and personal data are kept out by the path itself, since a discipline that depends on every author is a leak with a date on it. **Telemetry is emitted vendor-neutral and the backend is swappable** (foundation section 10, v0.16), which is the same rule as the pluggable data provider. One dated caveat binds the mechanism and will expire: as of May 2026 the OpenTelemetry Python traces and metrics SDKs are stable while its logs SDK is still in development, so the log path runs through the standard library with the trace identifiers injected into it, and the record a compliance question is answered from does not depend on an unstable SDK.
- **Client telemetry is the same mechanism, and it is where the N1 budgets get real numbers.** The interaction rules N1 states (no main-thread task over the long-task line, no interaction past the perceived-lag threshold at the 75th percentile) are what a browser already reports, so real-user telemetry from the surfaces is a legitimate and stronger source for the 10.5 measurements than a bench alone, especially for the field tablet. It carries the same redaction rule, and more strictly: a browser leaks identifiers through URLs and user events unless the path strips them.
- **Basis:** foundation section 4 and foundation section 10 (the observability decision, v0.16); I2, I9, I10; T2, T5; N1, N5.
- **Provenance:** the requirement settled in PRD v0.9; the mechanism half settled in v0.12 from the foundation round that put observability on the record.
- **Acceptance:** given an operation identifier from a user report, the flush decision path is reconstructible end to end; no log line carries coordinates or personal data, asserted by a test over the logging path rather than by review; every user-visible refusal has a matching record and the reverse; a failure with no user-visible signal and no record fails review; a log line on the sync path that carries no correlation key fails review; the emitted telemetry is readable by a second backend without changing application code, which is what proves the neutrality claim.
- **Open / ADR:** the backend, the sampling policy, the dashboards and the alerting are an ADR whose trigger is the first real users (foundation section 10, v0.16); the logging library and the client telemetry SDK are part of the same ADR, surveyed in `specs/dependencies.md`.

### N10. Reliability, resync, and backpressure

- **Requirement:** after any disconnection inside the supported offline window, reconnect converges with no user intervention (I2), resends are idempotent (I9), a gap resyncs from the database (T2.2), and the queue survives a crash and a restart (T1.2). What this block adds is the shape that keeps those guarantees true at real field volumes: a large queue flushes in **bounded batches with per-batch acknowledgment**, preserving the contiguous mutation-number order (M10) and showing progress, so a long offline trip never becomes a single all-or-nothing request that times out and takes the window with it. An interrupted batch flush resumes from the echoed cursor (T2.3) rather than from the beginning.
- **Basis:** I1, I2, I9; T1.2, T2.1, T2.2, T2.3, M10; C1, C2, C9, C12.
- **Provenance:** the guarantees closed in foundation v0.2, v0.7, and v0.8; the batching and backpressure shape is settled this PRD round.
- **Acceptance:** a queue far larger than one practical request flushes to completion in batches with visible progress and no loss; interrupting mid-flush and reconnecting resumes from the echoed last-applied with no duplicate and no gap; batching never breaks mutation-number contiguity, which since 2026-08-11 is contiguity **within one flush domain**, one clientID in one tenant and one project (M10).

### N11. Supported environments

- **Requirement:** the web floor is **WebGL2**, because MapLibre GL JS v5 removed WebGL1 support and requires WebGL2, and the library targets ES2019, which puts browsers and tooling older than roughly 2022 outside the floor. An environment below the floor is **detected and told plainly** rather than rendering a broken or blank map. The support matrix (browsers, operating systems, devices) is declared and versioned in the dependency survey, and the **named reference devices** (a field tablet and a laptop) are the same ones N1's budgets are measured on and the field surface is validated on, so a budget and a support claim never refer to different hardware.
- **Basis:** foundation section 8 (MapLibre as the renderer); N1, T3.6, S4, S7; the external-dependency rule.
- **Provenance:** settled this PRD round, against the current MapLibre GL JS v5 requirement.
- **Acceptance:** a browser without WebGL2 receives an explicit unsupported message rather than a blank canvas; the support matrix exists, names versions, and lives in the dependency survey; the reference devices are pinned there and are the ones every budget cites.
- **Open / ADR:** the concrete browser and operating-system version floors are pinned in `specs/dependencies.md` when it is written, against the versions actually in the lockfile rather than from memory.

### N12. Availability, degradation, and recovery

- **Requirement:** three properties, all of them free at design time and expensive to retrofit (foundation section 10, v0.16). **Liveness and readiness are distinct probes and are never conflated:** liveness answers whether the process should be restarted and therefore touches no dependency, because a probe that fails on a slow query restarts a healthy service and turns a hiccup into an outage; readiness answers whether this instance should receive traffic and therefore does check what it needs. **Degradation is announced, never silent:** when a dependency is unavailable the surface names the capability that is unavailable and why, which is the S6 offline rule applied to a server-side outage, and an outage that presents as a wrong answer or a blank result is the silent-discard sin in a different costume. **A backup counts only once a restore has been rehearsed**, and the rehearsal is recorded with its date, its versions, and what came back, on the same discipline N1 applies to a measured budget; the shape is continuous archiving with point-in-time recovery rather than a periodic dump alone, because the data lost in an incident here is legally consequential and the acceptable loss window is the last operation rather than the last night.
- **Two consequences specific to this product, so a generic runbook does not overwrite them.** A **logical restore into a new cluster is a survivable event by design**, because ADR-0004 chose a resync cursor that is ordinary data in an ordinary column rather than an artifact of the cluster's physical identity; that property is load-bearing for the restore plan, and any future change to the cursor is a change to this requirement. And the operation log is append-only (M15), so backup growth and the retention policy of foundation OQ-20 are one conversation: a retention rule that keeps everything forever is also a backup that grows forever.
- **Basis:** foundation section 10 (the availability decision, v0.16), section 5 (what is refused is said), ADR-0004; I2, I9; M15, N9, N10, S6; OQ-20.
- **Provenance:** settled in v0.12 from the foundation round of the same date; the liveness reasoning was already implemented in `apps/api` before it was written down here, which is why it is stated rather than proposed.
- **Acceptance:** the liveness probe passes while a dependency is down and the readiness probe fails, and neither is implemented in terms of the other; a dependency outage produces a named, user-visible unavailability with a reason rather than a blank result or a wrong one; a restore rehearsal exists with its date, its versions, and the verification of what came back, and a backup with no recorded rehearsal fails review; restoring into a fresh cluster leaves offline clients able to resync from the cursor they already hold.
- **Open / ADR:** the backup tooling, the schedule, and the recovery-point and recovery-time targets are an ADR gated on a deployment target existing; the availability target itself, the replica and failover topology, and any multi-region posture wait for a measured need and for a commercial commitment (foundation section 10, v0.16), with the residency constraint of N5 binding whatever wins.

---

## 9. Design system and UI

> **Scope.** The UI contract: the token system, the material system, the shell geometry, the panel and layout system that makes family K real, iconography and states, the component library's role, the map components, and the catalog. It fixes what must be true of every screen; it does not draw screens, which is the catalog's job.
>
> **IDs.** U1 to Un (user interface).
>
> **Ratification.** The visual language was explored in a throwaway prototype (`tests/prototypes/editor`) and the **owner has ratified that language as Mapsift's visual identity**. That ratification is an owner decision rather than the prototype becoming authoritative, and this section is the authority that carries the identity forward in normative form. The three things the rebuild must improve on the prototype, stated by the owner and turned into requirements below, are code organization (U1, U9, U10), hand-maintainability (U1, U9, U12), and structural robustness (U2, U3, U11).
>
> **The working rule: reference the look, recreate the code.** For **design-system and interface work only**, the prototype is a **permitted visual reference**, and an agent or a developer is expected to open it to see what the result must look like: the material, the spacing, the geometry, the density, the feel of a hover, how a panel behaves under the hand. That permission is bounded by three rules that do not bend.
>
> 1. **Always recreate by refactoring, never copy.** No file, no class, no stylesheet block, and no component structure moves across. The prototype answers *what it must look like*; this section answers *how it is built*, and every rule below (tokens with no literals, one material, semantic state names, library-first, accessibility, the catalog) applies to the rebuilt version even where the prototype violated it. The known case is concrete: the prototype produces the right hover with colour-named classes, and the rebuild produces the same hover with semantic state tokens (U9).
> 2. **Where the prototype and this section disagree, this section wins**, and the *look* is preserved by other means. A prototype implementation is never a reason to relax a rule here.
> 3. **The permission covers appearance and interaction feel, nothing else.** Architecture, state management, persistence, identity, geometry, and logic are governed by Layers 2 and 3, and the prototype's shortcuts in those areas are explicitly not inherited: client logic living in the UI instead of the shared core (C11), a browser key-value store instead of the T1.2 store behind an interface, a counter instead of an operation log, a timestamp-plus-counter identifier instead of the I3 one, chrome hand-rolled around the component library (U10), and a component that renders correctly only because of a mismatched theme block (U4).
>
> A **visual comparison against the prototype is legitimate evidence** that the rebuilt interface matches the ratified identity, and it is the one way the prototype may be cited. Its code is never cited as justification for a requirement, a structure, or a decision.

### U1. The token system is the single source of truth

- **Requirement:** every visual value comes from a named token, and **no component carries a raw colour, radius, size, or spacing literal**. The scales are closed and deliberately small, because smallness is what makes the system maintainable by hand: a designer or a developer holds the whole scale in their head and a new value is a visible decision rather than a silent drift. The ratified scales are these. **Base surfaces:** the page behind everything, the application background, the corner tone, and the shell tone. **Radius, four steps:** 4 px for fields, small controls, chips and panels; 6 px for cards, buttons and floating controls; 9 px for menus, dialogs and toasts; and a pill. **Type, six steps:** 10 px captions (units, counts, tiny meta), 11 px labels and secondary text as the readable floor, 12 px small body, 13 px base, 15 px emphasis and metric values, 18 px large values and titles. **Text, four steps** from primary to quaternary, with the two weakest steps set so they hold contrast on the dark material (N7). **Accent,** one hue plus its hover, used sparingly. **Divider and hairlines.** **Spacing** is a closed scale on the same rule, rather than free numbers picked per component.
- **Basis:** foundation 0.5 (consistency is what makes a tool feel learnable); foundation 9.6.5; N7.
- **Provenance:** the scales are the ones consolidated during the prototype and ratified by the owner this PRD round; the closed-scale rule and the no-literals rule are settled here.
- **Acceptance:** a raw colour, an off-scale radius, or an off-scale font size in a component fails lint; changing a token changes every surface with no component edited; adding a step to a scale is a change to the token file and is visible as such in review.

### U2. One material, three layers, and a fourth thing that is not the material

- **Requirement:** there is **one glass material**, a single tint, a single blur, and a single saturation, and surfaces differ only by **alpha and elevation, never by colour**. The material has the two states U3 defines (Glass and Solid) and the two colour schemes U4 defines; those are token sets, not new materials, so nothing below changes when either axis is switched. That is what makes the frame and the floating panels read as one system rather than as a pile of separately-tuned recipes. Three layers use it: the **chrome** (top bar, rails, status bar), slightly more solid; the **floating surface** (panels), lighter so the map breathes through; and the **transient overlay** (menus, pickers, dialogs, toasts, the drag preview), the densest. The fourth thing is not the material and must never be given it: **inset content is solid and never blurred**, which is cards, fields, metric boxes, and recessed wells sitting on top of a surface, with one card tone, one well tone, and one hairline. Every surface in the product points at these tokens, including the ones that render outside the application root, and **a new surface that invents its own recipe is a defect**, not a variation.
- **Basis:** foundation 0.5 (a consistent surface is what makes learning transfer between corners of the tool); U1.
- **Provenance:** the single-material consolidation was made during the prototype, replacing eight ad-hoc recipes, and is ratified this PRD round.
- **Acceptance:** every translucent surface resolves to the material tokens and none declares its own blur, tint, or saturation; an inset never carries a backdrop filter; a surface rendered outside the application root (an overlay, a toast) matches the chrome exactly.

### U3. The material axis: Glass and Solid

- **Requirement:** the material (U2) has **two states the user chooses between**, and they are an appearance decision rather than an apology for slow hardware. **Glass** is the translucent material with its blur and saturation. **Solid** removes the filter **entirely rather than blurring by zero**, so no backdrop layer is composited at all, which is the only version of the setting that buys anything. The switch is applied at the **document root** so it reaches surfaces rendered outside the application root, it persists per installation, and every surface honours it by construction because every surface reads the same tokens (U2). Both states are legible: contrast holds in either (N7). **The performance consequence is real and secondary:** Solid is the state that gives the GPU back to the map, which is why the N1 budgets are measured in both, and it is not the reason the state exists.
- **Basis:** N1, N7, U2, U4; foundation 0.5.
- **Provenance:** both states were built and validated in the prototype (which ships Glass and Solid within the dark scheme) and are ratified by the owner as user-facing appearance modes this round, reframed from the "performance mode" the first draft of this section called them.
- **Acceptance:** in Solid, no composited backdrop filter exists anywhere, including overlays rendered outside the application root; contrast passes in both states; the choice persists across restarts; the N1 budgets are measured in **both** states and recorded separately.

### U4. The appearance model: two axes, four combinations, one token set each

- **Requirement:** appearance has **two orthogonal axes**: the **colour scheme** (Dark or Light) and the **material** (Glass or Solid, U3). Four combinations ship. **Each combination is a complete token set switched at the root, and a per-component variant override is prohibited by name.** A component that hardcodes a colour for one scheme, or carries a scheme-specific utility variant, is a defect under this requirement and under U1's no-raw-literals rule at the same time, and it is the concrete failure mode a vendored library brings in. **The default is Dark Glass**, because the ratified identity is the chrome receding so the map and the data are the bright thing on the screen (foundation 0.5); the product does **not** follow the operating system's preference by default, since that would hand the identity to a setting outside the product. A **vendored or third-party component is mapped onto the Mapsift token set when it is adopted, and if it cannot be mapped it is not adopted**, and no component may depend on a mismatched or default theme block to render correctly.
- **Basis:** U1, U2, U3; foundation 0.5, 9.6.5.
- **Provenance:** the first draft of this section said the chrome was dark by design and **not** a theme toggled off a light default, with a light variant only hypothetical. The owner ratified the four-mode model this round, which supersedes that sentence; what survives from it, and is now load-bearing rather than hypothetical, is the architectural half: a variant is a complete token set at the root, never a per-component override.
- **Acceptance:** switching either axis switches the whole interface with no component edited; no component carries a scheme-specific override or a raw colour; every vendored component's tokens resolve to Mapsift tokens; a new user lands in Dark Glass; the four combinations each pass the N7 contrast checks.
- **Open / ADR:** whether the user's choice syncs across devices or stays per installation is a small product call, deferred with the rest of the preference model.

### U5. Typography and numerals

- **Requirement:** three families, each with one job: a **sans** for the interface, a **display** face for identity moments, and a **monospace** for data that must align or be read character by character (SQL, coordinates, identifiers). **Tabular numerals are enabled globally**, because this is a tool of numeric tables and a metric that jitters as it updates is a metric the professional stops trusting. The type scale is U1's six steps and nothing else. The **document root font size is never overridden**, because the spacing and sizing scales assume the standard root; the editor's base size lives on the editor host instead.
- **Basis:** U1; Layer 1 E1 (the attribute table), G1 and D8 (metrics); AR3.
- **Provenance:** ratified this PRD round.
- **Acceptance:** numeric columns align and do not shift width as values update; no component sets a size outside the scale; the document root font size is untouched, asserted by a test.

### U6. The shell geometry

- **Requirement:** the editor is a **full-bleed map with the chrome floating over it**: a top bar, a left tool rail, a right panel dock, a status bar, and a transparent stage between them. The stage is **click-through**, so panning and zooming reach the map through every gap, and each floating surface opts back into events for itself, which means a newly added panel is interactive by construction rather than by remembering. The seam where the chrome meets the map is a **hairline frame with concave corners**, so the visible map reads as a rounded window rather than a rectangle cut out of a panel. The ratified dimensions are a 44 px top bar, 48 px rails, a 26 px status bar, and a seam radius of 4 px at the top and 2 px at the bottom, and they are **tokens**, not literals repeated per component. The map control cluster sits bottom right and **fades when a panel covers it** rather than competing for the same pixels.
- **Basis:** foundation 0.5 (the map is the subject, the chrome is the frame); foundation section 8 (MapLibre as the renderer); U1, U2.
- **Provenance:** the geometry was built and tuned in the prototype and is ratified by the owner this PRD round.
- **Acceptance:** the map is visible behind the chrome edge to edge; a click in an empty stage area pans the map; every floating surface receives its own events with no per-panel wiring; the seam, the corners, and the shell dimensions all come from tokens; a covered control fades and restores.

### U7. Panels, docking, and the layout system that makes family K real

- **Requirement:** every panel is the **same surface with the same grab header and the same close control**, so learning one panel teaches all of them. Panels float over the map, drag by their header, resize, and **never overlap**: a dragged panel is pushed out of the others along the axis of least penetration so it slides along an obstacle's edge, keeps a fixed gap, and is clamped inside the stage. A panel can also live docked in the rail rather than floating. On top of that behaviour the family K requirements become concrete: the user shows and hides panels and tools, moves and resizes them, switches between layout modes, and **saves named layouts** that restore later, scoped to the surface family (S8), with a deliberately simple default and the depth one step away (K1, K2, foundation 0.5).
- **Basis:** Layer 1 K1, K2; S8; foundation 0.5.
- **Provenance:** the non-overlapping drag behaviour and the dock were built in the prototype and are ratified this PRD round; named saved layouts are K1's requirement and are not yet built anywhere.
- **Acceptance:** two open panels never overlap, and a dragged panel slides along an obstacle rather than covering it; every panel shares one header and one close control; a panel docks and undocks; a named layout saves and restores within its surface family; the default layout is the simple one.
- **Open / ADR:** the preset layout modes and the panel inventory are refined with the engineer and real use (K1), and the docking model beyond a single dock rail is an ADR.

### U8. Iconography

- **Requirement:** one icon set, line style, one stroke weight, sized from the scale, and **no emoji is ever used as an interface affordance**. An icon-only control always carries an accessible name and a tooltip (N7), because an icon alone is a guess for anyone who has not learned it yet.
- **Basis:** N7; foundation 0.5; U1.
- **Provenance:** ratified this PRD round.
- **Acceptance:** every icon comes from the one set; no emoji appears as an affordance; every icon-only control has an accessible name and a tooltip.

### U9. States are semantic, not colour-named

- **Requirement:** interactive states are **semantic tokens** (hover, active, selected, disabled, focus, danger), never utility names that encode a colour value. This is the concrete fix for the pattern the prototype used, where a hover class was named after its grey, which reads fine until the meaning changes and every usage has to be renamed to keep telling the truth. Hover is **instant with no transition**, which is part of the ratified feel. Focus is always visible (N7). **Selection is never conveyed by colour alone** (N7), and state is never conveyed by the accent hue alone, since the accent is used sparingly by design.
- **Basis:** U1, N7; foundation 0.5 (consistency across corners of the tool).
- **Provenance:** the instant-hover feel is ratified from the prototype; the semantic-naming rule is settled this PRD round as the maintainability fix the owner asked for.
- **Acceptance:** no class or token name encodes a colour value; changing a state token changes every occurrence of that state; focus is visible on every interactive element; every selected state has a non-colour cue.

### U10. The library is the source of the chrome

- **Requirement:** the interface is built from the component library `@mapsift/ui`, consumed **by package name and never by a relative path into its source**, and **no bespoke element may duplicate a primitive the library provides**. If a button, menu, tooltip, dialog, popover, or form control exists in the library, the editor uses it; if the library's version is not good enough, the library is improved and every consumer benefits, rather than the editor forking a copy in place. A component that is genuinely editor-specific (the tool rail, the map stage, the panel frame) lives in the editor and is still assembled from library primitives and tokens. A primitive that turns out to be shared moves **into** the library rather than being copied a second time.
- **Basis:** foundation 9.6.5; the monorepo rule (`apps/` never imports from another `apps/`, everything shared crosses through `libs/`).
- **Provenance:** settled this PRD round. The prototype deliberately hand-rolled most of its chrome to hit visual fidelity fast, which is correct for a prototype and is exactly the debt this requirement refuses to inherit.
- **Acceptance:** no relative import reaches into the library's source; no bespoke re-implementation of a library primitive exists; a shared primitive lives in the library and not in a feature folder; the editor's own components are assembled from primitives and tokens.

### U11. The map components

- **Requirement:** the map is reached through a **declarative component layer** over MapLibre GL JS, built with the same technique and the same tokens as the rest of the library: a map container, layer and source groups, markers and clusters, popups and tooltips, shapes, and the zoom, locate, fullscreen, search, layers, and draw controls. The architectural constraint governs the API: **no live map handle crosses a capability or core boundary** (C11, T7.1, M11), so the map components own the live instance internally and expose serializable state outward, and MapLibre's own default chrome is suppressed in favour of Mapsift's controls. The renderer is settled (foundation section 8, WebGL2 per N11), so a reference project built on a different renderer may inform the component inventory and the declarative shape and **its rendering backend does not come along**.
- **Basis:** foundation section 8, 9.6.4, 9.6.5; C11; T7.1, M11, M14, N11.
- **Provenance:** the renderer closed in foundation v0.1; the component-layer requirement and the no-live-handle constraint are settled this PRD round.
- **Acceptance:** the map layer exposes a declarative API and no live map object crosses a capability or core boundary; the controls are styled from the tokens; no second rendering library enters the dependency set; the editable source is addressed by stable identifiers (M14).

### U12. The catalog, and the tokens as the cross-platform contract

- **Requirement:** the design system is documented in an **isolated, versioned component catalog** (foundation 9.6.5), and every library component appears in it with its states, so a change to a token or a primitive is reviewed against the whole system rather than against one screen. The **tokens are exported in a platform-neutral form**, because the Angular component library does not cross to Flutter (foundation 9.6.3) and the thing that must cross is the identity: the mobile surface rebuilds the components and consumes **the same token values**, so the two surfaces are the same product rather than two products that resemble each other.
- **Basis:** foundation 9.6.3, 9.6.5; S1, S8; U1.
- **Provenance:** the catalog principle closed in foundation v0.4; the tokens-as-the-cross-platform-contract rule is settled this PRD round.
- **Acceptance:** every library component appears in the catalog with its states, and a component absent from it fails review; the token set is exported in a form the Flutter surface consumes; a token changed once changes both surfaces.
- **Open / ADR:** the catalog tool (Storybook on the web, a Flutter equivalent when mobile arrives) is an ADR per foundation 9.6.5, and the token export format is part of it.

---

## 10. What remains for this PRD to be complete

This section is the PRD's own gap list, kept current so completion is a checked state rather than a feeling. The gaps do not block each other.

**10.1 Blocks not yet written.** None. All four layers, the non-functional block (PRD section 8), and the design system (PRD section 9) are drafted. What remains below is not prose to write but decisions, artifacts, and measurements.

**10.2 Requirements that are written but still soft.** **None as of v0.10.** Every item is a pass/fail test (PRD section 0.2). The one that was not, **J2** (work output and report), whose acceptance said it would be specified with the engineer, is closed: its acceptance is now the regenerate-after-a-vertex-edit test, and the artifact still wanted from the engineer (a real delivered exemplar) sharpens the wording and the ordering of the template rather than the test.

**10.3 Artifacts the requirements call for and that do not exist yet.**

- **The capability-by-surface matrix** that S1 requires, covering every Layer 1 capability with a reason on every non-available cell.
- **The component catalog** that U12 requires, with every library component and its states, plus the platform-neutral token export the Flutter surface will consume.
- **The native-kit tagging table** foundation 9.5 asks the PRD to carry: each analysis capability tagged native or extensible **with its frequency-and-centrality justification recorded**, so the boundary is not relitigated later. Layer 1 G2 fixes the native core and foundation section 3 lists the extension candidates. **Partly delivered in v0.10:** G2 now records the justification for the five capabilities promoted into the core and for the ones deliberately left as extensions, from a frequency review whose input is a domain round rather than an observed sample (`specs/domain-questions.md` Q2.1). What is still missing is the full table over every capability, and the confirmation of the frequency column by a practising professional, which is the half of that round research could not produce.
- **The restore rehearsal record** that N12 requires: a dated entry saying what was restored, from which backup, on which versions, and what was verified afterwards. A backup with no such record is not a backup this document recognises, and the entry belongs beside the N1 measurements rather than in a runbook nobody opens.
- **The Brazilian jurisdiction package** that M16 requires: the legal-weight feature types with their cited authority, the regulatory geometry tables, the deliverable and attestation templates, and the retention policy, each entry dated and sourced. Its content is gated on the owners in 10.4, and one entry is explicitly blocked: the consolidated-area recomposition ladder failed verification in the round that produced the rest, because the primary text could not be reached, and it does not enter until it is read verbatim (`specs/domain-questions.md` section V.3).

**10.4 Gates owned by people, not by research.**

- **OQ-8, the legal-weight classification rule** (the environmental engineer). It arms preserve-not-discard across families C, D, and G3, and it is also load-bearing for M7 and S5. **Narrowed in v0.10, and what is left is smaller than it was:** the **criterion** is closed in the foundation (an error in the geometry can produce a sanction, an authority's demand, a loss in a public register, or a change in a legally declared obligation or asset), the **mechanism** is closed in M7 (the marker follows the feature's nature and never the registry's state of the moment), and the **shape** is closed in M16 (a package entry with its cited authority). What remains is the **list** for the Brazilian package, applying the closed criterion, which is domain knowledge and still the engineer's.
- **OQ-5, which environmental analyses matter beyond the decided core** (the engineer), which also feeds J2.
- **OQ-7, the license and seat tiers** (a product and pricing decision), which T6.2's ceiling refers to.

**10.5 Numbers this PRD asserts as budgets and does not yet have.** Each is set by measurement on a named reference device under the N1 protocol, in both material modes (U3), never assumed: the **element budget** (M2), the **editable working-set budgets** and the reference devices (T3.6, M14, N11), the **I6 per-tile budget** (N1), the **maximum supported offline window** and the cursor retention that must exceed it (M4), and the **compatibility window** for the force-upgrade (T9.4, OQ-15).

**10.6 Pending decisions that are this document's own, not foundation OQs.** A deferral that names no owner and lands in no section is a decision nobody makes. These are the ones an audit of the 47 Open/ADR fields found pointing nowhere:

- **The offline session parameters (T5.2):** the offline-authenticated lifetime, the refresh-rotation policy, and the authorization-failed resolution UI are named as PRD decisions and are not taken anywhere in this document.
- **"The detailed permission model" (T6.3, T6.4, T6.5):** three requirements defer to an artifact by that name which does not exist and is not a section here. T6 **is** the permission model, so those deferrals point at themselves. Either the remaining detail lands in T6 or the artifact is created and listed in 10.3.
- **The preview-versus-authoritative surface (M5):** deferred to Layer 4, and Layer 4 never received it. No S requirement mentions a preview value.
- **The panel inventory and the preset layouts:** S8 defers to the design system, U7 defers to K1 and to an ADR, K1 defers to a design decision with the engineer. The loop closes with nobody deciding.
- **The support matrix and the named reference devices (N11):** the acceptance requires them to live in `specs/dependencies.md`, which exists and does not carry them yet.

**10.7 Acceptance criteria that are not yet falsifiable.** J2 left this list in v0.10 (see 10.2). Three read as tests and are not:

- **K1 and K2** rest on "simple" and "guided", which two reviewers can disagree about with neither being wrong. **They are not fixed by inventing a number here**, which would be exactly the premature specification this document avoids elsewhere; they are fixed by a countable criterion set with the engineer at design time, and that is the pending item.
- **B1** says "recent low-cloud imagery" without saying how recent or how cloudy, while `specs/data-and-tooling-references.md` section 1.4 already carries the Sentinel-2 revisit cadence the criterion could inherit.
- **T3.6** invokes a "promotion-latency budget" and "the long-task line" that N1 does not name among its three budgets and two interaction rules. Either N1 names them or T3.6 folds into what N1 already defines.

**10.8 Structural.** The prose is complete and the file is now about 1,200 lines, so the split per layer that was deferred while the material was still growing is the remaining structural task, with `specs/index.md` and the authority chain updated to match. It is a mechanical move and it is not a prerequisite for anything above. The two adjacent documents the canon cites, `specs/testing.md` and `specs/dependencies.md`, both exist as of 2026-07-30. What `specs/dependencies.md` still owes N11 is the **support matrix and the named reference devices**, which it does not yet carry; that belongs in 10.3 with the other missing artifacts.
