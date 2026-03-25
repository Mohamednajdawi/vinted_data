import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from vinted.processor import SalesProcessor
from vinted.client import VintedClient
from vinted.vindy_api import router as vindy_router
from dotenv import load_dotenv
import httpx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

load_dotenv()

import logging
logging.basicConfig(
    filename='vinted_debug.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vinted Sales Analytics & Vindy Extension API")

# Include the newly mocked Vindy APIs
app.include_router(vindy_router)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize processor (Now decoupled from CSV)
processor = SalesProcessor()

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/v1/stats")
async def get_stats():
    # Return empty/prompt. Live interaction requires POST to /api/v1/live_sync
    return {"success": False, "error": "Authentication required. Please connect your Vinted account."}

@app.get("/api/v1/orders")
async def get_orders():
    return processor.get_all_orders()

class LiveSyncRequest(BaseModel):
    domain: str
    cookie: str

@app.post("/api/v1/live_sync")
async def live_sync(req: LiveSyncRequest):
    try:
        client = VintedClient(domain=req.domain, cookie=req.cookie)
        raw_orders = await client.fetch_all_orders(max_pages=20)
        
        print(f"[LiveSync] raw_orders count: {len(raw_orders)}")
        if raw_orders:
            print(f"[LiveSync] First raw order keys: {list(raw_orders[0].keys())}")
            print(f"[LiveSync] First raw order sample: {str(raw_orders[0])[:500]}")
        
        orders = [VintedClient.map_api_order(o) for o in raw_orders]
        print(f"[LiveSync] mapped orders count: {len(orders)}")
        completed = [o for o in orders if o.transaction_id]
        print(f"[LiveSync] completed orders (with transaction_id): {len(completed)}")
        
        stats = processor.calculate_stats(orders)
        stats["_debug"] = {
            "raw_fetched": len(raw_orders),
            "mapped": len(orders),
            "completed": len(completed)
        }
        
        return {"success": True, "stats": stats}
    except Exception as e:
        import traceback
        print(f"[LiveSync ERROR] {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

@app.post("/api/v1/debug_raw")
async def debug_raw(req: LiveSyncRequest):
    """Returns the raw first order from Vinted to diagnose field names."""
    try:
        client = VintedClient(domain=req.domain, cookie=req.cookie)
        raw_orders = await client.fetch_all_orders(max_pages=1)
        if not raw_orders:
            return {"success": False, "error": "Vinted returned 0 orders", "count": 0}
        first = raw_orders[0]
        # Show all keys and extract date-related ones
        date_keys = {k: v for k, v in first.items() if any(x in k.lower() for x in ['at', 'date', 'time', 'created', 'sold', 'updated'])}
        return {
            "success": True,
            "count": len(raw_orders),
            "all_keys": sorted(first.keys()),
            "date_related_fields": date_keys,
            "full_first_order": first
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/debug_items")
async def debug_items(req: LiveSyncRequest):
    """Returns raw diagnostic info for the items/user API."""
    try:
        client = VintedClient(domain=req.domain, cookie=req.cookie)
        diagnostics = []
        endpoints = ["/users/current_user", "/users/me", "/account/profile"]
        
        user_info = {}
        for ep in endpoints:
            url = f"{client.base_url}{ep}"
            async with httpx.AsyncClient(headers=client.headers, follow_redirects=False) as http:
                resp = await http.get(url)
                diagnostics.append({
                    "endpoint": ep,
                    "status": resp.status_code,
                    "content_type": resp.headers.get("content-type"),
                    "preview": resp.text[:200]
                })
                if resp.status_code == 200:
                    try:
                        user_info = resp.json()
                        break
                    except: pass

        items, user = await client.fetch_all_items(max_pages=1)
        return {
            "success": True,
            "diagnostics": diagnostics,
            "user_info_found": bool(user_info),
            "item_count": len(items),
            "first_item": items[0] if items else None
        }
    except Exception as e:
        import traceback
        return {
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "diagnostics": locals().get('diagnostics', [])
        }

@app.post("/api/v1/live_inventory_sync")
async def live_inventory_sync(req: LiveSyncRequest):
    """Fetches all active listings and returns computed inventory stats."""
    try:
        client = VintedClient(domain=req.domain, cookie=req.cookie)
        logger.info(f"Syncing inventory for domain: {client.domain}")
        items, user = await client.fetch_all_items(max_pages=20)
        logger.info(f"Fetched {len(items)} items")
        stats = await compute_inventory_stats(items, user, client)
        logger.info(f"Computed stats: {stats.get('total_items')} items")
        return {"success": True, "stats": stats}
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"[InventorySync ERROR] Console Dump:\n{err_msg}")
        return {"success": False, "error": str(e)}

async def compute_inventory_stats(items: list, user: dict, client: VintedClient) -> dict:
    print(f"[DEBUG] Started compute_inventory_stats with {len(items)} items")
    if not items:
        return {"total_items": 0}

    try:
        df = pd.DataFrame(items)
        print(f"[DEBUG] DataFrame created with shape: {df.shape}")
    except Exception as e:
        print(f"[ERROR] DataFrame creation failed: {e}")
        return {"total_items": len(items), "error": "DataFrame error"}
    if not df.empty:
        # --- Diagnostic: Snapshot of the first item ---
        print(f"[DIAGNOSTIC] RAW FIRST ITEM ID: {items[0].get('id')}")
        print(f"[DIAGNOSTIC] Path: {items[0].get('path')}")

    def parse_price(p):
        if isinstance(p, dict): return float(p.get('amount', 0))
        try: return float(p)
        except: return 0.0

    df['price_val'] = df['price'].apply(parse_price) if 'price' in df.columns else 0.0

    # --- KPI Totals ---
    total_potential = round(float(df['price_val'].sum()), 2)
    avg_price = round(float(df['price_val'].mean()), 2)
    total_favs = int(df['favourite_count'].sum()) if 'favourite_count' in df.columns else None
    total_views = int(df['view_count'].sum()) if 'view_count' in df.columns else None

    # --- Price distribution ---
    bins = [0, 5, 10, 20, 30, 50, 100, float('inf')]
    labels = ['€0-5', '€5-10', '€10-20', '€20-30', '€30-50', '€50-100', '€100+']
    df['price_range'] = pd.cut(df['price_val'], bins=bins, labels=labels, right=False)
    price_dist = {str(k): int(v) for k, v in df['price_range'].value_counts().sort_index().items()}

    # --- Days listed ---
    now = datetime.now()
    def parse_ts(v):
        try:
            if isinstance(v, (int, float)): return (now - datetime.fromtimestamp(v)).days
            return (now - datetime.fromisoformat(str(v)).replace(tzinfo=None)).days
        except: return None

    days_listed = []
    for col in ['created_at_ts', 'active_at_ts', 'updated_at_ts', 'created_at']:
        if col in df.columns:
            days_listed = df[col].apply(parse_ts).dropna().tolist()
            if days_listed: break

    # --- Category breakdown from catalog
    # Try to find category column or extract from path
    cat_col = None
    for c in ['catalog_title', 'category_title', 'category_name']:
        if c in df.columns:
            cat_col = c
            break
            
    if not cat_col:
        def extract_cat_v2(row):
            # 1. Try real catalog branch title first (if we fetched full details)
            if 'catalog_branch_title' in row and row['catalog_branch_title']:
                return row['catalog_branch_title']
            
            # 2. Try to get it from the path/slug, but CLEAN IT
            p = row.get('path', '')
            if p and '/items/' in p:
                parts = str(p).strip('/').split('/')
                slug = parts[2] if len(parts) >= 3 else (parts[1] if len(parts) >= 2 else parts[0])
                import re
                clean = re.sub(r'^\d+-', '', slug)
                return clean.replace('-', ' ').title()
                
            # 3. Fallback to title
            return str(row.get('title', 'Other')).split('-')[0].strip().title()
            
        print(f"[DEBUG] Applying extract_cat_v2 to {len(df)} rows...")
        try:
            df['catalog_title'] = df.apply(extract_cat_v2, axis=1)
            cat_col = 'catalog_title'
            print("[DEBUG] Category extraction successful")
        except Exception as e:
            print(f"[ERROR] Category extraction failed: {e}")
            import traceback
            print(traceback.format_exc())
            # Fallback
            df['catalog_title'] = 'Uncategorized'
            cat_col = 'catalog_title'
    
    print(f"[DEBUG] Building categories dict from {cat_col}...")
    categories = df[cat_col].value_counts().head(8).to_dict() if cat_col else {}

    # --- Brand breakdown (from brand_dto dict) ---
    brand_col = 'brand_dto'
    brands = {}
    if brand_col in df.columns:
        brands_series = df[brand_col].apply(lambda b: b.get('title') if isinstance(b, dict) else b)
        brands = brands_series.value_counts().head(8).to_dict()

    # --- Top 10 most expensive listings ---
    # --- Advanced Data Science Metrics ---
    # Engagement Rate = Likes / Views (if Views > 0)
    df['favourite_count'] = df['favourite_count'].fillna(0)
    df['view_count'] = df['view_count'].fillna(0)
    df['engagement_rate'] = (df['favourite_count'] / df['view_count'].replace(0, 1) * 100).fillna(0).round(2)
    
    # Sell-Through Score (Heuristic: weighted likes/views and normalized days listed)
    # Higher score = More likely to sell soon.
    # We use log(views+1) to prevent outliers from dominating.
    import numpy as np
    df['sell_score'] = (
        (df['favourite_count'].fillna(0) * 2.0) + 
        (np.log1p(df['view_count'].fillna(0)) * 0.5)
    ).round(2)

    def make_listing_row(row):
        brand = ''
        if 'brand_dto' in row and isinstance(row.get('brand_dto'), dict):
            brand = row['brand_dto'].get('title', '')
        elif 'brand' in row:
            brand = str(row.get('brand', ''))
        
        def safe_int(v):
            try:
                import pandas as pd
                if pd.isna(v): return 0
                return int(float(v))
            except: return 0

        views = safe_int(row.get('view_count'))
        favs  = safe_int(row.get('favourite_count'))
        er    = float(row.get('engagement_rate', 0.0))
        
        # Status logic
        if row.get('is_closed'): s = 'Sold'
        elif row.get('is_hidden'): s = 'Hidden'
        elif row.get('is_reserved'): s = 'Reserved'
        else: s = 'Available'
        
        return {
            'title': str(row.get('title', 'Unknown'))[:60],
            'price_val': float(row.get('price_val', 0)),
            'brand': brand,
            'views': views,
            'favs': favs,
            'engagement_rate': er,
            'sell_score': float(row.get('sell_score', 0.0)),
            'id': row.get('id'),
            'stock_status': s
        }

    top_listings = [
        make_listing_row(row)
        for _, row in df.nlargest(10, 'price_val').iterrows()
    ]

    # --- Most favourited items (SHOW ALL as requested) ---
    most_liked = []
    if 'favourite_count' in df.columns:
        most_liked = [
            make_listing_row(row)
            for _, row in df.sort_values('favourite_count', ascending=False).iterrows()
        ]

    # --- Status Distribution ---
    df['stock_status'] = 'Available'
    if 'is_closed' in df.columns:
        df.loc[df['is_closed'] == True, 'stock_status'] = 'Sold'
    if 'is_hidden' in df.columns:
        df.loc[(df['is_hidden'] == True) & (df['stock_status'] == 'Available'), 'stock_status'] = 'Hidden'
    if 'is_reserved' in df.columns:
        df.loc[(df['is_reserved'] == True) & (df['stock_status'] == 'Available'), 'stock_status'] = 'Reserved'
        
    status_dist = df['stock_status'].value_counts().to_dict()

    # --- Most Liked listings ---
    # (SHOW ALL as requested) ---
    most_viewed = []
    if 'view_count' in df.columns:
        most_viewed = [
            make_listing_row(row)
            for _, row in df.sort_values('view_count', ascending=False).iterrows()
        ]
        
    # --- Category Performance (Data Scientist Deep Dive) ---
    cat_perf = []
    if cat_col and not df.empty:
        # Group by category and compute means/sums
        cat_group = df.groupby(cat_col).agg({
            'price_val': 'mean',
            'favourite_count': 'sum',
            'view_count': 'sum',
            'id': 'count'
        }).rename(columns={'id': 'count'})
        
        # Calculate engagement rate per category
        cat_group['er'] = (cat_group['favourite_count'] / cat_group['view_count'].replace(0, 1) * 100).round(2)
        
        # Convert to list of dicts for frontend and handle NaN
        cat_perf = cat_group.reset_index().fillna(0).sort_values('count', ascending=False).to_dict('records')

    # --- Top Engagement Items ---
    top_engagement = [
        make_listing_row(row)
        for _, row in df.sort_values('engagement_rate', ascending=False).head(20).iterrows()
    ]

    res = {
        "total_items": int(len(df)),
        "total_potential_revenue": total_potential,
        "avg_listing_price": avg_price,
        "price_distribution": price_dist,
        "categories": {str(k): int(v) for k, v in categories.items()},
        "brands": {str(k): int(v) for k, v in brands.items()} if isinstance(brands, dict) else {},
        "top_listings": top_listings,
        "all_listings": df.to_dict('records')[:100],
        "most_liked": most_liked,
        "most_viewed": most_viewed,
        "top_engagement": top_engagement,
        "avg_days_listed": round(sum(days_listed)/len(days_listed), 1) if days_listed else None,
        "total_favourites": total_favs,
        "total_views": total_views,
        "avg_engagement_rate": round(float(df['engagement_rate'].mean()), 2) if not df.empty else 0,
        "category_performance": cat_perf,
        "status_distribution": {str(k): int(v) for k, v in status_dist.items()},
        "user_login": user.get('login'),
        "user_feedback_count": user.get('feedback_count'),
        "user_positive_feedback": user.get('positive_feedback_count'),
    }
    print(f"[DEBUG] Final results summary: {res['total_items']} items, {len(res['category_performance'])} cats")
    
    # Extra debug log and JSON cleanup
    # Ensure no NaN values reach the JSON serializer
    def clean_nan(obj):
        if isinstance(obj, dict):
            return {k: clean_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_nan(x) for x in obj]
        elif isinstance(obj, float):
            import math
            return 0.0 if math.isnan(obj) or math.isinf(obj) else obj
        return obj

    res = clean_nan(res)
    
    logger.info(f"Final stats keys: {list(res.keys())}")
    if res.get('top_listings') and len(res['top_listings']) > 0:
        logger.info(f"Sample listing: {res['top_listings'][0]}")
    
    return res
