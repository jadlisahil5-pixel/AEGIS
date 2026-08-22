# Spring Boot Integration Guidance

This document outlines how the Spring Boot backend should consume the AEGIS-AI FastAPI emergency services.

---

## 1. System Integration Architecture

The Spring Boot application acts strictly as a **REST client / consumer** of the AEGIS-AI FastAPI endpoints. It does **not** duplicate logic, run YOLO inference, perform severity classifications, or maintain routing tables.

```
React Frontend (UI)
        |
        | HTTP REST
        ↓
Spring Boot Backend (Orchestration/User Mgmt/DB)
        |
        | HTTP REST (RestTemplate / WebClient)
        ↓
AEGIS-AI FastAPI Backend (AI recommendation, YOLO, CCTV Pipeline)
```

---

## 2. Spring Boot Best Practices & Recommendations

1.  **Configure API Clients**: Use `WebClient` or `RestTemplate` configured with reasonable connect and read timeouts.
    - Video upload processing `/vision/emergency/process` involves frame reading, YOLO detection, and orchestration. It is recommended to set the read timeout to at least **15–30 seconds** depending on the average video duration and server hardware.
2.  **Pass-through Geolocation Parameters**: Ensure coordinates and camera fields are mapped directly to FastAPI form parameters without hardcoding dummy fallbacks (e.g. `(0,0)`). Allow `null` coordinate values when genuinely unavailable, letting the AEGIS-AI backend return fallback orchestration statuses naturally.
3.  **Consume Full JSON Payload**: Do not parse only parts of the orchestrator or pipeline responses. Forward the entire returned JSON structure—especially the `reasoning` block and `decision_trace` list—to the React frontend, allowing the UI to display the explainability trace fully.

---

## 3. Core Integration Flows

### Flow A: CCTV Footage Ingestion & Analysis
This flow is triggered when the Spring Boot backend receives camera footage uploads from the CCTV monitoring network.

```
CCTV Camera / Client Upload
         ↓
Spring Boot (Controller endpoint receiving MultipartFile)
         ↓
Spring Boot constructs a Multipart Body (MultipartFile + optional camera metadata Form Parameters)
         ↓
POST http://aegis-ai-service/vision/emergency/process
         ↓
AEGIS-AI processes frames, detects events, and coordinates resources
         ↓
Spring Boot receives VisionEmergencyProcessResponse JSON
         ↓
Spring Boot persists incident record (if incident_created is true)
         ↓
Spring Boot sends JSON response to React frontend
```

#### Spring Boot Java Example:
```java
@RestController
@RequestMapping("/api/cctv")
public class CctvController {

    @Autowired
    private RestTemplate restTemplate;

    @Value("${aegis.ai.url}")
    private String aegisAiUrl;

    @PostMapping(value = "/process", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<String> processVideo(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "camera_id", required = false) String cameraId,
            @RequestParam(value = "latitude", required = false) Double latitude,
            @RequestParam(value = "longitude", required = false) Double longitude
    ) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", file.getResource());
        if (cameraId != null) body.add("camera_id", cameraId);
        if (latitude != null) body.add("latitude", latitude.toString());
        if (longitude != null) body.add("longitude", longitude.toString());

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        String endpoint = aegisAiUrl + "/vision/emergency/process";
        ResponseEntity<String> response = restTemplate.postForEntity(endpoint, requestEntity, String.class);

        return ResponseEntity.ok(response.getBody());
    }
}
```

---

### Flow B: Citizen Emergency Manual Reporting
This flow is used when a citizen manually reports an incident via phone or web form.

```
Citizen Report (incident type, location coordinates, hazards)
         ↓
Spring Boot
         ↓
POST http://aegis-ai-service/agents/orchestrate
         ↓
AEGIS-AI performs Incident Normalization, Severity, Command, Resource allocation, and Trace
         ↓
Spring Boot consumes OrchestrationResponse JSON
         ↓
Spring Boot coordinates response resources and notifies operators via React
```

#### Spring Boot Java Example:
```java
@Service
public class EmergencyOrchestrationService {

    @Autowired
    private RestTemplate restTemplate;

    @Value("${aegis.ai.url}")
    private String aegisAiUrl;

    public OrchestrationResponse orchestrateEmergency(EmergencyReport report) {
        String endpoint = aegisAiUrl + "/agents/orchestrate";
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<EmergencyReport> entity = new HttpEntity<>(report, headers);
        
        return restTemplate.postForObject(endpoint, entity, OrchestrationResponse.class);
    }
}
```
