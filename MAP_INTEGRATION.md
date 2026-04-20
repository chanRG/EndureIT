# Map Integration for Strava Activities

## Overview
Interactive Strava route maps are rendered inside the activity detail modal using Leaflet paired with Mapbox’s **Dark** basemap. If a Mapbox access token is not supplied the component gracefully falls back to Carto’s dark tiles, so the dark UI experience is preserved without an API key.

## Key Features
- 🗺️ Dark-themed Mapbox tiles (`mapbox/dark-v11`) for cohesive styling.
- 🧭 Auto-fit to the full route with Strava-orange polyline styling.
- 📍 Start (green) and finish (red) markers with glow effects.
- 🚀 Lazy-loaded map so the dashboard bundle stays lean.
- 🔄 Robust fallbacks for missing polylines or missing Mapbox tokens.

## Relevant Files
- `frontend/src/components/ActivityMap.tsx` — Leaflet map implementation.
- `frontend/src/components/ActivityDetailModal.tsx` — Integrates the map into the modal.
- `frontend/src/app/globals.css` — Leaflet-specific styles and dark theme helpers.

## Setup & Configuration
1. **Install dependencies** (already in package.json, but can be re-run if needed):
   ```bash
   docker-compose exec frontend npm install leaflet @types/leaflet
   ```
2. **Configure a Mapbox token (recommended)**  
   Create or edit `frontend/.env.local`:
   ```
   NEXT_PUBLIC_MAPBOX_TOKEN=pk.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```
   Tokens can be generated from [https://account.mapbox.com/](https://account.mapbox.com/).
3. **Restart the frontend** (if running under Docker):
   ```bash
   docker-compose restart frontend
   ```

If `NEXT_PUBLIC_MAPBOX_TOKEN` is omitted the component will log a warning (in non-production builds) and automatically switch to Carto’s `dark_all` tiles, so maps still render.

## Data Flow
```
Strava Activity (API)
├─ map.summary_polyline  (encoded route)
├─ start_latlng          (optional)
└─ end_latlng            (optional)
       ↓
ActivityMap Component
├─ Decode polyline
├─ Initialize Leaflet map
├─ Add Mapbox Dark tiles (or Carto fallback)
├─ Draw route + start/end markers
└─ Fit map bounds to visible data
```

## Runtime Behaviour
- **Polyline available** → route is decoded, drawn, and bounds are fit.
- **Only start/end latlng** → markers are rendered and the map frames them.
- **No location data** → map defaults to world view.
- **Modal reopen** → map instance persists and refreshes cleanly.

## Styling Details
- Route line colour: `#FC4C02` (Strava orange), weight `3`, opacity `0.8`.
- Start marker: glowing green dot, end marker: glowing red dot.
- Map container: dark glass background, rounded corners, subtle border to match the dashboard aesthetic.

## Troubleshooting
| Issue | Resolution |
|-------|------------|
| Mapbox tiles not loading | Ensure `NEXT_PUBLIC_MAPBOX_TOKEN` is set. Check browser console for warnings. |
| No map displayed | Confirm `leaflet` is installed and `ActivityMap` is referenced only on the client. |
| Polyline decoding error | The component catches errors, logs to console, and falls back to start/end markers or world view. |

```bash
# Dependency check
docker-compose exec frontend npm list leaflet

# Reinstall (if needed)
docker-compose exec frontend npm install leaflet @types/leaflet

# Restart frontend service
docker-compose restart frontend
```

## Future Enhancements
- Elevation profile beneath the map.
- Pace/heart-rate heatmaps along the route.
- Segment / lap markers and tooltips.
- Toggle between dark, light, and satellite basemaps.

## Credits
- **Leaflet** – BSD 2-Clause Licence.
- **Mapbox** – Dark basemap style (token required).
- **Carto** – Dark fallback tiles (no token needed).
- **Strava** – Activity data & encoded polyline format.

