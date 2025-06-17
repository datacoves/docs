# from prometheus_client import make_wsgi_app
from flask import Flask
from prometheus_client import Gauge, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

g = Gauge(
    "kube_node_status_condition",
    "Description node condition",
    ["node", "condition", "status"],
)
g.labels(node="test-app", condition="DiskPressure", status="true").set(1)

# Create my app
app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Datacoves Test App!</p>"


# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})
