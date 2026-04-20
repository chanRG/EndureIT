'use client';

import React, { useEffect, useMemo, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface ActivityMapProps {
  polyline?: string;
  startLatlng?: [number, number];
  endLatlng?: [number, number];
}

// Decode Strava polyline (Google Polyline Algorithm Format)
function decodePolyline(encoded: string): [number, number][] {
  const points: [number, number][] = [];
  let index = 0;
  let lat = 0;
  let lng = 0;

  while (index < encoded.length) {
    let shift = 0;
    let result = 0;
    let byte;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    const dlat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    const dlng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    points.push([lat / 1e5, lng / 1e5]);
  }

  return points;
}

export default function ActivityMap({
  polyline,
  startLatlng,
  endLatlng,
}: ActivityMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const baseLayerRef = useRef<L.TileLayer | null>(null);

  const mapboxToken = useMemo(() => process.env.NEXT_PUBLIC_MAPBOX_TOKEN, []);
  const startIcon = useMemo(
    () =>
      L.divIcon({
        className: 'custom-marker',
        html: '<div style="background-color: #22c55e; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.3);"></div>',
        iconSize: [12, 12],
      }),
    []
  );

  const endIcon = useMemo(
    () =>
      L.divIcon({
        className: 'custom-marker',
        html: '<div style="background-color: #ef4444; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.3);"></div>',
        iconSize: [12, 12],
      }),
    []
  );

  useEffect(() => {
    if (!mapRef.current) return;

    // Initialize map only once
    if (!mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapRef.current, {
        zoomControl: true,
        scrollWheelZoom: true,
      });

      if (!mapboxToken && process.env.NODE_ENV !== 'production') {
        console.warn(
          '[ActivityMap] NEXT_PUBLIC_MAPBOX_TOKEN not set. Falling back to dark Carto tiles.'
        );
      }

      const baseLayer = mapboxToken
        ? L.tileLayer(
            `https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/512/{z}/{x}/{y}?access_token=${mapboxToken}`,
            {
              attribution:
                '© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
              tileSize: 512,
              zoomOffset: -1,
              maxZoom: 20,
            }
          )
        : L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution:
              '© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/attributions">CARTO</a>',
            maxZoom: 19,
          });

      baseLayerRef.current = baseLayer.addTo(mapInstanceRef.current);
    }

    const map = mapInstanceRef.current;

    // Clear existing layers (except tile layer)
    map.eachLayer((layer) => {
      if (layer instanceof L.Polyline || layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });

    if (polyline) {
      try {
        // Decode and display polyline
        const coordinates = decodePolyline(polyline);
        
        if (coordinates.length > 0) {
          // Draw the route
          const routeLine = L.polyline(coordinates, {
            color: '#FC4C02', // Strava orange
            weight: 3,
            opacity: 0.8,
          }).addTo(map);

          // Add start marker (green)
          if (coordinates[0]) {
            L.marker(coordinates[0], { icon: startIcon }).addTo(map);
          }

          // Add end marker (red)
          if (coordinates[coordinates.length - 1]) {
            L.marker(coordinates[coordinates.length - 1], { icon: endIcon }).addTo(map);
          }

          // Fit bounds to show entire route
          map.fitBounds(routeLine.getBounds(), { padding: [20, 20] });
        }
      } catch (error) {
        console.error('Error decoding polyline:', error);
      }
    } else if (startLatlng || endLatlng) {
      const bounds: L.LatLngExpression[] = [];

      if (startLatlng) {
        L.marker(startLatlng, { icon: startIcon }).addTo(map);
        bounds.push(startLatlng);
      }

      if (endLatlng) {
        L.marker(endLatlng, { icon: endIcon }).addTo(map);
        bounds.push(endLatlng);
      }

      if (bounds.length > 1) {
        map.fitBounds(L.latLngBounds(bounds), { padding: [20, 20] });
      } else if (bounds.length === 1) {
        map.setView(bounds[0], 13);
      }
    } else {
      // Default view (world)
      map.setView([0, 0], 2);
    }

    // Cleanup on unmount
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        baseLayerRef.current = null;
      }
    };
  }, [polyline, startLatlng, endLatlng, mapboxToken, startIcon, endIcon]);

  return (
    <div 
      ref={mapRef} 
      className="w-full h-64 md:h-96 rounded-xl border border-slate-800/70 bg-slate-900/60 relative z-0 shadow-inner"
      style={{ minHeight: '300px' }}
    />
  );
}

