from common.config import Config
from pymongo import MongoClient


class Database:
    def __init__(self, uri: str | None = None, db: str | None = None):
        self.client = MongoClient(uri or Config.get_mongo_uri())
        self.db = self.client[db or Config.get_mongo_db()]
        self.scans = self.db[Config.get_scan_collection()]

    def close(self):
        self.client.close()
