
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest, os
from dotenv import load_dotenv
from unittest.mock import Mock, MagicMock, patch
from lafia.api.patient.patient import get_coms, get_addresses, get_email, get_phone, get_telecom_table, get_relationship_code, patient_lafia_before_insert_script, get_patient_relationship, get_patient_info, get_patient_contact, patient_lafia_after_save

load_dotenv()

test_email1 = "stem@mail.com"

def mocked_get_last_doc(*args, **kwargs):
	class MockGetLastDoc:
			doctype = "Patient",
			name = "ENC-LIO-223",
			fhir_serverid = "223",

			def __init__(self, doctype=doctype, filters=None):
					self.email = filters.get("email")
			
			def save(self):
					data = {
							"status": self.status,
							"name": self.name,
							"fhir_serverid": self.fhir_serverid
					}
					return data
	return MockGetLastDoc(doctype=kwargs["doctype"], filters=kwargs["filters"])


def mock_get_site_name(*args, **kwargs):
	class MockSiteName:
		name = "test"
		def __init__(self, name):
			self.name = name
	site_name = MockSiteName("test")
	return site_name.name

def mock_get_producer(*args, **kwargs):
	class MockProducer:
		name = "test"
		def __init__(self, name):
			self.name = name
	producer = MockProducer("test")
	return producer

def mocked_get_doc(*args, **kwargs):
	class MockGetDoc:
			code = "codeGeass"
			system = "system2"
			gender = "Male"
			relationship = [{"relationship": "Father"}]

			def __init__(self, doctype, name):
					self.name = name
					self.doctype = doctype
					self.fullname = ""
					self.telecom = ""
					self.addresses = ""
					self.period = ""
					self.display = "Father"
			
			def save(self):
					data = {
							"status": self.status,
							"name": self.name,
							"fhir_serverid": self.fhir_serverid
					}
					return data
			def get(self, attr):
					return getattr(self, attr)
	return MockGetDoc(args[0], args[1])



def mocked_requests_get(*args, **kwargs):
	print("kwargs", kwargs)
	class MockResponse:
		def __init__(self, json_data, status_code):
				self.json_data = json_data
				self.status_code = status_code

		def json(self):
			self.json_data["fhir_serverid"] = "123456789"
			return self.json_data

	if args[0] == '{0}/fhir/Patient'.format(os.environ.get("LAFIA_SERVER_URL")):
			return MockResponse(kwargs.get("json"), 201)

	return MockResponse(None, 404)

class TestPatient(unittest.TestCase):
	maxDiff = None

	@patch('frappe.get_last_doc', side_effect=mocked_get_last_doc)
	def test_get_patient_info(self, mock_doc):
		email = "patient@hospital.com"
		patient_info = get_patient_info(email)
		self.assertEqual(patient_info.email, email)
	

	def test_get_telecom_table(self):
		telecom_table_list = [{
				"use": "code",
				"system": "system",
				"value": "display"
		}]
		telecom_table = get_telecom_table(telecom_table_list)
		self.assertEqual(telecom_table, telecom_table_list)


	def test_get_addresses(self):
		address_list = [
			{
				"city": "Nakama",
				"country": "Japan",
				"postal_code": "Postal Code 12",
				"state": "Osaka",
				"district": "Nekoma",
				"line": "Karakuramachi",
				"type": "type1",
				"use": "use2",
				"text": "text12"
			}
		]
		address_result = [
			{
				"use": "use2",
				"type": "type1",
				# "text": "text12",
				"country": "Japan",
				"line": ['Karakuramachi'],
				"city": "Nakama",
				"district": "Nekoma",
				"state": "Osaka",
				"postalCode": "Postal Code 12",
				"period": {'start': '', 'end': ''}
			}
		]
		addresses = get_addresses(address_list)
		self.assertEqual(addresses, address_result)

	def test_get_relationship_code(self):
		relationship_code_list = {
				"code": "codeGeass",
				"system": "system2",
				"display": "display3"
		}
		relationship_code_result = {
				"code": "codeGeass",
				"system": "system2",
				"display": "display3"
		}
		relationship_code = get_relationship_code(relationship_code_list)
		self.assertEqual(relationship_code, relationship_code_result)

	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	def test_get_patient_relationship(self, mock_doc):
		relationship_list = [{"relationship": "Father"}]
		relationship_list_result = [{
				"coding":{
					"code": "codeGeass",
					"system": "system2",
					"display": "Father"
				},
				"text": "Father"
		}]
		relationships = get_patient_relationship(relationship_list)
		self.assertEqual(relationships, relationship_list_result)

	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	def test_get_patient_contact(self, mock_doc):
		contact_list = [
			{
				"gender": "Male",
				"relationship": [{"relationship": "Father"}]
			}
		]
		contact_list_result = [{
			"addresses": [],
			"gender": "Male",
			"name": [],
			"period": "",
			"relationship": [{
				"coding":{
					"code": "codeGeass",
					"system": "system2",
					"display": "Father"
				},
				"text": "Father"
			}],
			"telecom": []
		}]
		contacts = get_patient_contact(contact_list)
		self.assertEqual(contacts, contact_list_result)

	@patch('requests.post', side_effect=mocked_requests_get)
	def test_before_insert(self, mock_post):
		class PatientInfo:
			email = "user@mail.com"
			first_name = "John"
			id = "123456789"
			phone = "123456789"
			last_name = "Doe"
			other_name = "Doe"
			sex = "Male"

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
		
		patient_info = PatientInfo()
		patient_lafia_before_insert_script(patient_info, None)
		self.assertEqual(patient_info.fhir_serverid, "123456789")

	def test_get_phone(self):
		phone_list = [
			{
				"code": "codeGeass",
				"system": "phone",
				"value": "09085678367"
			},
			{
				"code": "codeGeass",
				"system": "phone",
				"value": "09085878367"
			}
		]
		phone_result = ["09085678367", "09085878367"]
		phone = get_phone(phone_list)
		self.assertEqual(phone, phone_result)

	def test_get_email(self):
		email_list = [
			{
				"code": "codeGeass",
				"system": "email",
				"value": test_email1
			},
			{
				"code": "codeGeass",
				"system": "email",
				"value": "stew@grail.com"
			}
		]
		email_result = [test_email1, "stew@grail.com"]
		email = get_email(email_list)
		self.assertEqual(email, email_result)

	def test_get_coms(self):
		telecom_list = [
			{
				"code": "codeGeass",
				"system": "phone",
				"value": test_email1
			},
			{
				"code": "codeGeass",
				"system": "telecom",
				"value": "stew@grail.com"
			}
		]
		telecom = get_coms("phone", telecom_list)
		self.assertEqual(telecom, test_email1)


	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	@patch('frappe.utils.get_site_name', side_effect=mock_get_site_name)
	@patch('lafia.api.services.brokers.producer.producer', side_effect=mock_get_producer)
	def test_after_save(self, mock_doc, mock_post, mock_producer):
		class PatientInfo:
			email = "user@mail.com"
			first_name = "John"
			id = "123456789"
			phone = "123456789"
			last_name = "Doe"
			other_name = "Doe"
			user_id = ""
			sex = "Male"
			name = "PAT-LIO-5678"

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
		
		patient_info = PatientInfo()
		patient_lafia_after_save(patient_info, None)
		self.assertEqual(patient_info.fhir_serverid, "123456789")

if __name__ == '__main__':
	unittest.main()
