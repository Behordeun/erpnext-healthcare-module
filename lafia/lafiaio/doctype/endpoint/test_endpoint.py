# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

from .endpoint import Endpoint
import unittest

class TestEndpoint(unittest.TestCase):
	def test_before_insert(self):
		class Info:
			email = "@mail.com"
			name1 = "Test Endpoint"
			id = "123456789"
			phone = "123456789"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
			
			def get(self, attr):
					return getattr(self, attr)
		
		info = Info()
		Endpoint.before_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")

	def test_after_save(self):
		class Info:
			email = "@mail.com"
			name1 = "Test Endpoint"
			id = "123456789"
			phone = "123456789"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
			
			def save(self):
					data = {
							"name": self.name,
							"fhir_serverid": self.fhir_serverid
					}
					return data
			
			def get(self, attr):
					return getattr(self, attr)
		
		info = Info()
		Endpoint.after_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")




