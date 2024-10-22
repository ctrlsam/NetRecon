/*{
    "_id": {
      "$oid": "671708b75aed5f4a9484ce2b"
    },
    "ip": "179.189.19.221",
    "first_seen": {
      "$date": "2024-10-22T02:06:47.788Z"
    },
    "location": {
      "country_code": "SA",
      "continent_name": "South America",
      "country_name": "Brazil",
      "accuracy_radius": 5,
      "latitude": -23.947,
      "longitude": -48.8383
    },
    "updated_at": {
      "$date": "2024-10-22T02:06:47.788Z"
    },
    "banners": {
      "ssh": {
        "service": "ssh",
        "port": 22,
        "data": {
          "status": "connection-timeout",
          "protocol": "ssh",
          "result": {},
          "timestamp": "2024-10-22T02:06:47Z",
          "error": "dial tcp 179.189.19.221:22: connect: connection refused"
        }
      }
    }
} */

export type Location = {
    country_code: string;
    continent_name: string;
    country_name: string;
    accuracy_radius: number;
    latitude: number;
    longitude: number;
}

export type Banner = {
    service: string;
    port: number;
    data: {
        status: string;
        protocol: string;
        result: object;
        timestamp: string;
        error: string;
    }
}

export type Vulnerability = {
    name: string;
    title: string;
    version: string;
    link: string;
}

export type Host = {
    ip: string;
    location: Location;
    first_seen: string;
    updated_at: string;
    banners: {
        [key: string]: Banner;
    };
    vulnerabilities: Vulnerability[];
};

export type Count = {
  total: number,
  facets: {
    [key: string]: {
      _id: string,
      count: number
    }[]
  }
}
