# 📈 Vinted Inventory & Sales Analytics

A premium, data-driven dashboard designed for Vinted power sellers to optimize their shop performance, track revenue trends, and manage inventory health with professional-grade insights.

![Dashboard Preview](file:///C:/Users/INT100313/.gemini/antigravity/brain/74aadb77-00d1-4853-ab80-0560267da9e3/sales_analytics_dashboard_1774361925399.png)

## ✨ Key Features

### 📊 Advanced Sales Analytics
- **Revenue Visualization**: Track monthly and cumulative revenue with sleek interactive charts.
- **Activity Insights**: Identify peak engagement times by day of the week and hour of the day.
- **Filterable Transactions**: Deep-dive into recent sales with dynamic status filtering (Completed, Processing, etc.).
- **Top Performers**: Auto-identify your most valuable historical sales.

### 📦 Inventory Optimization
- **Stock Health Assessment**: Visual breakdown of Sold, Hidden, Reserved, and Available listings.
- **Performance Triage**: Instant identification of "Viral" (🔥), "Good" (💎), and "Static" (🧊) items based on engagement rates.
- **Category Deep-Dive**: Sortable market performance metrics (Average Price, Views, Likes) for every niche in your shop.
- **Live Sync**: Direct integration with Vinted wardrobe API for real-time inventory tracking.

![Inventory Health](file:///C:/Users/INT100313/.gemini/antigravity/brain/74aadb77-00d1-4853-ab80-0560267da9e3/inventory_dashboard_1774361933516.png)

## 🚀 Quick Start

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/Mohamednajdawi/vinted_data.git
   cd vinted_data
   ```

2. **Install Dependencies**:
   Using [uv](https://github.com/astral-sh/uv):
   ```bash
   uv sync
   ```

3. **Run the Dashboard**:
   ```bash
   uv run uvicorn main:app --port 8000 --reload
   ```

4. **Sync Data**:
   - Open `http://127.0.0.1:8000`
   - Use the **Sync** button to provide your Vinted session cookie and start analyzing!

## 🛠️ Technical Stack
- **Backend**: Python 3.12+, FastAPI, Pandas (Data Analytics), HTTPX
- **Frontend**: Vanilla ES6+ Javascript, Chart.js, Glassmorphism CSS Design

---
*Built with professional Data Science principles for Vinted inventory optimization.*
