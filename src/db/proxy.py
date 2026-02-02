import socket
import subprocess
import sys
import time
from threading import Event, Thread

import boto3

from libs.utils.log import get_logger

REMOTE_PORT = 5432
LOCAL_PORT = 5432

# Ping connection every interval to avoid idle connection timeout
KEEP_ALIVE_INTERVAL_SECONDS = 300

log = get_logger(logs_to_file=True, logs_to_console=True)


def get_instance_id():
    """
    Return the first running EC2 instance ID found in this account/region.
    """
    ec2 = boto3.client("ec2")
    resp = ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
    for res in resp.get("Reservations", []):
        for inst in res.get("Instances", []):
            return inst["InstanceId"]
    log.error("No running EC2 instances found.")
    sys.exit(1)


def get_db_host():
    """
    Return the endpoint address of the first RDS instance.
    """
    rds = boto3.client("rds")
    resp = rds.describe_db_instances()
    dbs = resp.get("DBInstances", [])
    if not dbs:
        log.error("No RDS instances found.")
        sys.exit(1)
    return dbs[0]["Endpoint"]["Address"]


def start_ssm_tunnel(instance_id: str, db_host: str, remote_port: int, local_port: int):
    """
    Launch aws ssm start-session for port forwarding.
    """
    cmd = [
        "aws",
        "ssm",
        "start-session",
        "--target",
        instance_id,
        "--document-name",
        "AWS-StartPortForwardingSessionToRemoteHost",
        "--parameters",
        f"host=[{db_host}],portNumber=[{remote_port}],localPortNumber=[{local_port}]",
    ]
    return subprocess.Popen(cmd)


def keep_alive_socket(local_port: int, stop_event: Event, interval: int = 300):
    while not stop_event.is_set():
        time.sleep(interval)

        try:
            with socket.create_connection(("localhost", local_port), timeout=5):
                log.info("Pinged connection")
                pass
        except Exception:
            pass


def main():
    stop_event = Event()

    while True:
        try:
            log.info("Discovering resources…")
            instance_id = get_instance_id()
            db_host = get_db_host()
            log.info(f"EC2 instance: {instance_id}")
            log.info(f"RDS endpoint: {db_host}:{REMOTE_PORT}")

            log.info("Starting port-forwarding session…")
            session_proc = start_ssm_tunnel(instance_id, db_host, REMOTE_PORT, LOCAL_PORT)

            stop_event.clear()
            keep_alive_thread = Thread(
                target=keep_alive_socket,
                args=(LOCAL_PORT, stop_event, KEEP_ALIVE_INTERVAL_SECONDS),
                daemon=True,
            )
            keep_alive_thread.start()

            session_proc.wait()
            log.warning("Session exited; restarting in 3s…")
            stop_event.set()
            time.sleep(3)

        except KeyboardInterrupt:
            log.info("Gracefully exited.")
            break


if __name__ == "__main__":
    main()
