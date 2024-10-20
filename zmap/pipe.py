import logging
import os
from datetime import datetime
import json
import subprocess
import pika
from pymongo import MongoClient


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def run_zmap(ports: str, callback: callable):
    # Define the ZMap command and parameters
    command = [
        "zmap",
        "-p",
        ports,  # Target ports
        "--output-module=json",  # Output in CSV format
        "--quiet",  # Suppress status updates
        #'--no-header-row',        # Do not output CSV headers
        "--rate=100",
        "--seed=12515112",
        #'--bandwidth=1Mbps',
    ]

    # Run ZMap as a subprocess
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )

    # Read and process the output line by line
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue

        data = json.loads(line)

        # Add source port when only one port is scanned
        if "," not in ports and "-" not in ports:
            data["sport"] = int(ports)

        elif "sport" not in data:
            continue  # Skip if source port is not available TODO: research why this occurs

        callback(data)

    # Wait for the process to finish and check for errors
    process.wait()
    stderr = process.stderr.read()
    if stderr:
        logging.error(stderr)


def main(ports: str, mongodb_uri: str | None = None, rabbitmq_url: str | None = None):
    # Set up MongoDB connection
    mongodb_uri = mongodb_uri or os.environ.get(
        "MONGO_URL", "mongodb://localhost:27017/"
    )
    client = MongoClient(mongodb_uri)
    db = client["zmap_results"]
    collection = db["scans"]

    # Setup RabbitMQ connection
    rabbitmq_url = rabbitmq_url or os.environ.get(
        "RABBITMQ_URL", "amqp://localhost:5672/"
    )
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="zmap_results")

    def callback(result: dict):
        logging.info(result)

        result_with_timestamp = dict(result)
        result_with_timestamp["timestamp"] = datetime.now()

        # Insert the data into the MongoDB collectiom
        collection.update_one(
            {"saddr": result["saddr"], "sport": result["sport"]},
            {"$set": result_with_timestamp},
            upsert=True,
        )

        # Send the data to the RabbitMQ queue
        message = json.dumps(result)
        channel.basic_publish(exchange="", routing_key="zmap_results", body=message)

    # Run ZMap and pass the callback function
    run_zmap(ports, callback)

    # Close the MongoDB connection
    client.close()

    # Close the RabbitMQ connection
    connection.close()


if __name__ == "__main__":
    main(ports="80,443,8080,8443,8888")
