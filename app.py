from flask  import Flask, Response
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
import time
import random
import os

app = Flask(__name__)

#prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method','endpoint','status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['endpoint']
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP Errors',
    ['endpoint']
)

APP_INFO = Gauge(
    'app_info',
    'Application information',
    ['version','environment']
)

APP_INFO.labels(version='1.0.0', environment=os.getenv('ENV','dev')).set(1)

@app.route('/')
def home():
    start_time = time.time()

    processing_time = random.uniform(0.01,0.3)
    time.sleep(processing_time)

    if random.random() < 0.05:
        ERROR_COUNT.labels('/').inc()
        REQUEST_COUNT.labels('GET','/','500').inc()
        REQUEST_LATENCY.labels('/').observe(time.time() - start_time)
        return "Internal Server Error", 500

    REQUEST_COUNT.labels('GET','/','200').inc()
    REQUEST_LATENCY.labels('/').observe(time.time() - start_time)
    return f"Hello from Monitoring Demo APP! (v1.0.0)"

@app.route('/health')
def health():
    REQUEST_COUNT.labels('GET','/health','200').inc()
    return Response('{"status": "healthy"}',mimetype='application/json')

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    start_time = time.time()


    time.sleep(random.uniform(0.05,0.5))

    REQUEST_COUNT.labels('GET','/api/users','200').inc()
    REQUEST_LATENCY.labels('/api/users').observe(time.time() - start_time)
    return f'Slow response: {delay:.2f} seconds'

@app.route('/metrics')
def metrics():
    return Response(
        prometheus_client.generate_latest(),
        mimetype='text/plain'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=False)
    