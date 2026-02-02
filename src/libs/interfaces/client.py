from abc import ABC, abstractmethod


class VendorClient(ABC):
    @abstractmethod
    def buy(self, item: str, price: float, amount: float) -> bool:
        """
        Buy an item on the vendor with the specified price and amount.

        Args:
            item (str): The standardised name of the item to buy.
            price (float): The price at which to buy the item.
            amount (float): The amount to invest.

        Returns:
            bool: True if the item was bought successfully, False otherwise.

        This method should also handle validation to ensure the item is bought at the correct price and amount.
        """
        pass

    @abstractmethod
    def balance(self) -> float:
        """
        Get the current balance of the vendor account.

        Returns:
            float: The current balance.
        """
        pass
