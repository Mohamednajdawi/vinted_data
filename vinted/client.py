import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import VintedOrder

class VintedClient:
    def __init__(self, domain: str = "www.vinted.fr", cookie: Optional[str] = None):
        # Ensure domain always has www. prefix
        if not domain.startswith("www."):
            domain = f"www.{domain}"
        self.domain = domain
        self.base_url = f"https://{domain}/api/v2"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"https://{domain}/",
            "X-Vinted-Domain": domain.replace("www.", "")
        }
        if cookie:
            self.headers["Cookie"] = cookie

    async def fetch_all_orders(self, max_pages: int = 20) -> List[Dict[str, Any]]:
        all_orders = []
        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/my_orders?type=sold&status=all&per_page=100&page={page}"
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=False) as client:
                response = await client.get(url)
                if response.status_code in (301, 302, 303, 307, 308):
                    raise Exception(
                        f"Vinted redirected the request (HTTP {response.status_code}). "
                        "This usually means the Session Cookie is invalid or has expired. "
                        f"Please re-copy the cookie from a fresh www.{self.domain} page in your browser."
                    )
                if response.status_code == 401:
                    raise Exception("Vinted returned 401 Unauthorized. Your session cookie has expired — please refresh the page and re-copy a fresh cookie.")
                if response.status_code != 200:
                    if page == 1:
                        raise Exception(f"Vinted API error (HTTP {response.status_code}). Check your domain and cookie.")
                    break
                
                try:
                    data = response.json()
                except Exception:
                    # Vinted returned HTML instead of JSON (login redirect disguised as 200)
                    ct = response.headers.get('content-type', '')
                    print(f"[VintedClient] Non-JSON response (content-type={ct}): {response.text[:300]}")
                    raise Exception(
                        "Vinted returned an HTML page instead of JSON. "
                        "This means authentication failed. \n\n"
                        "How to fix: In Chrome DevTools Network tab, look at a request to "
                        "www.vinted.at/api/v2/... and copy the FULL cookie header string "
                        "(it should contain 'access_token_web=' near the start)."
                    )
                if page == 1:
                    print(f"[VintedClient] Response keys: {list(data.keys())}")
                    print(f"[VintedClient] Response preview: {str(data)[:500]}")
                orders = data.get("orders", []) or data.get("my_orders", [])
                if orders and page == 1:
                    print(f"[VintedClient] First raw order keys: {list(orders[0].keys())}")
                    print(f"[VintedClient] First raw order sample: {str(orders[0])[:500]}")
                
                if not orders:
                    # Try alternate keys used by some Vinted locales
                    orders = data.get("my_orders", [])
                    orders = data.get("my_orders", data.get("items", data.get("data", [])))
                if not orders:
                    break
                
                all_orders.extend(orders)
        return all_orders

    async def fetch_conversation(self, conv_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/conversations/{conv_id}"
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def _extract_user_id_from_cookie(self) -> Optional[str]:
        """Extract user ID directly from the access_token_web JWT in the cookie string."""
        import base64, json as _json
        cookie = self.headers.get('Cookie', '')
        for part in cookie.split(';'):
            part = part.strip()
            if part.startswith('access_token_web='):
                token = part[len('access_token_web='):].strip()
                # JWT = header.payload.signature — decode the payload
                parts = token.split('.')
                if len(parts) >= 2:
                    payload_b64 = parts[1]
                    # Fix base64 padding
                    payload_b64 += '=' * (4 - len(payload_b64) % 4)
                    try:
                        payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
                        user_id = payload.get('user_id') or payload.get('sub') or payload.get('id')
                        if user_id:
                            print(f"[VintedClient] Extracted user_id={user_id} from JWT")
                            return str(user_id)
                    except Exception as e:
                        print(f"[VintedClient] JWT decode error: {e}")
        return None

    async def fetch_user_info(self) -> Dict[str, Any]:
        """Fetch current logged-in user profile stats."""
        # Try both the API and the JWT
        user_id = self._extract_user_id_from_cookie()
        print(f"[VintedClient] Extracted user_id from JWT: {user_id}")
        
        # Always try to fetch full user info from the correct current endpoint
        url = f"{self.base_url}/users/current"
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=False) as client:
            try:
                response = await client.get(url)
                print(f"[VintedClient] /users/current status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    user = data.get('user', {})
                    if user.get('id'):
                        print(f"[VintedClient] Successfully got user_id {user.get('id')} from /users/current")
                        return data
                else:
                    print(f"[VintedClient] /users/current failed body: {response.text[:200]}")
            except Exception as e:
                print(f"[VintedClient] /users/current error: {e}")
        
        # If /users/current failed but we have a JWT ID, we can still try /users/{id}
        if user_id:
            url = f"{self.base_url}/users/{user_id}"
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=False) as client:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return response.json()
                except: pass
        return {}

    async def fetch_all_items(self, max_pages: int = 20) -> List[Dict[str, Any]]:
        """Fetch all wardrobe listings for the current user."""
        # Try JWT first, then fallback to profile endpoint
        user_id = self._extract_user_id_from_cookie()
        user: Dict[str, Any] = {}
        
        print(f"[VintedClient] Trace: user_id after extraction: '{user_id}'")
        if not user_id:
            print("[VintedClient] Trace: user_id missing, fetching info...")
            user_data = await self.fetch_user_info()
            user = user_data.get('user', user_data)
            user_id = str(user.get('id', '')) if user.get('id') else None
            print(f"[VintedClient] Trace: user_id after info fetch: '{user_id}'")

        print(f"[VintedClient] Final user_id for wardrobe: {user_id}")
        if not user_id:
            raise Exception("Could not resolve your Vinted user ID. Session may have expired.")

        all_items: List[Dict[str, Any]] = []
        try:
            for page in range(1, max_pages + 1):
                url = f"{self.base_url}/wardrobe/{user_id}/items?page={page}&per_page=100"
                print(f"[VintedClient] Fetching wardrobe page {page}: {url}")
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=False) as client:
                    response = await client.get(url)
                    print(f"[VintedClient] Wardrobe page {page} status: {response.status_code}")
                    if response.status_code != 200:
                        print(f"[VintedClient] Wardrobe error body: {response.text[:200]}")
                        break
                    data = response.json()
                    current_items = data.get('items', [])
                    print(f"[VintedClient] Page {page} fetched {len(current_items)} items")
                    if not current_items:
                        break
                    all_items.extend(current_items)
        except Exception as e:
            print(f"[VintedClient] Critical error in fetch_all_items loop: {e}")
            import traceback
            print(traceback.format_exc())
            
        print(f"[VintedClient] Total wardrobe items fetched: {len(all_items)}")
        return all_items, user

    @staticmethod
    def map_api_order(raw: dict) -> VintedOrder:
        # Price: dict with 'amount' (string) and 'currency_code'
        raw_price = raw.get('price', {})
        if isinstance(raw_price, dict):
            price_val = float(raw_price.get('amount', 0))
            currency = raw_price.get('currency_code', 'EUR')
        else:
            price_val = float(raw_price) if str(raw_price).replace('.','',1).isdigit() else 0.0
            currency = 'EUR'

        # transaction_id: present = payment confirmed
        transaction_id = str(raw.get('transaction_id')) if raw.get('transaction_id') else None

        # Completion via transaction_user_status OR transaction_id
        user_status = raw.get('transaction_user_status', '')
        if user_status == 'completed' and not transaction_id:
            transaction_id = f"status_completed_{raw.get('conversation_id', 'x')}"

        # Date: the confirmed field name is just 'date'
        created_at = datetime.now()
        raw_date = raw.get('date')
        if raw_date:
            try:
                # Strip timezone info to keep all dates naive for pandas compatibility
                created_at = datetime.fromisoformat(str(raw_date)).replace(tzinfo=None)
            except Exception:
                pass

        photo_url = None
        photo = raw.get('photo')
        if isinstance(photo, dict):
            photo_url = photo.get('url')

        # Velocity Heuristic: Extract timestamp from photo URL if listing_date is missing
        listing_date = None
        
        # 1. Try explicit fields first
        for k in ['listing_date', 'item_created_at_ts', 'created_at_ts']:
            if k in raw:
                try:
                    listing_date = datetime.fromtimestamp(float(raw[k]))
                    break
                except: pass
        
        # 2. Heuristic: Photo URLs like .../1774347753.jpeg contain the listing/upload TS
        if not listing_date and photo_url:
            import re
            # Match digits before .jpg or .jpeg
            match = re.search(r'/(\d{9,11})\.jpe?g', photo_url)
            if match:
                try:
                    ts = float(match.group(1))
                    if 1500000000 < ts < 2000000000: # Sanity check for Unix TS (2017-2033)
                        listing_date = datetime.fromtimestamp(ts)
                        print(f"[VintedClient] HEURISTIC: Extracted listing_date {listing_date} from photo URL")
                except: pass

        return VintedOrder(
            order_id=str(raw.get('conversation_id', 'unknown')),
            title=raw.get('title', 'Unknown Item'),
            price=price_val,
            currency=currency,
            buyer_name='Vinted Buyer',
            status=raw.get('status', raw.get('transaction_user_status', 'unknown')),
            date=created_at,
            listing_date=listing_date,
            transaction_id=transaction_id,
            brand=None
        )
