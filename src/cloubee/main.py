from datetime import timedelta
from multiprocessing import Queue
from threading import Thread

from db.config import get_db_engine
from db.repository import Repository
from jobs.save_races import generate_enriched_venues, load_enriched_venues
from libs.models.opportunity import Opportunity
from libs.notifications.sns import publish_to_sns
from libs.utils.datetimes import get_latest_datetime
from libs.utils.env import DB_URL, MACHINE
from libs.utils.log import get_logger
from libs.utils.provider import Vendor, Service, get_service
from libs.utils.shutdown import schedule_windows_shutdown
from libs.vendors.vendor_alpha.scraper import start_cycling_scrapers_for_all_venues

# Setup
# =============================================================================
log = get_logger(logs_to_file=True, logs_to_console=True)

opp_queue = Queue()


def main(vendor: Vendor):
    # Instantiate setup
    generate_enriched_venues(skip_if_exists=True)
    enriched_venues = load_enriched_venues()

    # Instantiate repository
    repository = Repository(get_db_engine(DB_URL))

    # Instantiate detector
    detector_class = get_service(vendor, Service.DETECTOR)
    detector = detector_class()

    Thread(target=repository.save_machine_to_db, args=(MACHINE,)).start()

    log.info("Starting scrapers for all venues..")
    processes = []
    start_cycling_scrapers_for_all_venues(detector, enriched_venues, processes, opp_queue)
    log.info("Started scrapers for all venues!")

    log.info("Cloubee started execution!")

    # Schedule shutdown after last event
    Thread(
        target=schedule_windows_shutdown,
        args=(get_latest_datetime(enriched_venues) + timedelta(minutes=1),),
    ).start()

    try:
        while any(process.is_alive() for process in processes):
            if not opp_queue.empty():
                opp: Opportunity = opp_queue.get()
                publish_to_sns(opp.to_json())
                Thread(
                    target=repository.save_opportunity_to_db,
                    args=(
                        opp,
                        MACHINE,
                    ),
                ).start()

    except KeyboardInterrupt:
        log.info("Gracefully shutting down...")

    finally:
        for process in processes:
            process.join()

        log.info("Cloubee completed execution!")


if __name__ == "__main__":
    main(vendor=Vendor.VENDOR_ALPHA)
