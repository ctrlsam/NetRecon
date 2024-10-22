import csv
import json
import os
import re
from typing import TypedDict

from common.types import Vulnerability


class ManifestDB(TypedDict):
    name: str
    file: str
    url: str
    link: str


class VulnerabilityDetector:
    def __init__(
        self, database_dir: str = "dbs", manifest_file: str = "manifest.json"
    ) -> None:
        self.database_dir = database_dir
        self.databases = [ManifestDB(**db) for db in json.load(open(manifest_file))]

    def scan(self, product: str, version: str) -> list[Vulnerability]:
        results = []
        for db in self.databases:
            results += self.find_vulnerabilities(product, version, db)

        return results

    def find_vulnerabilities(
        self, product: str, version: str, db: ManifestDB
    ) -> list[Vulnerability]:
        vulnerabilities = []
        db_path = os.path.join(self.database_dir, db["file"])

        with open(db_path, encoding="ISO-8859-1") as file:
            reader = csv.reader(file, delimiter=";")
            for row in reader:
                vuln_id, vuln_title = row[0], row[1]
                if self.match_product(vuln_title, product) and self.match_version(
                    vuln_title, version
                ):
                    vulnerabilities.append(
                        Vulnerability(
                            name=vuln_id,
                            title=vuln_title,
                            version=version,
                            link=db["link"].replace("{id}", vuln_id),
                        )
                    )

        return vulnerabilities

    def match_product(self, vuln_title: str, product: str) -> bool:
        product_keywords = product.lower().split()
        for keyword in product_keywords:
            if keyword in vuln_title.lower():
                return True
        return False

    def match_version(self, vuln_title: str, version: str) -> bool:
        version_pattern = re.compile(rf"\b{re.escape(version)}\b")
        return bool(re.search(version_pattern, vuln_title))
