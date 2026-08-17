import type { ScenarioPayload } from "./../hooks/useDigitalTwinState";

export const SCENARIOS_DATASET: ScenarioPayload[] = [
  {
    "incident": {
      "id": "INC-GZ-0001",
      "type": "Road Accident",
      "severity": "high",
      "status": "active",
      "location": "NH-58, Muradnagar",
      "lat": 28.7667,
      "lng": 77.4983,
      "assignedUnit": "AMB-100"
    },
    "ambulance": {
      "id": "AMB-100",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.76310229881448,
      "lng": 77.4999471070783,
      "speed": 55
    },
    "hospital": {
      "id": "HSP-10",
      "name": "Yashoda Hospital",
      "lat": 28.6692,
      "lng": 77.4538,
      "totalIcuBeds": 120,
      "availableIcuBeds": 8,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0002",
      "type": "Fire Emergency",
      "severity": "high",
      "status": "active",
      "location": "Vasundhara Sector 5",
      "lat": 28.6653,
      "lng": 77.3683,
      "assignedUnit": "AMB-101"
    },
    "ambulance": {
      "id": "AMB-101",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.669459532237905,
      "lng": 77.36652431737,
      "speed": 42
    },
    "hospital": {
      "id": "HSP-11",
      "name": "Vasundhara Medical",
      "lat": 28.6622,
      "lng": 77.3698,
      "totalIcuBeds": 60,
      "availableIcuBeds": 4,
      "emergencyLevel": "LOW"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0003",
      "type": "Theft",
      "severity": "medium",
      "status": "active",
      "location": "Raj Nagar",
      "lat": 28.6798,
      "lng": 77.4475,
      "assignedUnit": "AMB-102"
    },
    "ambulance": {
      "id": "AMB-102",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.67770027620573,
      "lng": 77.45151227318031,
      "speed": 44
    },
    "hospital": {
      "id": "HSP-12",
      "name": "Yashoda Hospital",
      "lat": 28.6692,
      "lng": 77.4538,
      "totalIcuBeds": 120,
      "availableIcuBeds": 8,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": false
  },
  {
    "incident": {
      "id": "INC-GZ-0004",
      "type": "Missing Person",
      "severity": "high",
      "status": "active",
      "location": "Vijay Nagar",
      "lat": 28.6366,
      "lng": 77.4231,
      "assignedUnit": "AMB-103"
    },
    "ambulance": {
      "id": "AMB-103",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.634398704590577,
      "lng": 77.4280240559845,
      "speed": 49
    },
    "hospital": {
      "id": "HSP-13",
      "name": "Apollo Clinic",
      "lat": 28.6501,
      "lng": 77.4201,
      "totalIcuBeds": 40,
      "availableIcuBeds": 1,
      "emergencyLevel": "LOW"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0005",
      "type": "Domestic Dispute",
      "severity": "high",
      "status": "active",
      "location": "Sahibabad",
      "lat": 28.665,
      "lng": 77.3488,
      "assignedUnit": "AMB-104"
    },
    "ambulance": {
      "id": "AMB-104",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.663207919444726,
      "lng": 77.34432782675556,
      "speed": 40
    },
    "hospital": {
      "id": "HSP-14",
      "name": "Vasundhara Medical",
      "lat": 28.6622,
      "lng": 77.3698,
      "totalIcuBeds": 60,
      "availableIcuBeds": 4,
      "emergencyLevel": "LOW"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0006",
      "type": "Cyber Fraud",
      "severity": "high",
      "status": "active",
      "location": "Kavinagar",
      "lat": 28.6738,
      "lng": 77.4526,
      "assignedUnit": "AMB-105"
    },
    "ambulance": {
      "id": "AMB-105",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.67342569175036,
      "lng": 77.4552452025271,
      "speed": 53
    },
    "hospital": {
      "id": "HSP-15",
      "name": "Yashoda Hospital",
      "lat": 28.6692,
      "lng": 77.4538,
      "totalIcuBeds": 120,
      "availableIcuBeds": 8,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0007",
      "type": "Chain Snatching",
      "severity": "high",
      "status": "active",
      "location": "Sihani Gate",
      "lat": 28.6749,
      "lng": 77.4332,
      "assignedUnit": "AMB-106"
    },
    "ambulance": {
      "id": "AMB-106",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.67497340780998,
      "lng": 77.42837518420203,
      "speed": 45
    },
    "hospital": {
      "id": "HSP-16",
      "name": "Sarvodaya Hospital",
      "lat": 28.6735,
      "lng": 77.4326,
      "totalIcuBeds": 110,
      "availableIcuBeds": 9,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0008",
      "type": "Public Disturbance",
      "severity": "medium",
      "status": "active",
      "location": "Loni Road",
      "lat": 28.7056,
      "lng": 77.2945,
      "assignedUnit": "AMB-107"
    },
    "ambulance": {
      "id": "AMB-107",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.70841489433919,
      "lng": 77.2986434197594,
      "speed": 40
    },
    "hospital": {
      "id": "HSP-17",
      "name": "Max Hospital",
      "lat": 28.6358,
      "lng": 77.3235,
      "totalIcuBeds": 200,
      "availableIcuBeds": 5,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": false
  },
  {
    "incident": {
      "id": "INC-GZ-0009",
      "type": "Vehicle Theft",
      "severity": "high",
      "status": "active",
      "location": "Crossings Republik",
      "lat": 28.6253,
      "lng": 77.4375,
      "assignedUnit": "AMB-108"
    },
    "ambulance": {
      "id": "AMB-108",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.622368202346074,
      "lng": 77.44140688517108,
      "speed": 52
    },
    "hospital": {
      "id": "HSP-10",
      "name": "Columbia Asia",
      "lat": 28.6322,
      "lng": 77.4578,
      "totalIcuBeds": 90,
      "availableIcuBeds": 3,
      "emergencyLevel": "MEDIUM"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0010",
      "type": "Medical Emergency",
      "severity": "high",
      "status": "active",
      "location": "Indirapuram",
      "lat": 28.6415,
      "lng": 77.3714,
      "assignedUnit": "AMB-109"
    },
    "ambulance": {
      "id": "AMB-109",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.64631870143123,
      "lng": 77.36654673871493,
      "speed": 50
    },
    "hospital": {
      "id": "HSP-11",
      "name": "Atlanta Hospital",
      "lat": 28.6411,
      "lng": 77.3755,
      "totalIcuBeds": 80,
      "availableIcuBeds": 2,
      "emergencyLevel": "MEDIUM"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0011",
      "type": "Burglary",
      "severity": "high",
      "status": "active",
      "location": "Shastri Nagar",
      "lat": 28.6766,
      "lng": 77.4646,
      "assignedUnit": "AMB-110"
    },
    "ambulance": {
      "id": "AMB-110",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.67515334379953,
      "lng": 77.46479550601147,
      "speed": 47
    },
    "hospital": {
      "id": "HSP-12",
      "name": "Yashoda Hospital",
      "lat": 28.6692,
      "lng": 77.4538,
      "totalIcuBeds": 120,
      "availableIcuBeds": 8,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0012",
      "type": "Street Harassment",
      "severity": "high",
      "status": "active",
      "location": "Indirapuram",
      "lat": 28.6415,
      "lng": 77.3714,
      "assignedUnit": "AMB-111"
    },
    "ambulance": {
      "id": "AMB-111",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.646254306242948,
      "lng": 77.37551015309086,
      "speed": 44
    },
    "hospital": {
      "id": "HSP-13",
      "name": "Atlanta Hospital",
      "lat": 28.6411,
      "lng": 77.3755,
      "totalIcuBeds": 80,
      "availableIcuBeds": 2,
      "emergencyLevel": "MEDIUM"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0013",
      "type": "Suspicious Activity",
      "severity": "medium",
      "status": "active",
      "location": "Lohia Nagar",
      "lat": 28.6669,
      "lng": 77.4404,
      "assignedUnit": "AMB-112"
    },
    "ambulance": {
      "id": "AMB-112",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.671237465992398,
      "lng": 77.4406398471448,
      "speed": 49
    },
    "hospital": {
      "id": "HSP-14",
      "name": "Sarvodaya Hospital",
      "lat": 28.6735,
      "lng": 77.4326,
      "totalIcuBeds": 110,
      "availableIcuBeds": 9,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": false
  },
  {
    "incident": {
      "id": "INC-GZ-0014",
      "type": "Road Accident",
      "severity": "high",
      "status": "active",
      "location": "GT Road, Sahibabad",
      "lat": 28.6685,
      "lng": 77.3512,
      "assignedUnit": "AMB-113"
    },
    "ambulance": {
      "id": "AMB-113",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.67101903443966,
      "lng": 77.35543219481806,
      "speed": 52
    },
    "hospital": {
      "id": "HSP-15",
      "name": "Vasundhara Medical",
      "lat": 28.6622,
      "lng": 77.3698,
      "totalIcuBeds": 60,
      "availableIcuBeds": 4,
      "emergencyLevel": "LOW"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0015",
      "type": "Lost Person",
      "severity": "medium",
      "status": "active",
      "location": "Kavinagar",
      "lat": 28.6738,
      "lng": 77.4526,
      "assignedUnit": "AMB-114"
    },
    "ambulance": {
      "id": "AMB-114",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.669548256865166,
      "lng": 77.45351924683159,
      "speed": 55
    },
    "hospital": {
      "id": "HSP-16",
      "name": "Yashoda Hospital",
      "lat": 28.6692,
      "lng": 77.4538,
      "totalIcuBeds": 120,
      "availableIcuBeds": 8,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": false
  },
  {
    "incident": {
      "id": "INC-GZ-0016",
      "type": "Robbery",
      "severity": "high",
      "status": "active",
      "location": "Nehru Nagar",
      "lat": 28.6656,
      "lng": 77.4357,
      "assignedUnit": "AMB-115"
    },
    "ambulance": {
      "id": "AMB-115",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.662425910141014,
      "lng": 77.434247796888,
      "speed": 46
    },
    "hospital": {
      "id": "HSP-17",
      "name": "Sarvodaya Hospital",
      "lat": 28.6735,
      "lng": 77.4326,
      "totalIcuBeds": 110,
      "availableIcuBeds": 9,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0017",
      "type": "Traffic Violation",
      "severity": "low",
      "status": "active",
      "location": "Indirapuram",
      "lat": 28.6415,
      "lng": 77.3714,
      "assignedUnit": "AMB-116"
    },
    "ambulance": {
      "id": "AMB-116",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.641303698623567,
      "lng": 77.37353597485846,
      "speed": 57
    },
    "hospital": {
      "id": "HSP-10",
      "name": "Atlanta Hospital",
      "lat": 28.6411,
      "lng": 77.3755,
      "totalIcuBeds": 80,
      "availableIcuBeds": 2,
      "emergencyLevel": "MEDIUM"
    },
    "triggerGreenCorridor": false
  },
  {
    "incident": {
      "id": "INC-GZ-0018",
      "type": "Assault",
      "severity": "high",
      "status": "active",
      "location": "Vijay Nagar",
      "lat": 28.6366,
      "lng": 77.4231,
      "assignedUnit": "AMB-117"
    },
    "ambulance": {
      "id": "AMB-117",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.63824872882208,
      "lng": 77.42474023506385,
      "speed": 52
    },
    "hospital": {
      "id": "HSP-11",
      "name": "Apollo Clinic",
      "lat": 28.6501,
      "lng": 77.4201,
      "totalIcuBeds": 40,
      "availableIcuBeds": 1,
      "emergencyLevel": "LOW"
    },
    "triggerGreenCorridor": true
  },
  {
    "incident": {
      "id": "INC-GZ-0019",
      "type": "Illegal Parking",
      "severity": "low",
      "status": "active",
      "location": "Sahibabad",
      "lat": 28.665,
      "lng": 77.3488,
      "assignedUnit": "AMB-118"
    },
    "ambulance": {
      "id": "AMB-118",
      "callsign": "ALS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.666411742762786,
      "lng": 77.34828676997306,
      "speed": 41
    },
    "hospital": {
      "id": "HSP-12",
      "name": "Vasundhara Medical",
      "lat": 28.6622,
      "lng": 77.3698,
      "totalIcuBeds": 60,
      "availableIcuBeds": 4,
      "emergencyLevel": "LOW"
    },
    "triggerGreenCorridor": false
  },
  {
    "incident": {
      "id": "INC-GZ-0020",
      "type": "Noise Complaint",
      "severity": "low",
      "status": "active",
      "location": "Raj Nagar",
      "lat": 28.6798,
      "lng": 77.4475,
      "assignedUnit": "AMB-119"
    },
    "ambulance": {
      "id": "AMB-119",
      "callsign": "BLS Unit",
      "driver": "AI Dispatch",
      "status": "dispatched",
      "lat": 28.679379318860892,
      "lng": 77.44628977897867,
      "speed": 52
    },
    "hospital": {
      "id": "HSP-13",
      "name": "Yashoda Hospital",
      "lat": 28.6692,
      "lng": 77.4538,
      "totalIcuBeds": 120,
      "availableIcuBeds": 8,
      "emergencyLevel": "HIGH"
    },
    "triggerGreenCorridor": false
  }
];
