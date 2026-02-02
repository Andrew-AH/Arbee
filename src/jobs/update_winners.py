import re
from datetime import datetime, timedelta

from selenium_driverless.types.by import By
from sqlalchemy import and_, update
from sqlalchemy.orm import Session

from db.config import get_db_engine
from db.entities import Events
from db.repository import Repository
from libs.utils.datetimes import uk_to_utc
from libs.utils.driver import get_chrome_driver
from libs.utils.env import DB_URL
from libs.utils.log import get_logger
from libs.utils.strings import standardize_string

log = get_logger(logs_to_file=True, logs_to_console=True)

# Setup - Constants
NO_WINNER = "nowinner"
event_table = Events.__table__


def main():
    # Setup - Counters
    no_venues = 0
    no_events = 0
    updated_records = 0
    missed_records = []

    # Setup - Initialise Driver
    driver = get_chrome_driver()

    # Setup - Repository
    repository = Repository(get_db_engine(DB_URL))

    # Setup - Create URL For Yesterday's Events
    yesterday = datetime.now().replace(second=0, microsecond=0) - timedelta(days=1)
    formatted_date = yesterday.strftime("%Y-%m-%d")
    EVENT_RESULTS_URL = f"https://www.example-results.com/uk-ireland/results/{formatted_date}"

    try:
        with Session(repository.engine) as session:
            log.info(f"Navigating to {EVENT_RESULTS_URL}")

            driver.get(EVENT_RESULTS_URL)

            content = driver.find_element(By.XPATH, "//*[@class='ssrcss-14xrj8w-Stack e1y4nx260']")

            sections = content.find_elements(By.XPATH, ".//section")

            log.info("Begin enriching..")

            for section in sections:
                no_venues += 1
                venue_element = section.find_element(
                    By.XPATH,
                    ".//span",
                )

                venue = venue_element.text
                log.info(venue)

                events = section.find_elements(By.XPATH, ".//tr")

                for index, event in enumerate(events):
                    # Skip header row
                    if index == 0:
                        continue

                    no_events += 1
                    stats = event.find_elements(By.XPATH, ".//td")
                    uk_time = datetime.strptime(stats[0].text, "%H:%M")
                    uk_datetime = yesterday.replace(hour=uk_time.hour, minute=uk_time.minute)

                    start_time_utc = uk_to_utc(uk_datetime)
                    number_of_items = int(stats[1].text)
                    winner = standardize_string(re.match(r"[^,]+", stats[3].text).group())

                    if winner == NO_WINNER:
                        winner = None

                    log.info(
                        f"Start time: {start_time_utc} | No. items: {number_of_items:2} | Winner: {winner}"
                    )

                    # Save to DB
                    stmt = (
                        update(event_table)
                        .where(
                            and_(
                                event_table.c.venue == venue,
                                event_table.c.start_time == start_time_utc,
                            )
                        )
                        .values(winner=winner, number_of_items=number_of_items)
                    )
                    result = session.execute(stmt)
                    session.commit()
                    if result.rowcount > 0:
                        updated_records += 1
                    else:
                        missed_records.append(
                            {
                                "venue": venue,
                                "start_time": start_time_utc,
                                "number_of_items": number_of_items,
                                "winner": winner,
                            }
                        )

        log.info("Save winners complete!")
        log.info(f"{no_venues} venues scraped")
        log.info(f"{no_events} events scraped")
        log.info(f"{updated_records} event winners updated")
        log.info(f"{len(missed_records)} missed events (not found in db)")
        for records in missed_records:
            log.info(records)

        driver.quit()

    except Exception as e:
        log.exception(f"Exception thrown: {e}")
        driver.quit()


if __name__ == "__main__":
    main()
