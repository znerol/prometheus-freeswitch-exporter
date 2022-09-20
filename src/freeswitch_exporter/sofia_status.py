# -*- coding: utf-8 -*-
# vim:set noet ts=4 sw=4 fenc=utf-8 ff=unix ft=python:
import logging

_log = logging.getLogger("sofia_status")

sofia_profile_status_fields_map = {
	'CALLS-IN': (int, 'calls_in'),
	'CALLS-OUT': (int, 'calls_out'),
	'CNG': (int, 'congestion'),
	'Domain Name': (str, 'domain_name'),
	'FAILED-CALLS-IN': (int, 'failed_calls_in'),
	'FAILED-CALLS-OUT': (int, 'failed_calls_out'),
	'MAX-DIALOG': (int, 'max_dialog'),
	'Name': (str, 'name'),
	'REGISTRATIONS': (int, 'registrations'),
	'SESSION-TO': (int, 'session_to')
}


def split_sofia_status_data(lines: str) -> list[str]:
	return list(filter(None, [x.strip() for x in lines.split('\t')]))


class SofiaProfile(object):
	def __init__(self, name, uri, state):
		self.name = name
		self.uri = uri
		self.state = state

	@classmethod
	def profile_list_from_sofia_status(cls, data: str):
		for line in data.splitlines():
			fields = split_sofia_status_data(line)

			if len(fields) == 4 and fields[1] == "profile":
				_log.info("found profile %s", fields[0])
				yield cls(fields[0], fields[2], fields[3])


class SofiaProfileStatus(object):
	name: str
	domain_name: str
	congestion: int
	session_to: int
	max_dialog: int
	calls_in: int
	failed_calls_in: int
	calls_out: int
	failed_calls_out: int
	registrations: int

	def __init__(self, data: str):
		profile_name = "(unknown)"

		if data.startswith("-ERR "):
			raise ValueError("Error while reading sofia profile status: %s" % data)

		for line in data.splitlines():
			fields = split_sofia_status_data(line)

			if len(fields) == 2:
				try:
					field_type, field_name = sofia_profile_status_fields_map[fields[0]]
					setattr(self, field_name, field_type(fields[1]))

					if field_name == "name":
						profile_name = fields[1]

				except KeyError:
					continue
