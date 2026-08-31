from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
import logging
import random
import time
import os

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tracing
provider = TracerProvider()
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318") + "/v1/traces"
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Metrics
REQUEST_COUNT = Counter("demo_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("demo_request_latency_seconds", "Request latency", ["endpoint"])

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def root():
    with tracer.start_as_current_span("root-handler") as span:
        span.set_attribute("endpoint", "/")
        REQUEST_COUNT.labels(method="GET", endpoint="/", status="200").inc()
        logger.info("Root endpoint called")
        return {"status": "ok", "service": "demo-app"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/order")
async def create_order():
    with tracer.start_as_current_span("create-order") as span:
        order_id = random.randint(1000, 9999)
        span.set_attribute("order.id", order_id)

        # эмулируем работу с БД
        with tracer.start_as_current_span("db-query"):
            time.sleep(random.uniform(0.05, 0.2))
            logger.info(f"Order {order_id} saved to DB")

        # эмулируем внешний сервис
        with tracer.start_as_current_span("payment-service"):
            time.sleep(random.uniform(0.1, 0.3))
            logger.info(f"Payment processed for order {order_id}")

        REQUEST_COUNT.labels(method="GET", endpoint="/order", status="200").inc()
        return {"order_id": order_id, "status": "created"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")