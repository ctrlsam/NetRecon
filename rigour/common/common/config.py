import os


class Config:
    @staticmethod
    def get_mongo_uri(default: str = "mongodb://localhost:27017") -> str:
        return os.environ.get("MONGO_URL", default)

    @staticmethod
    def get_mongo_db(default: str = "rigour") -> str:
        return os.environ.get("MONGO_DB", default)

    @staticmethod
    def get_rabbitmq_uri(default: str = "amqp://localhost:5672/") -> str:
        return os.environ.get("RABBITMQ_URL", default)

    @staticmethod
    def get_scan_collection() -> str:
        return "scans"
