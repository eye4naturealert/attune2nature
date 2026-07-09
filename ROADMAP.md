Attune2Nature Development Plan

Current Status (Completed)
--------------------------
✓ GitHub repository created
✓ GitHub Actions workflow running
✓ Automatic email alerts working
✓ iNaturalist API integration
✓ Taxon ID species filtering
✓ Pagination implemented
✓ AOI polygon filtering
✓ W&OD buffered trail AOI
✓ Loudoun County AOI
✓ Fairfax County AOI
✓ AOI GeoJSONs moved into data/aois/
✓ W&OD Mile Marker GeoJSON created
✓ Reference folder created
✓ src folder structure created

Current Repository Structure

attune2nature/

data/
    aois/
        WOD_Buffer.geojson
        LoudounCounty.geojson
        FairfaxCounty.geojson

    reference/
        WOD_MileMarkers.geojson

src/
    ingestion/
    spatial/
    enrichment/
    alerts/
    email/
    phenology/

Goal

Continue developing Attune2Nature as a modular geospatial alert platform by completing ONE module at a time, thoroughly testing each before moving on.

Development Order

STEP 1
Build src/spatial/aoi_registry.py

Purpose:
Central location that knows every AOI.

Functions should include:

load_aoi(name)

list_aois()

get_reference_layers(name)

No more hardcoded file paths anywhere else.

--------------------------------------

STEP 2

Move existing polygon filtering code into

src/spatial/

Functions like

point_in_polygon()

find_matching_aoi()

buffer utilities

The current alert script should begin calling these functions.

--------------------------------------

STEP 3

Build src/ingestion/

Separate all iNaturalist API code from business logic.

Functions:

query_species()

paginate()

rate_limit()

future weather queries

future eBird queries

--------------------------------------

STEP 4

Build src/enrichment/

This module enhances observations.

Initially:

Add AOI name

For W&OD ONLY:

Nearest Mile Marker

Distance to Mile Marker

Later:

Weather

Trailheads

Parks

Season

Phenology

Habitat

Elevation

--------------------------------------

STEP 5

Build src/alerts/

This module decides

Should this observation notify someone?

No email logic.

Only alert logic.

--------------------------------------

STEP 6

Build src/email/

Move HTML generation here.

Support:

Email

Later:

SMS

Discord

Push notifications

--------------------------------------

STEP 7

Build src/phenology/

Seasonality engine.

Examples:

First Bluebells of spring

Peak turtle nesting

Migration timing

Historical averages

Bloom progression

--------------------------------------

STEP 8

Website Backend

Connect users

AOIs

Species

Subscriptions

--------------------------------------

STEP 9

Website Frontend

Interactive map

AOI selector

Species selector

User dashboard

Observation history

Alert management

--------------------------------------

Architecture Philosophy

Each module has ONE job.

ingestion/
gets data

spatial/
answers GIS questions

enrichment/
adds context

alerts/
decides whether to notify

email/
communicates

phenology/
understands seasonal behavior

Modules should never duplicate responsibilities.

Always prefer reusable functions over writing new code inside scripts.

Current Priority

Begin with

src/spatial/aoi_registry.py

and fully complete and test it before moving to Step 2.
