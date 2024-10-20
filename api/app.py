from collections import Counter
import json
import os
from fastapi import APIRouter, FastAPI, HTTPException, Query, Depends

from pydantic import BaseModel
from pymongo import MongoClient


router = APIRouter()

# MongoDB connection
mongodb_uri = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(mongodb_uri)
db = client.zmap_results


class Credential(BaseModel):
    saddr: str
    name: str
    sport: int
    url: str
    confidence: str
    value: str


class ScanResult(BaseModel):
    saddr: str
    sport: int
    data: dict | None = None
    apps: dict | None = None
    country: str | None = None


class HostAggregate(BaseModel):
    saddr: str
    credentials: list[Credential]
    scans: list[ScanResult]


class HostsResult(BaseModel):
    hosts: list[HostAggregate]
    top_countries: list[dict]
    top_ports: list[dict]
    total: int


class PaginationParams:
    def __init__(
        self, skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)
    ):
        self.skip = skip
        self.limit = limit


# Helper functions
def get_credential(saddr: str) -> list[Credential]:
    results = db.credentials.find({"saddr": saddr}, {"_id": 0})
    return [Credential(**doc) for doc in list(results)]


def get_scans(saddr: str) -> list[ScanResult]:
    results = db.scans.find({"saddr": saddr}, {"_id": 0})
    return [ScanResult(**doc) for doc in list(results)]


# Routes
@router.get("/hosts", response_model=HostsResult)
async def get_hosts(
    country: str | None = None,
    port: int | None = None,
    pagination: PaginationParams = Depends(),
):
    pipeline = []

    # Match stage
    match_stage = {}
    if country:
        match_stage["country"] = country
    if port:
        match_stage["sport"] = port

    if match_stage:
        pipeline.append({"$match": match_stage})

    # Group by saddr
    pipeline.extend(
        [
            {
                "$facet": {
                    "hosts": [
                        {
                            "$group": {
                                "_id": "$saddr",
                                "saddr": {"$first": "$saddr"},
                                "scans": {"$push": "$$ROOT"},
                            }
                        },
                        {
                            "$lookup": {
                                "from": "credentials",
                                "localField": "saddr",
                                "foreignField": "saddr",
                                "as": "credentials",
                            }
                        },
                        # Remove _id fields using $$REMOVE
                        {
                            "$addFields": {
                                "scans": {
                                    "$map": {
                                        "input": "$scans",
                                        "as": "scan",
                                        "in": {
                                            "$mergeObjects": [
                                                "$$scan",
                                                {"_id": "$$REMOVE"},
                                            ]
                                        },
                                    }
                                },
                                "credentials": {
                                    "$map": {
                                        "input": "$credentials",
                                        "as": "credential",
                                        "in": {
                                            "$mergeObjects": [
                                                "$$credential",
                                                {"_id": "$$REMOVE"},
                                            ]
                                        },
                                    }
                                },
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "saddr": 1,
                                "scans": 1,
                                "credentials": 1,
                            }
                        },
                        {"$skip": pagination.skip},
                        {"$limit": pagination.limit},
                    ],
                    "top_countries": [
                        {"$group": {"_id": "$country", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 5},
                        {"$project": {"_id": 0, "value": "$_id", "count": 1}},
                    ],
                    "top_ports": [
                        {"$group": {"_id": "$sport", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 5},
                        {"$project": {"_id": 0, "value": "$_id", "count": 1}},
                    ],
                    "total": [{"$group": {"_id": "$saddr"}}, {"$count": "total"}],
                }
            },
            {
                # Flatten the total array into a scalar field
                "$addFields": {"total": {"$arrayElemAt": ["$total.total", 0]}}
            },
        ]
    )

    results = db.scans.aggregate(pipeline)
    results = list(results)[0]

    print(len(results))

    return results


@router.get("/hosts/{ip}", response_model=HostAggregate)
async def get_host_by_ip(ip: str):
    credentials = get_credential(ip)
    scans = get_scans(ip)

    if not credentials and not scans:
        raise HTTPException(status_code=404, detail="Host not found")

    return HostAggregate(saddr=ip, credentials=credentials, scans=scans)


@router.get("/credentials", response_model=list[Credential])
async def get_credentials(pagination: PaginationParams = Depends()):
    results = (
        db.credentials.find({}, {"_id": 0})
        .skip(pagination.skip)
        .limit(pagination.limit)
    )
    return [Credential(**doc) for doc in list(results)]


@router.get("/search")
async def search(query: str, pagination: PaginationParams = Depends()):
    pipeline = [
        {"$match": {"$text": {"$search": query}}},
        {"$skip": pagination.skip},
        {"$limit": pagination.limit},
    ]

    credentials = db.credentials.aggregate(pipeline)
    scans = db.scans.aggregate(pipeline)

    return {"credentials": list(credentials), "scans": list(scans)}


if __name__ == "__main__":
    app = FastAPI(root_path="/api")
    app.include_router(router, prefix="/v1")

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=1234)
