"""
FreeSWITCH exporter for the Prometheus monitoring system.
"""

import sys
from argparse import ArgumentParser
from freeswitch_exporter.http import start_http_server

def main(args=None):
    """
    Main entry point.
    """

    parser = ArgumentParser()
    parser.add_argument('config', nargs='?', default='esl.yml',
                        help='Path to configuration file (esl.yml)')
    parser.add_argument('port', nargs='?', type=int, default='9724',
                        help='Port on which the exporter is listening (9724)')
    parser.add_argument('address', nargs='?', default='',
                        help='Address to which the exporter will bind')

    params = parser.parse_args(args if args is None else sys.argv[1:])

    start_http_server(params.config, params.port, params.address)
