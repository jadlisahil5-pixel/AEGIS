import { useEffect, useRef, useState, type MutableRefObject } from "react";
import { setOptions, importLibrary } from "@googlemaps/js-api-loader";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { config } from "@/config/env";
import { DEFAULT_LOCATION, GHAZIABAD_BOUNDS } from "@/config/constants";

// Real Google Maps-based Digital Twin map, centered on Ghaziabad/NCR.
export interface MapMarker {
  id: string;
  type: "emergency" | "ambulance" | "hospital" | "volunteer" | "signal" | "police";
  /** Real coordinates — preferred. */
  lat?: number;
  lng?: number;
  /**
   * Legacy 0-100 percentage position, kept only for portals not yet wired to
   * real backend coordinates. Converted to a real point inside the Ghaziabad
   * bounding box so nothing renders off a fake grid.
   */
  x?: number;
  y?: number;
  label?: string;
  active?: boolean;
  status?: string;
}

export interface RoutePoint {
  lat: number;
  lng: number;
}

interface LiveMapProps {
  markers?: MapMarker[];
  /** Real lat/lng route. Prefer this over the legacy `route` prop. */
  routePoints?: RoutePoint[];
  /** @deprecated legacy 0-100 x/y route, converted into the Ghaziabad bounds. */
  route?: { from: [number, number]; via?: [number, number][]; to: [number, number] };
  className?: string;
  showCorridor?: boolean;
  center?: RoutePoint;
  zoom?: number;
}

let optionsSet = false;
let mapsLibraryPromise: Promise<google.maps.MapsLibrary> | null = null;
let markerLibraryPromise: Promise<google.maps.MarkerLibrary> | null = null;

/** Loads the Maps JS API using the current recommended functional loader API. */
function loadGoogleMaps(apiKey: string) {
  if (!optionsSet) {
    setOptions({ key: apiKey, v: "weekly" });
    optionsSet = true;
  }
  mapsLibraryPromise ??= importLibrary("maps");
  markerLibraryPromise ??= importLibrary("marker");
  return Promise.all([mapsLibraryPromise, markerLibraryPromise]);
}

/** Maps a legacy 0-100 percentage coordinate onto the real Ghaziabad bounding box. */
function xyToLatLng(x: number, y: number): RoutePoint {
  const { latMin, latMax, lngMin, lngMax } = GHAZIABAD_BOUNDS;
  return {
    lat: latMax - (y / 100) * (latMax - latMin), // y grows downward on screen
    lng: lngMin + (x / 100) * (lngMax - lngMin),
  };
}

function markerLatLng(marker: MapMarker): RoutePoint {
  if (typeof marker.lat === "number" && typeof marker.lng === "number") {
    return { lat: marker.lat, lng: marker.lng };
  }
  if (typeof marker.x === "number" && typeof marker.y === "number") {
    return xyToLatLng(marker.x, marker.y);
  }
  return DEFAULT_LOCATION;
}

function legacyRouteToPoints(route: NonNullable<LiveMapProps["route"]>): RoutePoint[] {
  const pts = [route.from, ...(route.via ?? []), route.to];
  return pts.map(([x, y]) => xyToLatLng(x, y));
}

/** Great-circle distance in meters — used only to decide whether a position
 * change is a genuine teleport (new assignment) vs. real incremental GPS
 * movement worth animating smoothly. */
