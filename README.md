# Attune2Nature

Attune2Nature is a geospatial awareness system that helps people reconnect with local ecosystems by tracking and analyzing wildlife and plant observations in near real-time.

It uses iNaturalist data to detect recent species activity within a defined Area of Interest (AOI), and will eventually incorporate predictive models to forecast likely wildlife encounters based on time, location, and historical patterns.

## 🌿 Current Features

- Pulls recent wildlife observations from iNaturalist (last 24 hours)
- Filters observations by geographic AOI (GeoJSON boundary)
- Identifies species of interest (e.g., turtles, bears)
- Outputs matched observations with location and metadata

## 🧭 Data Sources

- iNaturalist API
- Local GeoJSON AOI boundaries

## ⚙️ Future Development

- Automated daily runs via GitHub Actions
- Email alerting system
- Wildlife encounter prediction models (ML-based)
- Expanded geographic coverage beyond Loudoun County

## 🛰️ Vision

To create a “living awareness layer” over geography that helps people notice, understand, and reconnect with the natural world around them.

attune2nature will help empower individual nature enthusiasts, conservation organizations, parks departments, and citizen science groups.
---

Built with Python, GeoPandas, and iNaturalist API.
