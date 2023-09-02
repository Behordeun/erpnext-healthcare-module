# Copyright (c) 2022, ParallelScore and Contributors
# See license.txt

# import frappe
from unittest import result
from frappe.tests.utils import FrappeTestCase
from .organization_affiliation import OrganizationAffiliation


class TestOrganizationAffiliation(FrappeTestCase):
	def setUp(self):
		self.data = {
			"contact": [
				{
					'name1': 'test',
					'purpose': 'Billing',
					'email': '',
					'phone': '',
					'address': '5, Long Str',
					'city': 'Dallas',
					'country': 'US',
					'organization': ''

				}
			]
		}

	def test_get_contact(self):
		result = [{
			'name': [{'text':'test'}],
			'purpose': {'text':'Billing'},
			'telecom': [],
			'address': {
				'text': '5, Long Str',
				'city': 'Dallas',
				'country': 'US',
			},
			'organization': ''

		}]
		a = OrganizationAffiliation.get_contact(self.data)
		self.assertEqual(a,result)

	def test_before_insert(self):
		class Info:
			email = "@mail.com"
			organization = "Test Org"
			id = "123456789"
			phone = "123456789"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
				self.code = ""
				self.location = ""
				self.contact = ""
			
			def get(self, attr):
					return getattr(self, attr)
		
		info = Info()
		OrganizationAffiliation.before_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")

	def test_after_save(self):
		class Info:
			email = "@mail.com"
			organization = "Test Org"
			id = "123456789"
			phone = "123456789"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
				self.code = ""
			
			def save(self):
					data = {
							"name": self.name,
							"fhir_serverid": self.fhir_serverid
					}
					return data
			
			def get(self, attr):
					return getattr(self, attr)
		
		info = Info()
		OrganizationAffiliation.after_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")

