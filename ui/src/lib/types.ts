export type Host = {
    timestamp: Date;
    saddr: string;
    scans: {
        sport: number;
        data: object | null;
        country: string | null;
        apps: object | null;
    }[];
};

export type Hosts = {
    hosts: Host[];
    top_ports: {
        value: number;
        count: number;
    }[];
    top_countries: {
        value: string;
        count: number;
    }[];
    total: number;
}

export type Credential = {
    saddr: string;
    name: string;
    sport: number;
    url: string;
    confidence: string;
    value: string;
}