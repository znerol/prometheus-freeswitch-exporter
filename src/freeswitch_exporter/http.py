"""
HTTP API for FreeSWITCH prometheus collector.
"""

import logging
import time
import yaml

from prometheus_client import CONTENT_TYPE_LATEST, Summary, Counter, generate_latest
from werkzeug.exceptions import InternalServerError
from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response

from freeswitch_exporter.collector import collect_esl


class FreeswitchExporterApplication():
    """
    FreeSWITCH prometheus collector HTTP handler.
    """

    # pylint: disable=no-self-use

    def __init__(self, config, duration, errors):
        self._config = config
        self._duration = duration
        self._errors = errors

        self._log = logging.getLogger(__name__)

        self._url_map = Map([
            Rule('/', endpoint='index'),
            Rule('/metrics', endpoint='metrics'),
            Rule('/esl', endpoint='esl'),
        ])

        self._args = {
            'esl': ['module', 'target']
        }

        self._views = {
            'index': self.on_index,
            'metrics': self.on_metrics,
            'esl': self.on_esl,
        }

    def on_esl(self, module='default', target='localhost'):
        """
        Request handler for /esl route
        """

        if module in self._config:
            start = time.time()
            output = collect_esl(self._config[module], target)
            response = Response(output)
            response.headers['content-type'] = CONTENT_TYPE_LATEST
            self._duration.labels(module).observe(time.time() - start)
        else:
            response = Response(f"Module '{module}' not found in config")
            response.status_code = 400

        return response

    def on_metrics(self):
        """
        Request handler for /metrics route
        """

        response = Response(generate_latest())
        response.headers['content-type'] = CONTENT_TYPE_LATEST

        return response

    def on_index(self):
        """
        Request handler for index route (/).
        """

        response = Response(
            """<html>
            <head><title>FreeSWITCH Exporter</title></head>
            <body>
            <h1>FreeSWITCH Exporter</h1>
            <p>Visit <code>/esl?target=1.2.3.4</code> to use.</p>
            </body>
            </html>"""
        )
        response.headers['content-type'] = 'text/html'

        return response

    def view(self, endpoint, values, args):
        """
        Werkzeug views mapping method.
        """

        params = dict(values)
        if endpoint in self._args:
            params.update({key: args[key] for key in self._args[endpoint] if key in args})

        try:
            return self._views[endpoint](**params)
        except Exception as error:  # pylint: disable=broad-except
            self._log.exception("Exception thrown while rendering view")
            self._errors.labels(args.get('module', 'default')).inc()
            raise InternalServerError from error


    @Request.application
    def __call__(self, request):
        urls = self._url_map.bind_to_environ(request.environ)
        view_func = lambda endpoint, values: self.view(endpoint, values, request.args)
        return urls.dispatch(view_func, catch_http_exceptions=True)


def start_http_server(config_path, port, address=''):
    """
    Start a HTTP API server for FreeSWITCH prometheus collector.
    """

    duration = Summary(
        'freeswitch_collection_duration_seconds',
        'Duration of collections by the FreeSWITCH exporter',
        ['module'],
    )
    errors = Counter(
        'freeswitch_request_errors_total',
        'Errors in requests to FreeSWITCH exporter',
        ['module'],
    )

    # Load configuration.
    with open(config_path) as handle:
        config = yaml.safe_load(handle)

    # Initialize metrics.
    for module in config.keys():
        # pylint: disable=no-member
        errors.labels(module)
        # pylint: disable=no-member
        duration.labels(module)

    app = FreeswitchExporterApplication(config, duration, errors)
    run_simple(address, port, app, threaded=True)
