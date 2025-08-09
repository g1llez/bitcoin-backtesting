from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

EFFICIENCY_CACHE_HITS = Counter(
    "efficiency_cache_hits_total",
    "Cache hits for efficiency lookups",
)

EFFICIENCY_CACHE_MISSES = Counter(
    "efficiency_cache_misses_total",
    "Cache misses for efficiency lookups",
)


STARTUP_DURATION = Gauge(
    "api_startup_duration_seconds",
    "Duration from process start to API readiness (seconds)",
)

STARTUP_READY_TIMESTAMP = Gauge(
    "api_startup_ready_timestamp_seconds",
    "Unix timestamp when the API finished startup and is ready",
)

DB_BOOTSTRAP_DURATION = Gauge(
    "api_db_bootstrap_duration_seconds",
    "Duration to run database startup migrations (seconds)",
)

MARKET_WARM_DURATION = Gauge(
    "api_market_warm_duration_seconds",
    "Duration to warm market data cache during startup (seconds)",
)

