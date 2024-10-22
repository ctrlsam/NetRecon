def process_host_document(doc) -> dict:
    """
    Process a MongoDB document to remove the _id field and return a dictionary.
    """
    doc = dict(doc)
    doc.pop("_id", None)  # Remove MongoDB's _id field
    return doc


def parse_query_filters(query: str) -> dict:
    """
    Parse the query string to extract filters and build MongoDB match conditions.

    Args:
        query: Query string with optional filters in 'filter:value' format

    Returns:
        dict: MongoDB match conditions
    """
    conditions = {}

    # Split query into parts by whitespace, preserving quoted strings
    import shlex

    query_parts = shlex.split(query)

    for part in query_parts:
        if ":" in part:
            field, value = part.split(":", 1)
            # Handle special cases and type conversion as needed
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            conditions[field] = value
        else:
            # Add text search condition for non-filter parts
            if "text" not in conditions:
                conditions["text"] = {"$search": part}
            else:
                # Append to existing text search
                conditions["text"]["$search"] += f" {part}"

    return conditions


def build_facet_stages(facet: str | None = None) -> dict:
    """
    Build MongoDB facet stages from facet parameter.

    Args:
        facet: Comma-separated list of properties for faceted search

    Returns:
        dict: Facet stages for MongoDB aggregation pipeline
    """
    if not facet:
        return {}

    facet_stages = {"total": [{"$count": "count"}]}

    for facet_item in facet.split(","):
        field_parts = facet_item.strip().split(":")
        field_name = field_parts[0]
        limit = int(field_parts[1]) if len(field_parts) > 1 else 10

        # Handle nested fields using $getField
        group_field = field_name
        if "." in field_name:
            field_parts = field_name.split(".")
            group_field = {
                "$getField": {
                    "field": field_parts[-1],
                    "input": {
                        "$getField": {"field": field_parts[0], "input": "$$ROOT"}
                    },
                }
            }
        else:
            group_field = f"${field_name}"

        facet_stages[field_name.replace(".", "_")] = [  # type: ignore
            {"$group": {"_id": group_field, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]

    return facet_stages
