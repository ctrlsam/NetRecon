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
    def get_networks(default: str = "10.0.0.0/8") -> str:
        return os.environ.get("NETWORKS", default)

    @staticmethod
    def get_ports(default: str = "80") -> str:
        return os.environ.get("PORTS", default)

    @staticmethod
    def get_scan_collection() -> str:
        return "scans"
