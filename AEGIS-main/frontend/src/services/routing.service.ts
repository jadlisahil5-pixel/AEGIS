import { config } from "@/config/env";
import { apiRequest } from "./api-client";
import type { RouteComputeRequest, RouteComputeResponse } from "./types";

const BASE = `${config.emergencyApiUrl}/api/v1/routes`;

// Real Ghaziabad routing, proxied through emergency-service to the Google
// Routes API. The Google API key lives only on the backend — this call
// never touches Google directly, so no key is exposed to the browser.
export const routingService = {
  compute(request: RouteComputeRequest) {
    return apiRequest<RouteComputeResponse>(`${BASE}/compute`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  },
};
