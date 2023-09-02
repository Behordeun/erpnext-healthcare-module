
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest, os
from unittest.mock import Mock, MagicMock, patch
from lafia.api.practitioner.practitioner import get_telecom, practitioner_lafia_after_save, get_phone, get_practitioner_qualifications, get_codeable_concept, get_qualifications, get_addresses, get_relationship_code, get_period, get_practitioner_communication, get_communication_code, practitioner_lafia_before_insert_script, get_email
from lafia.api.patient.test_patient import mock_get_site_name, mock_get_producer

# def mocked_get_last_doc(*args, **kwargs):
# 	print(args[0])
# 	class MockResponse:
# 			def __init__(self, json_data, status_code):
# 					self.json_data = json_data
# 					self.status_code = status_code

# 			def json(self):
# 					return self.json_data

# 	if args[0] == 'https://api.lafia.io/fhir/Encounter/223':
# 			return MockResponse({"key1": "value1"}, 200)

# 	return MockResponse(None, 404)
test_system = "urn:ietf:bcp:47"

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

def mocked_get_doc(*args, **kwargs):
	class MockGetDoc:
			code = "Eng-GB"
			display = "Eng-GB"
			gender = "Male"
			language = [{"relationship": "Father"}]

			def __init__(self, doctype, name):
					self.name = name
					self.doctype = doctype
					self.fullname = ""
					self.telecom = ""
					self.addresses = ""
					self.system = test_system
					self.period = ""
					self.display = "Eng-GB"
			
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

