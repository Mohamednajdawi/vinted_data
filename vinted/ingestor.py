import pandas as pd
from datetime import datetime
from typing import List
from .models import VintedOrder

class CSVParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> List[VintedOrder]:
        df = pd.read_csv(self.file_path)
        orders = []
        for _, row in df.iterrows():
            # Date,Title,Price,Currency,Buyer,Status
            try:
                date_val = datetime.strptime(row['Date'], '%Y-%m-%d')
            except (ValueError, TypeError):
                date_val = datetime.now()

            status = str(row['Status'])
            is_completed = any(s in status.lower() for s in ['beendet', 'erfolgreich', 'verschickt'])
            transaction_id = f"txn_{_}" if is_completed else None

            orders.append(VintedOrder(
                order_id=f"csv_{_}", # Placeholder ID for CSV items
                title=str(row['Title']),
                price=float(row['Price']),
                currency=str(row['Currency']),
                buyer_name=str(row['Buyer']),
                status=status,
                date=date_val,
                transaction_id=transaction_id
            ))
        return orders
