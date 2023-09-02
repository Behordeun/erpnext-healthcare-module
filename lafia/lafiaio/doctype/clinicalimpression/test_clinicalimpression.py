# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest, os

from dotenv import load_dotenv
from unittest.mock import Mock, MagicMock, patch
from lafia.lafiaio.doctype.clinicalimpression.clinicalimpression import ClinicalImpression

load_dotenv()

def mocked_requests_get(*args, **kwargs):
	print(args[0])
	class MockResponse:
			def __init__(self, json_data, status_code):
					self.json_data = json_data
					self.status_code = status_code

			def json(self):
					return self.json_data

	if args[0] == '{0}/fhir/ClinicalImpression/474'.format(os.environ.get('LAFIA_SERVER_URL')):
			return MockResponse({"key1": "value1"}, 200)
	print("Errororrrorro")

	return MockResponse(None, 404)
class TestClinicalImpression(unittest.TestCase):

	data_model = {
		"identifier": "",
		"status": "in-progress",
		"statusreason": "",
		"code": "",
		"description": "",
		"subject_type": "",
		"subject": "",
		"encounter": "",
		"effectivedatetime": "",
		"effective_period": "",
		"date": "",
		"assessor_type": "",
		"assessor": "",
		"previous": "",
		"problem_type": "",
		"problem": "",
		"investigation": "",
		"protocol": "",
		"summary": "",
		"finding": "",
		"prognosiscodeableconcept": "",
		"prognosisreference": "",
		"supportinginfo": "",
		"note": "",
		"fhir_serverid": ""
	}

	def test_get_body(self):
		clinicalimpression = ClinicalImpression
		result = self.data_model
		self.assertEqual(clinicalimpression.get_body(self.data_model).get("status"), result.get("status"))

	@patch('requests.put', side_effect=mocked_requests_get)
	def test_before_save(self, mock_put):
		print("Ground0")
		print(self.data_model)
		clinicalimpression = ClinicalImpression
		result = {
			"status": "in-progress",
			"name": "CLI-LIO-474",
			"fhir_serverid": "474",
			"get_body": MagicMock(return_value=self.data_model)
		}
		clinicalimpression.before_save(result)
		result.get("get_body").assert_called_once()

	def test_get_investigation(self):
		clinicalimpression = ClinicalImpression
		copy_self = self.data_model.copy()
		copy_self["get_code"] = MagicMock(return_value={
			"code": "",
			"system": "",
			"display": ""
		})
		investigation_dict = {
			"code": "",
			"item": "",
			"item_type": "",
		}
		investigation_result = {
			"code": {
				"coding": []
			},
			"item": ""
		}
		self.assertEqual(clinicalimpression.get_investigation(copy_self, investigation_dict), investigation_result)

	def test_get_finding(self):
		clinicalimpression = ClinicalImpression
		copy_self = self.data_model.copy()
		copy_self["get_code"] = MagicMock(return_value={
			"code": "",
			"system": "",
			"display": ""
		})
		copy_self["get_optional_doctype"] = MagicMock(return_value={ "reference": "Patient/266" })
		finding_dict = {
			"itemcodeableConcept": "",
			"itemreference": "",
			"itemreference_type": "Patient_LafiaIO",
			"basis": "On the Basis of our lord Jesus",
		}
		finding_result = {
			"itemCodeableConcept": {
				"coding": []
			},
			"itemReference": [],
			"basis": "On the Basis of our lord Jesus",
		}
		self.assertEqual(clinicalimpression.get_finding(self.data_model, finding_dict), finding_result)

if __name__ == '__main__':
    unittest.main()
