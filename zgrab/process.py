import os
import json
import pika
import subprocess
import threading
import queue
from pymongo import MongoClient
from datetime import datetime
import logging
import select

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create a queue for IP addresses
ip_queue = queue.Queue()


def read_zgrab_output(process, collection):
    logging.info("Starting to read ZGrab output")
    while True:
        ready, _, _ = select.select([process.stdout], [], [], 1.0)
        if ready:
            line = process.stdout.readline()
            if not line:
                logging.debug("ZGrab output ended")
                break  # EOF
            line = line.strip()
            if line:
                try:
                    result = json.loads(line)
                    logging.info(f"Received ZGrab output: {result}")

                    result["data"]["http"]["timestamp"] = datetime.strptime(
                        result["data"]["http"]["timestamp"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    ip = result.pop("ip")

                    # Store data in MongoDB
                    collection.update_one(
                        {"saddr": ip}, {"$set": dict(result)}, upsert=True
                    )
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse JSON: {line}")
        else:
            logging.debug("No output from ZGrab in the last second")


def write_to_zgrab(process):
    logging.info("Starting to write IPs to ZGrab")
    while True:
        try:
            ip = ip_queue.get(timeout=1)
            logging.debug(f"Writing IP to ZGrab: {ip}")
            process.stdin.write(f"{ip}\n")
            process.stdin.flush()
        except queue.Empty:
            continue
        except BrokenPipeError:
            logging.error("Broken pipe when writing to ZGrab")
            break


def main(rabbitmq_url: str | None = None, mongodb_uri: str | None = None):
    logging.info("Starting main function")

    # Set up MongoDB connection
    mongodb_uri = mongodb_uri or os.environ.get(
        "MONGO_URL", "mongodb://localhost:27017/"
    )
    logging.info(f"Connecting to MongoDB: {mongodb_uri}")
    client = MongoClient(mongodb_uri)
    db = client["zmap_results"]
    collection = db["scans"]

    # Start zgrab2 subprocess
    command = [
        "zgrab2",
        "http",
        #'--timeout=5',
        #'--output-file=-'  # Output to stdout
    ]

    logging.info(f"Starting ZGrab2 process: {' '.join(command)}")
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,  # Line-buffered
    )

    # Start threads to read from and write to zgrab2
    logging.info("Starting ZGrab output reading thread")
    stdout_thread = threading.Thread(
        target=read_zgrab_output, args=(process, collection)
    )
    stdout_thread.daemon = True
    stdout_thread.start()

    logging.info("Starting ZGrab input writing thread")
    stdin_thread = threading.Thread(target=write_to_zgrab, args=(process,))
    stdin_thread.daemon = True
    stdin_thread.start()

    # Setup RabbitMQ connection
    rabbitmq_url = rabbitmq_url or os.environ.get(
        "RABBITMQ_URL", "amqp://localhost:5672/"
    )
    logging.info(f"Connecting to RabbitMQ: {rabbitmq_url}")
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="zmap_results")

    def callback(ch, method, properties, body):
        logging.debug(f"Received message: {body}")
        data = json.loads(body)

        ip = data.get("saddr")
        sport = data.get("sport")

        # if sport != 80:
        #    return

        ip_queue.put(ip)
        logging.info(
            f"Queueing banner scan for {ip}. Total Queue Size: {ip_queue.qsize()}"
        )

    channel.basic_consume(
        queue="zmap_results", on_message_callback=callback, auto_ack=True
    )

    logging.info("Waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info("Interrupted")
    finally:
        process.stdin.close()
        process.terminate()
        stdout_thread.join()
        stdin_thread.join()
        connection.close()


if __name__ == "__main__":
    main()