function distanceMeters(a: RoutePoint, b: RoutePoint): number {
  const R = 6371000;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

function easeInOutQuad(t: number): number {
  return t < 0.5 ? 2 * t * t : 1 - ((-2 * t + 2) ** 2) / 2;
}

/**
 * Smoothly tweens a marker between two real, backend-reported positions.
 * This never invents movement — both endpoints are genuine data points
 * (the marker's last known position and the newly received one). It only
 * interpolates the pixels in between so the marker glides instead of
 * jumping, exactly like the real GPS ping it's reflecting.
 */
function animateMarkerTo(
  marker: google.maps.Marker,
  id: string,
  from: RoutePoint,
  to: RoutePoint,
  framesRef: MutableRefObject<Map<string, number>>,
) {
  const pending = framesRef.current.get(id);
  if (pending) cancelAnimationFrame(pending);

  const duration = 900;
  const start = performance.now();

  const step = (now: number) => {
    const t = Math.min((now - start) / duration, 1);
    const eased = easeInOutQuad(t);
    marker.setPosition({
      lat: from.lat + (to.lat - from.lat) * eased,
      lng: from.lng + (to.lng - from.lng) * eased,
    });
    if (t < 1) {
      framesRef.current.set(id, requestAnimationFrame(step));
    } else {
      framesRef.current.delete(id);
    }
  };

  framesRef.current.set(id, requestAnimationFrame(step));
}

const MARKER_GLYPH: Record<MapMarker["type"], { color: string; glyph: string }> = {
  emergency: { color: "#E63946", glyph: "\u2715" },
  ambulance: { color: "#2563EB", glyph: "\uD83D\uDE91" },
  hospital: { color: "#22C55E", glyph: "H" },
  volunteer: { color: "#9333EA", glyph: "\u2605" },
  signal: { color: "#22C55E", glyph: "\u25CF" },
  police: { color: "#1E293B", glyph: "\uD83D\uDE93" },
};

export function LiveMap({
  markers = [],
  routePoints,
  route,
  className,
  showCorridor = false,
  center = DEFAULT_LOCATION,
  zoom = 13,
}: LiveMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const markerObjsRef = useRef<Map<string, google.maps.Marker>>(new Map());
  const animationFramesRef = useRef<Map<string, number>>(new Map());
  const polylineRef = useRef<google.maps.Polyline | null>(null);
  const glowPolylineRef = useRef<google.maps.Polyline | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error" | "no-key">(
    config.googleMapsApiKey ? "loading" : "no-key",
  );

  // Initialize the map once.
  useEffect(() => {
    if (!config.googleMapsApiKey || !containerRef.current) return;
    let cancelled = false;

    loadGoogleMaps(config.googleMapsApiKey)
      .then(([mapsLib]) => {
        if (cancelled || !containerRef.current) return;
        mapRef.current = new mapsLib.Map(containerRef.current, {
          center,
          zoom,
          disableDefaultUI: true,
          zoomControl: true,
          styles: COMMAND_CENTER_STYLE,
        });
        setStatus("ready");
      })
      .catch((err) => {
        console.error("Google Maps failed to load", err);
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep the map recentered if the caller changes center/zoom.
  useEffect(() => {
    if (status !== "ready" || !mapRef.current) return;
    mapRef.current.setCenter(center);
    mapRef.current.setZoom(zoom);
  }, [status, center.lat, center.lng, zoom]);

  // Sync markers.
  useEffect(() => {
    if (status !== "ready" || !mapRef.current) return;
    const g = window.google;
    const existing = markerObjsRef.current;
    const seen = new Set<string>();

    markers.forEach((m) => {
      seen.add(m.id);
      const pos = markerLatLng(m);
      const { color, glyph } = MARKER_GLYPH[m.type];
      const icon: google.maps.Symbol = {
        path: g.maps.SymbolPath.CIRCLE,
        scale: 11,
        fillColor: color,
        fillOpacity: 1,
        strokeColor: "#FFFFFF",
        strokeWeight: 2,
      };

      let marker = existing.get(m.id);
      if (!marker) {
        marker = new g.maps.Marker({
          map: mapRef.current!,
          position: pos,
          icon,
          label: { text: glyph, color: "#FFFFFF", fontSize: "11px", fontWeight: "700" },
          title: m.label,
        });
        existing.set(m.id, marker);
      } else {
        const from = marker.getPosition();
        const shouldAnimate =
          (m.type === "ambulance" || m.type === "police") &&
          from != null &&
          distanceMeters({ lat: from.lat(), lng: from.lng() }, pos) < 2000;

        if (shouldAnimate && from) {
          animateMarkerTo(marker, m.id, { lat: from.lat(), lng: from.lng() }, pos, animationFramesRef);
        } else {
          const pending = animationFramesRef.current.get(m.id);
          if (pending) {
            cancelAnimationFrame(pending);
            animationFramesRef.current.delete(m.id);
          }
          marker.setPosition(pos);
        }
        marker.setIcon(icon);
        marker.setTitle(m.label ?? null);
      }
    });

    // Remove markers no longer present.
    existing.forEach((marker, id) => {
      if (!seen.has(id)) {
        const pending = animationFramesRef.current.get(id);
        if (pending) {
          cancelAnimationFrame(pending);
          animationFramesRef.current.delete(id);
        }
        marker.setMap(null);
        existing.delete(id);
      }
    });
  }, [status, markers]);

  // Cancel any in-flight animations on unmount.
  useEffect(() => {
    return () => {
      animationFramesRef.current.forEach((frameId) => cancelAnimationFrame(frameId));
      animationFramesRef.current.clear();
    };
  }, []);

  // Sync route / corridor polyline.
  useEffect(() => {
    if (status !== "ready" || !mapRef.current) return;
    const g = window.google;

    polylineRef.current?.setMap(null);
    glowPolylineRef.current?.setMap(null);
    polylineRef.current = null;
    glowPolylineRef.current = null;

    const points = routePoints ?? (route ? legacyRouteToPoints(route) : null);
    if (!points || points.length < 2) return;

    if (showCorridor) {
      polylineRef.current = new g.maps.Polyline({
        map: mapRef.current,
        path: points,
        strokeColor: "#22C55E",
        strokeOpacity: 0.9,
        strokeWeight: 5,
      });
      glowPolylineRef.current = new g.maps.Polyline({
        map: mapRef.current,
        path: points,
        strokeColor: "#86EFAC",
        strokeOpacity: 0.7,
        strokeWeight: 2,
        icons: [{ icon: { path: "M 0,-1 0,1", strokeOpacity: 1, scale: 3 }, offset: "0", repeat: "12px" }],
      });
    } else {
      polylineRef.current = new g.maps.Polyline({
        map: mapRef.current,
        path: points,
        strokeColor: "#E63946",
        strokeOpacity: 0.85,
        strokeWeight: 3,
        icons: [{ icon: { path: "M 0,-1 0,1", strokeOpacity: 1, scale: 3 }, offset: "0", repeat: "10px" }],
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, routePoints, route, showCorridor]);

  return (
    <div
      className={cn(
        "relative w-full overflow-hidden rounded-2xl border border-gray-200/80 shadow-sm",
        className,
      )}
      style={{ minHeight: 360 }}
    >
      {status === "no-key" && <MapFallback message="Map unavailable — VITE_GOOGLE_MAPS_API_KEY is not configured." />}
      {status === "error" && <MapFallback message="Google Maps failed to load. Check your network connection or API key." />}
      {status === "loading" && (
        <div className="absolute inset-0 grid place-items-center bg-[#F3F4F6] text-xs font-bold text-[#525866]">
          Loading live map…
        </div>
      )}
      <div ref={containerRef} className="absolute inset-0" />

      {status === "ready" && (
        <>
          <div className="pointer-events-none absolute left-3 top-3 flex items-center gap-2 rounded-md border border-gray-250 bg-white/90 px-2 py-1 text-[10px] uppercase tracking-widest text-gray-700 font-bold shadow-sm backdrop-blur">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" /> Live · Ghaziabad
          </div>
          <div className="pointer-events-none absolute right-3 top-3 rounded-md border border-gray-250 bg-white/90 px-2 py-1 text-[10px] uppercase tracking-widest text-gray-700 font-bold shadow-sm backdrop-blur">
            {center.lat.toFixed(4)}°N · {center.lng.toFixed(4)}°E
          </div>
        </>
      )}
    </div>
  );
}

function MapFallback({ message }: { message: string }) {
  return (
    <div className="absolute inset-0 grid place-items-center gap-2 bg-[#F8F9FB] px-6 text-center">
      <AlertTriangle className="h-6 w-6 text-[#E63946]" />
      <p className="text-xs font-semibold text-[#525866]">{message}</p>
    </div>
  );
}

// Muted, low-noise command-center styling so AEGIS markers/overlays stay visually dominant.
const COMMAND_CENTER_STYLE: google.maps.MapTypeStyle[] = [
  { elementType: "geometry", stylers: [{ color: "#F3F4F6" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#6B7280" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#F8F9FB" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#E5E7EB" }] },
  { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#D1D5DB" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#DCE7F5" }] },
  { featureType: "poi", stylers: [{ visibility: "off" }] },
  { featureType: "transit", stylers: [{ visibility: "off" }] },
];
