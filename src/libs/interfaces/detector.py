from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple


class VendorDetector(ABC):
    @abstractmethod
    def detect_venue_opps_cyclic(
        self, events: List[Tuple[str, int, int, datetime]]
    ) -> None:
        """
        Detects price arbitrage opportunities against all events for a single venue using a cyclic strategy.
        For example, say we have events E1, E2 and E3.
        The cyclic strategy will scan infinitely in the following order:
        E1 -> E2 -> E3 -> E1 -> E2 -> ...

        Args:
            events (List[Tuple[str, int, int, datetime]]): List of event tuples. Each tuple refers to a single event
                                                          where each entry is the following:
                                                          - vendor_event_url (str): URL of the event on vendor.
                                                          - vendor_beta_market_id (int): Market ID of the event on Vendor Beta.
                                                          - venue_name (int): Name of the event venue.
                                                          - event_date_time (datetime): Date and time of the event.
        """
        pass