class TestPractitioner(unittest.TestCase):

	def test_get_addresses(self):
		address_list = [
			{
				"city": "City",
				"country": "Country",
				"postal_code": "Postal Code",
				"state": "State",
				"district": "District",
				"line": "Line 1,Line 2",
				"type": "type",
				"use": "use",
				"text": "text"
			}
		]
		address_result = [
			{
				"use": "use",
				"type": "type",
				# "text": "text",
				"line": ["Line 1", "Line 2"],
				"country": "Country",
				"city": "City",
				"district": "District",
				"state": "State",
				"postalCode": "Postal Code",
				"period": {'start': '', 'end': ''}
			}
		]
		addresses = get_addresses(address_list)
		self.assertEqual(addresses, address_result)

	def test_get_relationship_code(self):
		relationship_code_list = {
				"code": "code",
				"system": "system",
				"display": "display"
		}
		relationship_code_result = {
				"code": "code",
				"system": "system",
				"display": "display"
		}
		relationship_code = get_relationship_code(relationship_code_list)
		self.assertEqual(relationship_code, relationship_code_result)

	def test_get_period(self):
		period_list = [{
				"start": '2019-01-01 00:00:00+00:00',
				"end": '2019-01-01 00:00:00+00:00'
		}]
		period_result = {
				"start": '2019-01-01T00:00:00+00:00',
				"end": '2019-01-01T00:00:00+00:00'
		}
		period = get_period(period_list)
		self.assertEqual(period, period_result)
	
	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	def test_get_practitioner_communication(self, mock_get_doc):
		practitioner_communication_list = [
			{
				"language": "Eng-GB",
			}
		]
		practitioner_communication_result = [{
					"coding": {
							"code": "Eng-GB",
							"system": test_system,
							"display": "Eng-GB"
					},
					"text": "Eng-GB"
			}
		]
		practitioner_communication = get_practitioner_communication(practitioner_communication_list)
		self.assertEqual(practitioner_communication, practitioner_communication_result)
	
	def test_get_communication_code(self):
		communication_code_obj = {
					"code": "Eng-GB",
					"system": test_system,
					"display": "Eng-GB"
			}
		communication_code_result = {
			"code": "Eng-GB",
			"system": test_system,
			"display": "Eng-GB"
		}
		communication_code = get_communication_code(communication_code_obj)
		self.assertEqual(communication_code, communication_code_result)
	
	def test_get_telecom(self):
		email = '_test@mail.com'
		phone = "12345678"
		
		telecom_result = [
			{
				"system": "email",
      			"use": "home",
      			"rank" : 0,
      			"value": '_test@mail.com'
			},
			{
				"system": "phone",
				"rank": 0,
				"use": "mobile",
				"value": "12345678"
			}
		]
		telecom = get_telecom(email=email,phone=phone)
		self.assertEqual(telecom, telecom_result)

	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	def test_get_practitioner_qualification(self, mock_get_doc):
		practitioner_qualification_list = [
			{
				"code": "code",
				"system": "system",
				"display": "display"
			}
		]
		practitioner_qualification_result = {
					"coding": [{
							"code": "Eng-GB",
							"system": test_system,
							"display": "Eng-GB"
					}],
					"text": "Eng-GB"
			}
		practitioner_qualification = get_practitioner_qualifications(practitioner_qualification_list)
		self.assertEqual(practitioner_qualification, practitioner_qualification_result)

	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	def test_get_codeable_concept(self, mock_get_doc):
		codeable_concept_list = [
			{
				"code": "code",
				"system": "system",
				"display": "display"
			}
		]
		codeable_concept_result = {
					"coding": [{
							"code": "Eng-GB",
							"system": test_system,
							"display": "Eng-GB"
					}],
					"text": "Eng-GB"
			}
		codeable_concept = get_codeable_concept("Qualification", codeable_concept_list)
		self.assertEqual(codeable_concept, codeable_concept_result)
	
	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	def test_get_qualification(self, mock_get_doc):
		qualification_list = [
			{
				"code": "code",
				"system": "system",
				"display": "display",
				"start": "2019-01-01 00:00:00+00:00",
				"end": "2019-01-01 00:00:00+00:00",
				"issuer": "Organization/1"
			}
		]
		qualification_result = [{
					"identifier": [
							{
									"system": "http://example.org/UniversityIdentifier",
									"value": "12345"
							}
					],
					"code": {
						"coding": [{
								"code": "Eng-GB",
								"system": test_system,
								"display": "Eng-GB"
						}],
						"text": "Eng-GB"
					},
					"period": {
						"start": "2019-01-01",
						"end": "2019-01-01"
					},
					"issuer": {
						"display": "Organization/1",
					}
			}]
		qualification = get_qualifications(qualification_list)
		self.assertEqual(qualification, qualification_result)

	@patch('requests.post', side_effect=mocked_requests_get)
	def test_before_insert(self, mock_post):
		class PractitionerInfo:
			email = "user@mail.com"
			first_name = "John"
			id = "123456789"
			mobile_phone = "123456789"
			birthdate = "2019-01-01 00:00:00+00:00"
			last_name = "Doe"
			other_name = "Doe"
			gender = "Male"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
				self.deceased_boolean = 0
				self.deceased_datetime = ""
				self.addresses = ""
				self.contact = ""
			
			def get(self, attr):
					return getattr(self, attr)
		
		practitioner_info = PractitionerInfo()
		practitioner_lafia_before_insert_script(practitioner_info, None)
		self.assertEqual(practitioner_info.fhir_serverid, "123456789")

	def test_get_email(self):
		email_list = [
			{
				"code": "codeGeass",
				"system": "email",
				"value": "stems@mail.com"
			},
			{
				"code": "codeGeass",
				"system": "email",
				"value": "stew@grail.com"
			}
		]
		email_result = ["stems@mail.com", "stew@grail.com"]
		email = get_email(email_list)
		self.assertEqual(email, email_result)

	def test_get_phone(self):
		phone_list = [
			{
				"code": "codeGeass",
				"system": "phone",
				"value": "09085678368"
			},
			{
				"code": "codeGeass",
				"system": "phone",
				"value": "09085878367"
			}
		]
		phone_result = ["09085678368", "09085878367"]
		phone = get_phone(phone_list)
		self.assertEqual(phone, phone_result)


	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	@patch('frappe.utils.get_site_name', side_effect=mock_get_site_name)
	@patch('lafia.api.services.brokers.producer.producer', side_effect=mock_get_producer)
	def test_after_save(self, mock_doc, mock_post, mock_producer):
		class PractitionerInfo:
			email = "user@mail.com"
			first_name = "John"
			id = "123456789"
			mobile_phone = "123456789"
			last_name = "Doe"
			other_name = "Doe"
			user_id = ""
			gender = "Male"
			name = "PAT-LIO-5678"

			def __init__(self):
				self.fhir_serverid = "123456789"
				self.identifier = ""
				self.birthdate = ""
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
		
		practitioner_info = PractitionerInfo()
		practitioner_lafia_after_save(practitioner_info, None)
		self.assertEqual(practitioner_info.fhir_serverid, "123456789")

if __name__ == '__main__':
		unittest.main()
