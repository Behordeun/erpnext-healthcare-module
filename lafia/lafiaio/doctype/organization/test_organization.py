# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

from .organization import Organization
import unittest

class TestOrganization(unittest.TestCase):
	def test_before_insert(self):
		class Info:
			email = "@mail.com"
			name1 = "Test Org"
			id = "123456789"
			phone = "123456789"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
				self.type = ""
				self.addresses = ""
				self.partof = ""
			
			def get(self, attr):
					return getattr(self, attr)
		
		info = Info()
		Organization.before_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")

	def test_after_save(self):
		class Info:
			email = "@mail.com"
			name1 = "Test Org"
			id = "123456789"
			phone = "123456789"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
				self.type = ""
				self.addresses = ""
				self.partof = ""
			
			def save(self):
					data = {
							"name": self.name,
							"fhir_serverid": self.fhir_serverid
					}
					return data
			
			def get(self, attr):
					return getattr(self, attr)
		
		info = Info()
		Organization.after_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")


