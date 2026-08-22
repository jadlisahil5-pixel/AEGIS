import { useEffect, useMemo, useState } from "react";
import { GoogleMap, useJsApiLoader, Marker, Polyline } from "@react-google-maps/api";
import { cn } from "@/lib/utils";

export interface GoogleMapMarker {
  id: string;
  type: string;
  lat: number;
  lng: number;
  label?: string;
  active?: boolean;
}

interface GoogleLiveMapProps {
  markers?: GoogleMapMarker[];
  route?: { from: { lat: number; lng: number }; via?: { lat: number; lng: number }[]; to: { lat: number; lng: number } };
  className?: string;
  showCorridor?: boolean;
  dark?: boolean;
  routeProgress?: number; // 0 to 1 progress of the entire mission
  policeRoute?: { from: { lat: number; lng: number }; to: { lat: number; lng: number } };
}

const containerStyle = {
  width: "100%",
  height: "100%",
};

export function GoogleLiveMap({ 
  markers = [], 
  route, 
  className, 
  showCorridor = false, 
  dark = false,
  routeProgress = 0,
  policeRoute
}: GoogleLiveMapProps) {
  const { isLoaded } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: "AIzaSyCo5LX__u7xIs3xvVfctlKXA7fkbaEFKv8",
  });

  const [directionsPath, setDirectionsPath] = useState<{ lat: number, lng: number }[]>([]);
  const [policePath, setPolicePath] = useState<{ lat: number, lng: number }[]>([]);

  // Fetch real roads when map loads and route changes
  useEffect(() => {
    if (!isLoaded || !window.google || !route) return;

    const directionsService = new window.google.maps.DirectionsService();

    const waypoints = (route.via || []).map(wp => ({
      location: wp,
      stopover: true,
    }));

    directionsService.route(
      {
        origin: route.from,
        destination: route.to,
        waypoints: waypoints,
        travelMode: window.google.maps.TravelMode.DRIVING,
      },
      (result, status) => {
        if (status === window.google.maps.DirectionsStatus.OK && result) {
          // Extract the detailed path array from the route
          const path = result.routes[0].overview_path.map(p => ({
            lat: p.lat(),
            lng: p.lng(),
          }));
          setDirectionsPath(path);
        } else {
          // Fallback to straight lines if Google API fails or is unauthorized
          setDirectionsPath([route.from, ...(route.via || []), route.to]);
        }
      }
    );
  }, [isLoaded, route?.from?.lat, route?.from?.lng, route?.to?.lat, route?.to?.lng]);

  // Fetch police real roads
  useEffect(() => {
    if (!isLoaded || !window.google || !policeRoute) return;

    const directionsService = new window.google.maps.DirectionsService();

    directionsService.route(
      {
        origin: policeRoute.from,
        destination: policeRoute.to,
        travelMode: window.google.maps.TravelMode.DRIVING,
      },
      (result, status) => {
        if (status === window.google.maps.DirectionsStatus.OK && result) {
          const path = result.routes[0].overview_path.map(p => ({
            lat: p.lat(),
            lng: p.lng(),
          }));
          setPolicePath(path);
        } else {
          setPolicePath([policeRoute.from, policeRoute.to]);
        }
      }
    );
  }, [isLoaded, policeRoute?.from?.lat, policeRoute?.from?.lng, policeRoute?.to?.lat, policeRoute?.to?.lng]);

  const center = useMemo(() => {
    if (markers.length === 0) return { lat: 28.6692, lng: 77.4538 };
    const lats = markers.map(m => m.lat);
    const lngs = markers.map(m => m.lng);
    return {
      lat: (Math.min(...lats) + Math.max(...lats)) / 2,
      lng: (Math.min(...lngs) + Math.max(...lngs)) / 2,
    };
  }, [markers]);

  // Use a custom styling to match the AEGIS dark/light theme
  const mapOptions = {
    disableDefaultUI: true,
    styles: dark ? darkStyle : lightStyle,
  };

  const getMarkerIcon = (type: string) => {
    switch (type) {
      case "ambulance": return "🚑";
      case "police": return "🚓";
      case "emergency": return "🚨";
      case "hospital": return "🏥";
      default: return "📍";
    }
  };

  // Helper to interpolate position precisely along the complex curved path array
  const getInterpolatedPosition = (path: {lat: number, lng: number}[], progress: number) => {
    if (path.length === 0) return null;
    if (progress <= 0) return path[0];
    if (progress >= 1) return path[path.length - 1];

    // Calculate total distance of path
    let totalDist = 0;
    const segments = [];
    for (let i = 0; i < path.length - 1; i++) {
      const p1 = path[i];
      const p2 = path[i+1];
      const dist = Math.sqrt(Math.pow(p2.lat - p1.lat, 2) + Math.pow(p2.lng - p1.lng, 2));
      segments.push(dist);
      totalDist += dist;
    }

    const targetDist = totalDist * progress;
    let accumulated = 0;

    for (let i = 0; i < path.length - 1; i++) {
      const segDist = segments[i];
      if (accumulated + segDist >= targetDist) {
        const segProgress = segDist > 0 ? (targetDist - accumulated) / segDist : 0;
        const p1 = path[i];
        const p2 = path[i+1];
        return {
          lat: p1.lat + (p2.lat - p1.lat) * segProgress,
          lng: p1.lng + (p2.lng - p1.lng) * segProgress
        };
      }
      accumulated += segDist;
    }
    return path[path.length - 1];
  };

  if (!isLoaded) return <div className={cn("flex items-center justify-center bg-gray-100", className)}>Loading Maps...</div>;

  // Render the final markers. Intercept the ambulance and apply the real road physics.
  const dynamicMarkers = markers.map(marker => {
    if (marker.type === "ambulance" && directionsPath.length > 0 && routeProgress > 0) {
      const realPos = getInterpolatedPosition(directionsPath, routeProgress);
      if (realPos) {
        return { ...marker, lat: realPos.lat, lng: realPos.lng };
      }
    }
    if (marker.type === "police" && policePath.length > 0 && routeProgress > 0) {
      const realPos = getInterpolatedPosition(policePath, routeProgress);
      if (realPos) {
        return { ...marker, lat: realPos.lat, lng: realPos.lng };
      }
    }
    return marker;
  });

  return (
    <div className={cn("relative w-full overflow-hidden rounded-2xl shadow-sm border", dark ? "border-[#242E42]" : "border-gray-200/80", className)} style={{ minHeight: 360 }}>
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={center}
        zoom={12}
        options={mapOptions}
      >
        {dynamicMarkers.map((marker) => (
          <Marker
            key={marker.id}
            position={{ lat: marker.lat, lng: marker.lng }}
            label={{
              text: getMarkerIcon(marker.type),
              fontSize: "20px",
            }}
            title={marker.title || marker.label}
          />
        ))}

        {showCorridor && directionsPath.length > 0 && (
          <Polyline
            path={directionsPath}
            options={{
              strokeColor: dark ? "#00E5FF" : "#2563EB",
              strokeOpacity: 0.8,
              strokeWeight: 5,
            }}
          />
        )}
      </GoogleMap>
    </div>
  );
}

const lightStyle = [
  { featureType: "all", elementType: "geometry", stylers: [{ color: "#f5f5f5" }] },
  { featureType: "all", elementType: "labels.text.fill", stylers: [{ color: "#616161" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#c9c9c9" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#ffffff" }] }
];

const darkStyle = [
  { featureType: "all", elementType: "geometry", stylers: [{ color: "#242f3e" }] },
  { featureType: "all", elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#17263c" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#38414e" }] }
];
