"""
Prometheus collecters for FreeSWITCH.
"""
# pylint: disable=too-few-public-methods

import csv
import itertools

import greenswitch

from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.core import GaugeMetricFamily


class ChannelCollector():
    """
    Collects channel statistics.

    # HELP freeswitch_version_info FreeSWITCH version info
    # TYPE freeswitch_version_info gauge
    freeswitch_version_info{release="15",repoid="7599e35a",version="4.4"} 1.0
    """

    def __init__(self, esl):
        self._esl = esl

    def collect(self):  # pylint: disable=missing-docstring
        metrics = {
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
            labels=['id', 'name'])

        millisecond_metrics = [
            'variable_rtp_audio_in_jitter_min_variance',
            'variable_rtp_audio_in_jitter_max_variance',
            'variable_rtp_audio_in_mean_interval',
        ]

        result = self._esl.send('api show calls')
        rows = [row.strip() for row in result.data.splitlines()]
        # Filter empty rows
        rows = [row for row in rows if len(row) > 0]
        # Remove the last one (X total.)
        rows = rows[:-1]
        if len(rows) > 1:
            for row in csv.DictReader(rows):
                uuid = row['uuid']

                self._esl.send(f'api uuid_set_media_stats {uuid}')
                result = self._esl.send(f'api uuid_dump {uuid}')
                channelvars = dict([
                    pair.split(': ', 1)
                    for pair
                    in result.data.splitlines()
                    if ':' in pair
                ])

                label_values = [uuid]
                for key, metric_value in channelvars.items():
                    if key in millisecond_metrics:
                        metric_value = float(metric_value) / 1000.
                    if key in metrics:
                        metrics[key].add_metric(label_values, metric_value)

                channel_info_label_values = [uuid, row['name']]
                channel_info_metric.add_metric(channel_info_label_values, 1)

        return itertools.chain(metrics.values(), [channel_info_metric])


def collect_esl(config, host):
    """Scrape a host and return prometheus text format for it"""

    esl = greenswitch.InboundESL(host, **config)
    esl.connect()

    registry = CollectorRegistry()
    registry.register(ChannelCollector(esl))
    result = generate_latest(registry)

    esl.stop()

    return result
