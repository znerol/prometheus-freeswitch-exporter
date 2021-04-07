"""
Prometheus collecters for FreeSWITCH.
"""
# pylint: disable=too-few-public-methods

import asyncio
import itertools
import json
import logging

from contextlib import asynccontextmanager

from asgiref.sync import async_to_sync
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.core import GaugeMetricFamily

from freeswitch_exporter.esl import ESL


class ESLProcessInfo():
    """
    Process info async collector
    """

    def __init__(self, esl: ESL):
        self._esl = esl

    async def collect(self):
        """
        Collects FreeSWITCH process info metrics.
        """

        (_, result) = await self._esl.send(
            'api json {"command" : "status", "data" : ""}')
        response = json.loads(result).get('response', {})

        process_info_metric = GaugeMetricFamily(
            'freeswitch_info',
            'FreeSWITCH info',
            labels=['version'])
        if 'version' in response:
            process_info_metric.add_metric([response['version']], 1)

        process_status_metric = GaugeMetricFamily(
            'freeswitch_up',
            'FreeSWITCH ready status',
        )
        if 'systemStatus' in response:
            status = int(response['systemStatus'] == 'ready')
            process_status_metric.add_metric([], status)

        process_memory_metric = GaugeMetricFamily(
            'freeswitch_stack_bytes',
            'FreeSWITCH stack size',
        )
        if 'stackSizeKB' in response:
            memory = response['stackSizeKB'].get('current', 0)
            process_memory_metric.add_metric([], memory * 1024)

        process_session_metrics = []
        if 'sessions' in response:
            for metric in ['total', 'active', 'limit']:
                process_session_metric = GaugeMetricFamily(
                    f'freeswitch_session_{metric}',
                    f'FreeSWITCH {metric} number of sessions',
                )

                value = response['sessions'].get('count', {}).get(metric, 0)
                process_session_metric.add_metric([], value)

                process_session_metrics.append(process_session_metric)

        return itertools.chain([
            process_info_metric,
            process_status_metric,
            process_memory_metric
        ], process_session_metrics)


