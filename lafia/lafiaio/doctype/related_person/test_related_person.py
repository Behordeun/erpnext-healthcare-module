# Copyright (c) 2022, ParallelScore and Contributors
# See license.txt

# import frappe
from frappe.tests.utils import FrappeTestCase
from .related_person import RelatedPerson


class TestRelatedPerson(FrappeTestCase):
	
	def test_before_insert(self):
		class RelatedInfo:
			email = "related@mail.com"
			first_name = "John"
			id = "123456789"
			phone = "123456789"
			last_name = "Doe"
			other_name = "Doe"
			gender = "Male"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
				self.birthdate = ""
				self.deceased_boolean = 0
				self.deceased_datetime = ""
				self.addresses = ""
				self.contact = ""
			
			def get(self, attr):
					return getattr(self, attr)
		
		info = RelatedInfo()
		RelatedPerson.before_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")

	def test_after_save(self):
		class RelatedInfo:
			email = "user@mail.com"
			first_name = "John"
			id = "123456789"
			phone = "123456789"
			last_name = "Doe"
			other_name = "Doe"
			gender = "Male"
			name = "RE-PER-5678"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
				self.birthdate = ""
				self.deceased_boolean = 0
				self.deceased_datetime = ""
				self.addresses = ""
				self.contact = ""
			
			def save(self):
					data = {
							"name": self.name,
							"fhir_serverid": self.fhir_serverid
					}
					return data
			
			def get(self, attr):
					return getattr(self, attr)
		
		info = RelatedInfo()
		RelatedPerson.after_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")


