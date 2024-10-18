import os
import subprocess
import csv
import sys

from pymongo import MongoClient


def main(ip_range: str, ports: str, mongodb_uri: str | None = None):
    # Set up MongoDB connection
    mongodb_uri = mongodb_uri or os.environ.get("MONGO_URL", "mongodb://mongo:27017/")
    client = MongoClient(mongodb_uri)
    db = client['zmap_results']
    collection = db['scans']

    # Define the ZMap command and parameters
    command = [
        'zmap',
        '-p', ports,  # Target port
        ip_range,  # Target IP range
        '--output-fields=saddr,daddr,sport,dport,success,repeat',  # Output fields
        '--output-module=csv',  # Output in CSV format
        '--quiet',  # Suppress status updates
        '--no-header-row'  # Do not output CSV headers
    ]

    try:
        # Run ZMap as a subprocess
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Define the CSV fields
        fields = ['saddr', 'daddr', 'sport', 'dport', 'success', 'repeat']

        # Read and process the output line by line
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            # Parse the CSV line
            reader = csv.reader([line])
            for row in reader:
                data = dict(zip(fields, row))
                # Convert string numbers to integers
                data['sport'] = int(data['sport'])
                data['dport'] = int(data['dport'])
                data['success'] = int(data['success'])
                data['repeat'] = int(data['repeat'])
                # Insert the data into MongoDB
                collection.insert_one(data)

        # Wait for the process to finish and check for errors
        process.wait()
        stderr = process.stderr.read()
        if stderr:
            print(f"Error: {stderr}", file=sys.stderr)

    except Exception as e:
        print(f"Exception occurred: {e}", file=sys.stderr)


if __name__ == '__main__':
    main(ip_range='192.168.1.0/24', ports='22')
