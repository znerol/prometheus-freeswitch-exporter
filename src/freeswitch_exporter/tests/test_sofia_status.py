# -*- coding: utf-8 -*-
# vim:set noet ts=4 sw=4 fenc=utf-8 ff=unix ft=python:
from unittest import TestCase
from freeswitch_exporter.sofia_status import SofiaProfile, SofiaProfileStatus

sofia_profiles = """
					 Name	   Type	                                      Data	State
=================================================================================================
			  128.66.20.6	  alias	                                  internal	ALIASED
			 v4.test2.net	  alias	                                  internal	ALIASED
			 v6.test2.net	  alias	                                internalv6	ALIASED
	  [2001:0db8:63ce::6]	  alias	                                internalv6	ALIASED
				 internet	profile	             sip:mod_sofia@127.0.0.1:45080	RUNNING (0)
				 internet	profile	             sip:mod_sofia@127.0.0.1:45081	RUNNING (0) (TLS)
internet::toronto.sip1.py	gateway	  sip:123456_abcdefghij@abcdefg4.sip1.py:5061	REGED
	internet::telesip.pyc	gateway	                  sip:12345@123.101.21.231	REGED
internet::montreal.sip1.py	gateway	  sip:123456_abcdefghij@zywxutva2.sip1.py:5061	REGED
				  default	  alias	                                  internal	ALIASED
			10.10.203.146	  alias	                                     test4	ALIASED
			   internalv6	profile	    sip:mod_sofia@[2001:0db8:63ce::6]:5060	RUNNING (0)
			   internalv6	profile	    sip:mod_sofia@[2001:0db8:63ce::6]:5061	RUNNING (0) (TLS)
	 masterpi.i.test2.net	  alias	                                  internal	ALIASED
					test4	profile	             sip:mod_sofia@10.10.0.33:5070	RUNNING (0)
		test4::casrvfswr1	gateway	           sip:chez@casrvfswr1.ab.test1.py	REGED
	 test4::fusionpbx-499	gateway	             sip:499@casrvpbx1.ab.test1.py	REGED
	 test4::fusionpbx-483	gateway	             sip:483@casrvpbx1.ab.test1.py	REGED
				 internal	profile	            sip:mod_sofia@128.66.20.6:5060	RUNNING (0)
				 internal	profile	            sip:mod_sofia@128.66.20.6:5061	RUNNING (0) (TLS)
=================================================================================================
4 profiles 7 aliases
"""
profiles_name = ('internal', 'internet', 'internalv6', 'test4')

sofia_profile_status = """

=================================================================================================
Name             	internal
Domain Name      	N/A
Auto-NAT         	false
DBName           	sofia_reg_internal
Pres Hosts       	128.66.20.6,128.66.20.6
Dialplan         	XML
Context          	default
Challenge Realm  	auto_from
RTP-IP           	128.66.20.6
Ext-RTP-IP       	128.66.20.6
SIP-IP           	128.66.20.6
Ext-SIP-IP       	128.66.20.6
URL              	sip:mod_sofia@128.66.20.6:5060
BIND-URL         	sip:mod_sofia@128.66.20.6:5060;maddr=128.66.20.6;transport=udp,tcp
TLS-URL          	sip:mod_sofia@128.66.20.6:5061
TLS-BIND-URL     	sips:mod_sofia@128.66.20.6:5061;maddr=128.66.20.6;transport=tls
HOLD-MUSIC       	tone_stream://%(100,100,800);%(100,100,800);%(100,5000,800);loops=-1
OUTBOUND-PROXY   	N/A
CODECS IN        	G722,PCMU
CODECS OUT       	G722,PCMU
TEL-EVENT        	101
DTMF-MODE        	rfc2833
CNG              	13
SESSION-TO       	0
MAX-DIALOG       	0
NOMEDIA          	false
LATE-NEG         	true
PROXY-MEDIA      	false
ZRTP-PASSTHRU    	false
AGGRESSIVENAT    	false
CALLS-IN         	0
FAILED-CALLS-IN  	0
CALLS-OUT        	3
FAILED-CALLS-OUT 	2
REGISTRATIONS    	1

"""

sofia_profile_status_fields = {
	"name": str,
	"domain_name": str,
	"congestion": int,
	"session_to": int,
	"max_dialog": int,
	"calls_in": int,
	"failed_calls_in": int,
	"calls_out": int,
	"failed_calls_out": int,
	"registrations": int,
}


class TestSofiaProfiles(TestCase):

	def test_profile_list_has_no_empty_fields(self):
		for profile in SofiaProfile.profile_list_from_sofia_status(sofia_profiles):
			self.assertGreater(len(profile.name), 0)
			self.assertGreater(len(profile.uri), 0)
			self.assertGreater(len(profile.state), 0)

	def test_profile_list_contains_only_profiles(self):
		for profile in SofiaProfile.profile_list_from_sofia_status(sofia_profiles):
			if profile.name not in profiles_name:
				self.fail(f"profile {profile.name} shouldn't be in profiles list")

	def test_profile_list_contains_all_profile_names(self):
		names = set(profiles_name)

		for profile in SofiaProfile.profile_list_from_sofia_status(sofia_profiles):
			names.discard(profile.name)

			if len(names) == 0:
				break

		if len(names) > 0:
			self.fail(f"didn't find all profiles in sofia status, missing {names}")


class TestSofiaProfileStatus(TestCase):

	def test_all_fields_are_filled(self):
		profile_status = SofiaProfileStatus(sofia_profile_status)

		for field_name, field_type in sofia_profile_status_fields.items():
			field_value = getattr(profile_status, field_name)
			field_value_type = type(field_value)

			if field_value_type != field_type:
				self.fail(f"type for field {field_name} is {field_value_type} instead of {field_type}")


