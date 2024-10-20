import os
import logging
import geoip2.database
import geoip2.errors
from pymongo import MongoClient


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


GEOIP_DB_PATH = "./geolite2-city.mmdb"


# Set up MongoDB connection
mongodb_uri = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(mongodb_uri)
db = client["zmap_results"]
scan_collection = db["scans"]

# Load the GeoIP database
reader = geoip2.database.Reader(GEOIP_DB_PATH)

# Get untagged servers
servers = scan_collection.find({"country": {"$exists": False}})

# Tag servers with country code
for server in list(servers):
    ip = server["saddr"]
    try:
        response = reader.city(ip)
        iso_code = response.country.iso_code

        if not iso_code:
            continue

        scan_collection.update_one(
            {"saddr": ip},
            {"$set": {"country": iso_code}},
        )

    except geoip2.errors.AddressNotFoundError:
        logging.warning(f"IP {ip} not found in database")
