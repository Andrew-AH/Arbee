from abc import ABC, abstractmethod

from libs.models.odds import PriceData


class VendorScraper(ABC):
    @abstractmethod
    def get_current_item_prices(self) -> PriceData:
        """
        Retrieve the current prices from the vendor.

        Returns:
            PriceData: An object representing the current prices for various items.
        """
        pass
