from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class VintedOrder:
    order_id: str
    title: str
    price: float
    currency: str
    buyer_name: str
    status: str
    date: datetime
    buyer_id: Optional[str] = None
    conversation_id: Optional[str] = None
    transaction_id: Optional[str] = None
    brand: Optional[str] = None
    listing_date: Optional[datetime] = None

    @property
    def days_to_sell(self) -> Optional[int]:
        if self.listing_date and self.date:
            return (self.date - self.listing_date).days
        return None
