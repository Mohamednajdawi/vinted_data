from typing import List, Dict, Any
import pandas as pd
from .models import VintedOrder
from .ingestor import CSVParser
from .client import VintedClient

class SalesProcessor:
    def __init__(self):
        pass

    def get_all_orders(self) -> List[VintedOrder]:
        return []

    def calculate_stats(self, orders: List[VintedOrder]) -> Dict[str, Any]:
        if not orders:
            return {}

        df = pd.DataFrame([vars(o) for o in orders])
        # Add the property manually since vars() misses it
        df['days_to_sell'] = [o.days_to_sell for o in orders]
        
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])  # drop any unparseable dates
        df = df.sort_values('date')

        # --- Split confirmed (transaction_id present) vs in-transit ---
        confirmed = df[df['transaction_id'].notnull()]
        in_transit = df[df['transaction_id'].isnull()]

        total_orders = len(df)
        total_revenue = float(confirmed['price'].sum() if not confirmed.empty else df['price'].sum())
        pending_revenue = float(in_transit['price'].sum()) if not in_transit.empty else 0.0
        aov = total_revenue / total_orders if total_orders > 0 else 0.0

        # --- Monthly sales (sorted) ---
        df['month'] = df['date'].dt.strftime('%Y-%m')
        monthly_series = df.groupby('month')['price'].sum().sort_index()
        monthly_sales = {k: round(float(v), 2) for k, v in monthly_series.items()}

        # --- Month-over-month growth % ---
        mom_growth = {}
        months = list(monthly_series.index)
        for i in range(1, len(months)):
            prev = float(monthly_series.iloc[i - 1])
            curr = float(monthly_series.iloc[i])
            if prev > 0:
                mom_growth[months[i]] = round((curr - prev) / prev * 100, 1)

        best_month = monthly_series.idxmax() if not monthly_series.empty else None
        worst_month = monthly_series.idxmin() if not monthly_series.empty else None

        # --- Cumulative revenue over time (by month) ---
        cumulative = monthly_series.cumsum()
        cumulative_revenue = {k: round(float(v), 2) for k, v in cumulative.items()}

        # --- Day of week ---
        df['day_name'] = df['date'].dt.day_name()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_group = df.groupby('day_name')['price'].sum()
        day_of_week_sales = {d: round(float(day_group.get(d, 0.0)), 2) for d in days}

        # --- Hour of day (when do buyers pay?) ---
        df['hour'] = df['date'].dt.hour
        hour_group = df.groupby('hour')['price'].count()
        hour_of_day = {str(h): int(hour_group.get(h, 0)) for h in range(24)}

        # --- Price range distribution ---
        bins = [0, 5, 10, 20, 30, 50, 100, float('inf')]
        labels = ['€0-5', '€5-10', '€10-20', '€20-30', '€30-50', '€50-100', '€100+']
        df['price_range'] = pd.cut(df['price'], bins=bins, labels=labels, right=False)
        price_dist = df['price_range'].value_counts().sort_index()
        price_distribution = {str(k): int(v) for k, v in price_dist.items()}

        # --- Top 10 most valuable items sold ---
        top_items_df = df.nlargest(10, 'price')[['title', 'price', 'date', 'status']].copy()
        top_items_df['date_str'] = top_items_df['date'].dt.strftime('%b %d, %Y')
        top_items = []
        for _, row in top_items_df.iterrows():
            item_dict = row.to_dict()
            item_dict['days_to_sell'] = next((o.days_to_sell for o in orders if o.title == row['title']), None)
            top_items.append(item_dict)

        # --- Recent transactions (10 most recent) ---
        latest = df.sort_values('date', ascending=False).head(10).fillna('')
        latest = latest.copy()
        latest['date_str'] = latest['date'].dt.strftime('%b %d, %H:%M')
        latest_sales = []
        for _, row in latest.iterrows():
            sale_dict = row[['title', 'price', 'date_str', 'status']].to_dict()
            # Match back to the original object to get the property
            sale_dict['days_to_sell'] = next((o.days_to_sell for o in orders if o.title == row['title']), None)
            latest_sales.append(sale_dict)

        # --- Status distribution ---
        status_dist = df['status'].value_counts().to_dict()

        # --- Fastest 10 items (lowest days_to_sell) ---
        fastest_items = []
        if 'days_to_sell' in df.columns:
            fastest_df = df[df['days_to_sell'].notnull()].nsmallest(10, 'days_to_sell').copy()
            fastest_df['date_str'] = fastest_df['date'].dt.strftime('%b %d, %Y')
            for _, row in fastest_df.iterrows():
                fastest_items.append({
                    'title': row['title'],
                    'price': row['price'],
                    'date_str': row['date_str'],
                    'status': row['status'],
                    'days_to_sell': row['days_to_sell']
                })

        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "pending_revenue": round(pending_revenue, 2),
            "aov": round(aov, 2),
            "monthly_sales": monthly_sales,
            "cumulative_revenue": cumulative_revenue,
            "mom_growth": mom_growth,
            "best_month": best_month,
            "worst_month": worst_month,
            "day_of_week_sales": day_of_week_sales,
            "hour_of_day": hour_of_day,
            "price_distribution": price_distribution,
            "top_items": top_items,
            "latest_sales": latest_sales,
            "fastest_items": fastest_items,
            "status_distribution": status_dist,
            "currency": orders[0].currency if orders else "EUR"
        }
