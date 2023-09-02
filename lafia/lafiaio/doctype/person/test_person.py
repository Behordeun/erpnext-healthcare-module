# Copyright (c) 2022, ParallelScore and Contributors
# See license.txt

# import frappe
from frappe.tests.utils import FrappeTestCase
from .person import Person


class TestPerson(FrappeTestCase):
	
	def test_before_insert(self):
		class Info:
			email = "@mail.com"
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
		
		info = Info()
		Person.before_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")

	def test_after_save(self):
		class Info:
			email = "user@mail.com"
			first_name = "John"
			id = "123456789"
			phone = "123456789"
			last_name = "Doe"
			other_name = "Doe"
			gender = "Male"
			name = "PER-5678"

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
		
		info = Info()
		Person.after_insert(info)
		self.assertEqual(info.fhir_serverid, "123456789")