class ESLChannelInfo():
    """
    Channel info async collector
    """

    def __init__(self, esl: ESL):
        self._esl = esl
        self._log = logging.getLogger(__name__)

    async def collect(self):
        """
        Collects channel metrics.
        """

        channel_metrics = {
            'variable_rtp_audio_in_raw_bytes': GaugeMetricFamily(
                'rtp_audio_in_raw_bytes_total',
                'Total number of bytes received via this channel.',
                labels=['id']),
            'variable_rtp_audio_out_raw_bytes': GaugeMetricFamily(
                'rtp_audio_out_raw_bytes_total',
                'Total number of bytes sent via this channel.',
                labels=['id']),
            'variable_rtp_audio_in_media_bytes': GaugeMetricFamily(
                'rtp_audio_in_media_bytes_total',
                'Total number of media bytes received via this channel.',
                labels=['id']),
            'variable_rtp_audio_out_media_bytes': GaugeMetricFamily(
                'rtp_audio_out_media_bytes_total',
                'Total number of media bytes sent via this channel.',
                labels=['id']),
            'variable_rtp_audio_in_packet_count': GaugeMetricFamily(
                'rtp_audio_in_packets_total',
                'Total number of packets received via this channel.',
                labels=['id']),
            'variable_rtp_audio_out_packet_count': GaugeMetricFamily(
                'rtp_audio_out_packets_total',
                'Total number of packets sent via this channel.',
                labels=['id']),
            'variable_rtp_audio_in_media_packet_count': GaugeMetricFamily(
                'rtp_audio_in_media_packets_total',
                'Total number of media packets received via this channel.',
                labels=['id']),
            'variable_rtp_audio_out_media_packet_count': GaugeMetricFamily(
                'rtp_audio_out_media_packets_total',
                'Total number of media packets sent via this channel.',
                labels=['id']),
            'variable_rtp_audio_in_skip_packet_count': GaugeMetricFamily(
                'rtp_audio_in_skip_packets_total',
                'Total number of inbound packets discarded by this channel.',
                labels=['id']),
            'variable_rtp_audio_out_skip_packet_count': GaugeMetricFamily(
                'rtp_audio_out_skip_packets_total',
                'Total number of outbound packets discarded by this channel.',
                labels=['id']),
            'variable_rtp_audio_in_jitter_packet_count': GaugeMetricFamily(
                'rtp_audio_in_jitter_packets_total',
                'Total number of ? packets in this channel.',
                labels=['id']),
            'variable_rtp_audio_in_dtmf_packet_count': GaugeMetricFamily(
                'rtp_audio_in_dtmf_packets_total',
                'Total number of ? packets in this channel.',
                labels=['id']),
            'variable_rtp_audio_out_dtmf_packet_count': GaugeMetricFamily(
                'rtp_audio_out_dtmf_packets_total',
                'Total number of ? packets in this channel.',
                labels=['id']),
            'variable_rtp_audio_in_cng_packet_count': GaugeMetricFamily(
                'rtp_audio_in_cng_packets_total',
                'Total number of ? packets in this channel.',
                labels=['id']),
            'variable_rtp_audio_out_cng_packet_count': GaugeMetricFamily(
                'rtp_audio_out_cng_packets_total',
                'Total number of ? packets in this channel.',
                labels=['id']),
            'variable_rtp_audio_in_flush_packet_count': GaugeMetricFamily(
                'rtp_audio_in_flush_packets_total',
                'Total number of ? packets in this channel.',
                labels=['id']),
            'variable_rtp_audio_in_largest_jb_size': GaugeMetricFamily(
                'rtp_audio_in_jitter_buffer_bytes_max',
                'Largest jitterbuffer size in this channel.',
                labels=['id']),
            'variable_rtp_audio_in_jitter_min_variance': GaugeMetricFamily(
                'rtp_audio_in_jitter_seconds_min',
                'Minimal jitter in seconds.',
                labels=['id']),
            'variable_rtp_audio_in_jitter_max_variance': GaugeMetricFamily(
                'rtp_audio_in_jitter_seconds_max',
                'Maximum jitter in seconds.',
                labels=['id']),
            'variable_rtp_audio_in_jitter_loss_rate': GaugeMetricFamily(
                'rtp_audio_in_jitter_loss_rate',
                'Ratio of lost packets due to inbound jitter.',
                labels=['id']),
            'variable_rtp_audio_in_jitter_burst_rate': GaugeMetricFamily(
                'rtp_audio_in_jitter_burst_rate',
                'Ratio of packet bursts due to inbound jitter.',
                labels=['id']),
            'variable_rtp_audio_in_mean_interval': GaugeMetricFamily(
                'rtp_audio_in_mean_interval_seconds',
                'Mean interval in seconds of inbound packets',
                labels=['id']),
            'variable_rtp_audio_in_flaw_total': GaugeMetricFamily(
                'rtp_audio_in_flaw_total',
                'Total number of flaws detected in the channel',
                labels=['id']),
            'variable_rtp_audio_in_quality_percentage': GaugeMetricFamily(
                'rtp_audio_in_quality_percent',
                'Audio quality in percent',
                labels=['id']),
            'variable_rtp_audio_in_mos': GaugeMetricFamily(
                'rtp_audio_in_quality_mos',
                'Audio quality as Mean Opinion Score, (between 1 and 5)',
                labels=['id']),
            'variable_rtp_audio_rtcp_octet_count': GaugeMetricFamily(
                'rtcp_audio_bytes_total',
                'Total number of rtcp bytes in this channel.',
                labels=['id']),
            'variable_rtp_audio_rtcp_packet_count': GaugeMetricFamily(
                'rtcp_audio_packets_total',
                'Total number of rtcp packets in this channel.',
                labels=['id']),
        }

        channel_info_metric = GaugeMetricFamily(
            'rtp_channel_info',
            'FreeSWITCH RTP channel info',
            labels=['id', 'name', 'user_agent'])

        millisecond_metrics = [
            'variable_rtp_audio_in_jitter_min_variance',
            'variable_rtp_audio_in_jitter_max_variance',
            'variable_rtp_audio_in_mean_interval',
        ]

        # This loop is potentially running while calls are being dropped and
        # new calls are established. This will lead to some failing api
        # requests. In that case it is better to just skip scraping for that
        # call and continue with the next one in order to avoid failing the
        # whole scrape.
        (_, result) = await self._esl.send('api show calls as json')
        for row in json.loads(result).get('rows', []):
            uuid = row['uuid']

            await self._esl.send(f'api uuid_set_media_stats {uuid}')
            (_, result) = await self._esl.send(f'api uuid_dump {uuid} json')

            if result.startswith("-ERR "):
                self._log.debug(
                    "Got error while scraping call stats for %s: %s",
                    uuid,
                    result.strip()
                )
                continue

            channelvars = json.loads(result)

            label_values = [uuid]
            for key, metric_value in channelvars.items():
                if key in millisecond_metrics:
                    metric_value = float(metric_value) / 1000.
                if key in channel_metrics:
                    channel_metrics[key].add_metric(
                        label_values, metric_value)

            user_agent = channelvars.get('variable_sip_user_agent', 'Unknown')
            channel_info_label_values = [uuid, row['name'], user_agent]
            channel_info_metric.add_metric(
                channel_info_label_values, 1)

        return itertools.chain(
            channel_metrics.values(),
            [channel_info_metric])


class ChannelCollector():
    """
    Collects channel statistics.

    # HELP freeswitch_version_info FreeSWITCH version info
    # TYPE freeswitch_version_info gauge
    freeswitch_version_info{release="15",repoid="7599e35a",version="4.4"} 1.0
    """

    def __init__(self, host, port, password):
        self._host = host
        self._port = port
        self._password = password

    @asynccontextmanager
    async def _connect(self):
        reader, writer = await asyncio.open_connection(self._host, self._port)
        try:
            esl = ESL(reader, writer)
            await esl.initialize()
            await esl.login(self._password)
            yield esl
        finally:
            writer.close()
            await writer.wait_closed()

    @async_to_sync
    async def collect(self):  # pylint: disable=missing-docstring
        async with self._connect() as esl:
            return itertools.chain(
                await ESLProcessInfo(esl).collect(),
                await ESLChannelInfo(esl).collect())


def collect_esl(config, host):
    """Scrape a host and return prometheus text format for it (asinc)"""

    port = config.get('port', 8021)
    password = config.get('password', 'ClueCon')

    registry = CollectorRegistry()
    registry.register(ChannelCollector(host, port, password))
    return generate_latest(registry)
