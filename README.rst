Prometheus FreeSWITCH Exporter
==============================

|Build Status| |Package Version|

This is an exporter that exposes information gathered from FreeSWITCH for use
by the Prometheus monitoring system.

Installation
------------

.. code:: shell

    pip install prometheus-freeswitch-exporter

Usage
-----

::

    usage: freeswitch_exporter [-h] [config] [port]

    positional arguments:
      config      Path to configuration file (esl.yml)
      port        Port on which the exporter is listening (9724)
      address     Address to which the exporter will bind

    optional arguments:
      -h, --help  show this help message and exit

Use `::` for the `address` argument in order to bind to both IPv6 and IPv4
sockets on dual stacked machines.

Visit http://localhost:9724/esl?target=1.2.3.4 where 1.2.3.4 is the IP of
FreeSWITCH to get metrics from. Specify the ``module`` request parameter, to
choose which module to use from the config file.

The ``target`` request parameter defaults to ``localhost``. Hence if
``freeswitch_exporter`` is deployed directly on the FreeSWITCH host, ``target``
can be omitted.

See the wiki_  for more examples and docs.

Authentication
--------------

Example ``esl.yml``

.. code:: yaml

    default:
        port: 8021  # default port, can be omitted
        password: ClueCon

The configuration is passed directly into `greenswitch.InboundESL()`_.

FreeSWITCH Configuration
------------------------

For security reasons it is essential to change the default passwort in
FreeSWITCH `autoload_configs/event_socket.conf.xml`.

Prometheus Configuration
------------------------

The FreeSWITCH exporter can be deployed either directly on a FreeSWITCH node or
onto a separate machine.

Example config for FreeSWITCH exporter running on FreeSWITCH node:

.. code:: yaml

    scrape_configs:
      - job_name: 'freeswitch'
        static_configs:
          - targets:
            - 192.168.1.2:9724  # FreeSWITCH node with FreeSWITCH exporter.
            - 192.168.1.3:9724  # FreeSWITCH node with FreeSWITCH exporter.
        metrics_path: /esl
        params:
          module: [default]

Example config for FreeSWITCH exporter running on Prometheus host:

.. code:: yaml

    scrape_configs:
      - job_name: 'freeswitch'
        static_configs:
          - targets:
            - 192.168.1.2  # FreeSWITCH node.
            - 192.168.1.3  # FreeSWITCH node.
        metrics_path: /esl
        params:
          module: [default]
        relabel_configs:
          - source_labels: [__address__]
            target_label: __param_target
          - source_labels: [__param_target]
            target_label: instance
          - target_label: __address__
            replacement: 127.0.0.1:9724  # FreeSWITCH exporter.

Grafana Dashboards
------------------

None yet.

.. |Build Status| image:: https://travis-ci.org/znerol/prometheus-freeswitch-exporter.svg?branch=master
   :target: https://travis-ci.org/znerol/prometheus-freeswitch-exporter
.. |Package Version| image:: https://img.shields.io/pypi/v/prometheus-freeswitch-exporter.svg
   :target: https://pypi.python.org/pypi/prometheus-freeswitch-exporter
.. _wiki: https://github.com/znerol/prometheus-freeswitch-exporter/wiki
.. _`greenswitch.InboundESL()`: https://pypi.org/project/greenswitch/
