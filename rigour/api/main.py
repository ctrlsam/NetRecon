from common.database.mongodb import Database
from common.types import DBHost
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from pydantic import ValidationError
from utils import build_facet_stages, parse_query_filters, process_host_document

db = Database()

router = APIRouter()


class PaginationParams:
    def __init__(
        self, skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)
    ):
        self.skip = skip
        self.limit = limit


@router.get("/host/search", response_model=list[DBHost])
async def get_hosts(
    query: str | None = Query(
        default=None,
        description="Search query with optional filters in 'filter:value' format",
    ),
    facet: str | None = Query(
        default=None,
        description="Comma-separated list of properties for faceted search, optionally\
            with counts (e.g., 'country:100')",
    ),
    pagination: PaginationParams = Depends(),
):
    """
    Search using query syntax and use facets to get summary information for different
    properties.

    Args:
        query: Shodan search query. The provided string is used to search the database
            of banners in Shodan, with the additional option to provide filters inside
            the search query using a "filter:value" format. For example, the following
            search query would find Apache Web servers located in Germany:
            "apache country:DE".

        facet: A comma-separated list of properties to get summary information on.
            Property names can also be in the format of "property:count", where "count"
            is the number of facets that will be returned for a property (i.e.
            "country:100" to get the top 100 countries for a search query).
    """
    pipeline = []

    # Build match stage from query if provided
    if query:
        match_conditions = parse_query_filters(query)
        pipeline.append({"$match": match_conditions})

    # if facet:
    #  TODO: Add facet stages to pipeline

    else:
        # Without facets, we can use a simpler pipeline
        pipeline.extend([{"$skip": pagination.skip}, {"$limit": pagination.limit}])

        # Execute aggregation
        return list(db.scans.aggregate(pipeline))


@router.get("/host/count")
async def get_hosts_count(
    query: str | None = Query(
        default=None,
        description="Search query with optional filters in 'filter:value' format",
    ),
    facet: str | None = Query(
        default=None,
        description="Comma-separated list of properties for faceted search, optionally\
            with counts (e.g., 'country:100')",
    ),
) -> dict:
    """
    This method behaves identical to "/host/search" with the only difference
    that this method does not return any host results, it only returns the total
    number of results that matched the query and any facet information that was
    requested.

    Args:
        query: The provided string is used to search the database of banners, with
            the additional option to provide filters inside the search query using
            a "filter:value" format. For example, the following search query would
            find Apache Web servers located in Germany: "location.country_name:DE".

        facet: A comma-separated list of properties to get summary information on.
            Property names can also be in the format of "property:count", where "count"
            is the number of facets that will be returned for a property (i.e.
            "country:100" to get the top 100 countries for a search query).

        db: AsyncIOMotorDatabase instance for MongoDB access

    Returns:
        dict: Contains total count and facet information if requested
    """
    pipeline = []

    # Build match stage from query if provided
    if query:
        match_conditions = parse_query_filters(query)
        pipeline.append({"$match": match_conditions})

    # Initialize response structure
    response = {"total": 0, "facets": {}}

    # Add facet stages if facets are requested
    if facet:
        pipeline.append({"$facet": build_facet_stages(facet)})
    else:
        # If no facets requested, just get the count
        pipeline.append({"$count": "total"})

    # Execute aggregation
    result = list(db.scans.aggregate(pipeline))

    if result:
        if facet:
            # Extract results from faceted query
            response["total"] = (
                result[0]["total"][0]["count"] if result[0]["total"] else 0
            )
            # Remove the total from facets before returning
            result[0].pop("total", None)
            response["facets"] = result[0]
        else:
            # Extract results from simple count query
            response["total"] = result[0]["total"]

    return response


@router.get("/host/{ip}", response_model=DBHost)
async def get_host_by_ip(ip: str):
    """
    Get host information by IP address

    Args:
        ip: IP address of the host to retrieve
    """
    host = db.scans.find_one({"ip": ip})

    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    host = process_host_document(host)

    try:
        host_model = DBHost(**host)
    except ValidationError:
        raise HTTPException(status_code=500, detail="Invalid host data")

    return host_model


app = FastAPI(root_path="/api")
app.include_router(router, prefix="/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=1234)
