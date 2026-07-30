# Analytics Engine

Business intelligence and analytics system for the Autonomous Company OS. This engine handles data aggregation, dashboard creation, real-time metrics, predictive analytics, and comprehensive reporting.

## Features

- **Data Aggregation** - Collect data from all engines
- **Real-time Metrics** - Live business metrics monitoring
- **Dashboard Creation** - Customizable analytics dashboards
- **Predictive Analytics** - AI-powered forecasting and predictions
- **Anomaly Detection** - Automatic anomaly detection and alerting
- **Custom Reports** - Generate custom business reports
- **Data Visualization** - Interactive charts and graphs
- **Performance Tracking** - KPI monitoring and goal tracking

## Architecture

```
┌─────────────┐    Data      ┌──────────────┐
│   All       │ ────────────> │  Data        │
│  Engines    │               │  Collector   │
└─────────────┘               └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Metrics    │ │ Predict │ │ Anomaly   │
            │   Engine     │ │ Engine  │ │ Detection  │
            └──────────────┘ └─────────┘ └───────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Dashboard Manager          │
                    │  (Custom dashboards and reports)  │
                    └─────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Reports    │ │ Visual  │ │ KPI       │
            │   Generator  │ │ Engine  │ │ Tracking   │
            └──────────────┘ └─────────┘ └───────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (for analytics data)
- Redis (for caching and real-time data)
- ClickHouse (optional, for time-series data)

### Local Development

```bash
# Clone repository
git clone https://github.com/autonomous-company/analytics-engine.git
cd analytics-engine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8042
```

### Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f analytics-engine

# Stop services
docker-compose down
```

## Configuration

Configuration is managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://localhost/analytics` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `CLICKHOUSE_URL` | - | ClickHouse connection URL (optional) |

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - Service information

### Metrics
- `GET /metrics/real-time` - Get real-time metrics
- `GET /metrics/historical` - Get historical metrics
- `POST /metrics/custom` - Create custom metric

### Dashboards
- `POST /dashboards/create` - Create dashboard
- `GET /dashboards/{dashboard_id}` - Get dashboard
- `GET /dashboards` - List dashboards

### Reports
- `POST /reports/generate` - Generate report
- `GET /reports/{report_id}` - Get report
- `GET /reports` - List reports

### Predictions
- `POST /predictions/forecast` - Generate forecast
- `GET /predictions/{prediction_id}` - Get prediction
- `GET /predictions/anomalies` - Get detected anomalies

### KPIs
- `GET /kpi/current` - Get current KPIs
- `POST /kpi/set-goal` - Set KPI goal
- `GET /kpi/progress` - Get KPI progress

## Usage Examples

### Get Real-time Metrics

```python
import httpx

async def get_real_time_metrics():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8042/metrics/real-time"
        )
        return response.json()
```

### Generate Forecast

```python
async def generate_forecast():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8042/predictions/forecast",
            json={
                "metric": "revenue",
                "period": "monthly",
                "months": 6
            }
        )
        return response.json()
```

### Create Dashboard

```python
async def create_dashboard():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8042/dashboards/create",
            json={
                "name": "Executive Overview",
                "widgets": [
                    {"type": "revenue", "position": "top-left"},
                    {"type": "users", "position": "top-right"}
                ]
            }
        )
        return response.json()
```

## Metric Categories

- **Revenue Metrics** - Total revenue, MRR, ARPU, churn
- **User Metrics** - Active users, new signups, retention
- **Marketing Metrics** - CAC, LTV, conversion rates
- **Sales Metrics** - Pipeline, close rate, deal size
- **Support Metrics** - Response time, CSAT, ticket volume
- **Operational Metrics** - System health, performance, uptime

## Integration with Other Engines

### All Engines
- Collects data from all engines
- Provides analytics back to engines
- Enables data-driven decision making

### Global State Manager
- Stores analytics state
- Tracks metric history
- Provides real-time updates

## Monitoring

### Metrics
- Data collection latency
- Query performance
- Dashboard load times
- Report generation time
- Prediction accuracy

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
