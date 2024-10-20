import os
import re
import csv
from datetime import datetime, timedelta
from pymongo import MongoClient

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class VulnerabilityScanner:
    def __init__(self, database_dir="dbs"):
        self.database_dir = database_dir
        self.databases = [
            {
                "name": "VulDB",
                "file": "scipvuldb.csv",
                "url": "https://vuldb.com",
                "link": "https://vuldb.com/id.{id}",
            },
            {
                "name": "MITRE CVE",
                "file": "cve.csv",
                "url": "https://cve.mitre.org",
                "link": "https://cve.mitre.org/cgi-bin/cvename.cgi?name={id}",
            },
            {
                "name": "SecurityFocus",
                "file": "securityfocus.csv",
                "url": "https://www.securityfocus.com/bid/",
                "link": "https://www.securityfocus.com/bid/{id}",
            },
            {
                "name": "IBM X-Force",
                "file": "xforce.csv",
                "url": "https://exchange.xforce.ibmcloud.com",
                "link": "https://exchange.xforce.ibmcloud.com/vulnerabilities/{id}",
            },
            {
                "name": "Exploit-DB",
                "file": "exploitdb.csv",
                "url": "https://www.exploit-db.com",
                "link": "https://www.exploit-db.com/exploits/{id}",
            },
            {
                "name": "OpenVAS (Nessus)",
                "file": "openvas.csv",
                "url": "http://www.openvas.org",
                "link": "https://www.tenable.com/plugins/nessus/{id}",
            },
            {
                "name": "SecurityTracker",
                "file": "securitytracker.csv",
                "url": "https://www.securitytracker.com",
                "link": "https://www.securitytracker.com/id/{id}",
            },
            {
                "name": "OSVDB",
                "file": "osvdb.csv",
                "url": "http://www.osvdb.org",
                "link": "http://www.osvdb.org/{id}",
            },
        ]

    def scan(self, product, version):
        results = []
        for db in self.databases:
            findings = self.find_vulnerabilities(product, version, db["file"])
            if findings:
                results.append(
                    {"database": db["name"], "url": db["url"], "findings": findings}
                )

        return results

    def find_vulnerabilities(self, product, version, db_file):
        vulnerabilities = []
        db_path = os.path.join(self.database_dir, db_file)
        with open(db_path, mode="r", encoding="ISO-8859-1") as file:
            reader = csv.reader(file, delimiter=";")
            for row in reader:
                vuln_id, vuln_title = row[0], row[1]
                if self.match_product(vuln_title, product) and self.match_version(
                    vuln_title, version
                ):
                    vulnerabilities.append(
                        {"id": vuln_id, "title": vuln_title, "version": version}
                    )
        return vulnerabilities

    def match_product(self, vuln_title, product):
        product_keywords = product.lower().split()
        for keyword in product_keywords:
            if keyword in vuln_title.lower():
                return True
        return False

    def match_version(self, vuln_title, version):
        version_pattern = re.compile(rf"\b{re.escape(version)}\b")
        return bool(re.search(version_pattern, vuln_title))


if __name__ == "__main__":
    # Set up MongoDB connection
    mongodb_uri = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
    client = MongoClient(mongodb_uri)
    db = client["zmap_results"]
    scan_collection = db["scans"]
    cve_collection = db["cve"]

    # Initiate the vulnerability scanner
    scanner = VulnerabilityScanner()

    # Regular expressions to extract software and version
    software_version_pattern = re.compile(r"(\w+)[/ ]([\d.]+)")

    # Get servers with 'server' header
    servers = scan_collection.find(
        {
            "data.http.result.response.headers.server": {"$exists": True},
            "$or": [
                {
                    "apps.vuln-finder.last_scan": {
                        "$lt": datetime.now() - timedelta(days=7)
                    }
                },
                {"apps.vuln-finder.last_scan": {"$exists": False}},
            ],
        }
    )

    logging.info(f"Scanning servers for vulnerabilities")

    for server in servers:
        server_header = server["data"]["http"]["result"]["response"]["headers"][
            "server"
        ][0]

        # Extract software name and version from the server header
        match = software_version_pattern.search(server_header)
        if not match:
            continue

        software, version = match.groups()
        logging.debug(f"Checking vulnerabilities for {software} {version}...")

        # Query the vulnerability database
        vulnerabilities = scanner.scan(software, version)

        if vulnerabilities:
            logging.info(
                f"Found {len(vulnerabilities)} vulnerabilities for {software} {version}"
            )

            scan_collection.update_one(
                {"saddr": server["saddr"], "sport": server["sport"]},
                {
                    "$set": {
                        "vulnerabilities": vulnerabilities,
                        "apps.vuln-finder.last_scan": datetime.now(),
                    }
                },
            )
