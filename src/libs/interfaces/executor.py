from abc import ABC, abstractmethod

from libs.models.opportunity import Opportunity


class VendorBetaSellOrderNotFulfilledException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ItemCouldNotBeClickedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class VendorPricesHaveChangedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class VendorExecutor(ABC):
    @abstractmethod
    def execute(self, opp: Opportunity) -> bool:
        """
        Executes a given price arbitrage opportunity.
        Returns

        Args:
            opp Opportunity: A price arbitrage opportunity.

        Returns:
            bool: True if opportunity execution succeeds, resulting in a profit.
                  False if opportunity execution fails, incurring a small loss due to manual exit.
        """
        pass
