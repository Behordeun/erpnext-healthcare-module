# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest
from unittest.mock import Mock, MagicMock, patch
from lafia.lafiaio.doctype.riskassessment.riskassessment import RiskAssessment


def mocked_requests_get(*args, **kwargs):
	print(args[0])
	class MockResponse:
			def __init__(self, json_data, status_code):
					self.json_data = json_data
					self.status_code = status_code

			def json(self):
					return self.json_data

	if args[0] == 'https://api.lafia.io/fhir/RiskAssessment/101':
			return MockResponse({"key1": "value1"}, 200)

	return MockResponse(None, 404)


class TestRiskAssessment(unittest.TestCase):

	data_model = {
	"identifier": "",
	"based_on": "",
	"parent1": "",
	"status": "",
	"method": "",
	"code": "",
	"subject_type": "",
	"subject": "",
	"encounter": "",
	"occurrence_datetime": "",
	"occurrence_period": "",
	"condition": "",
	"performer_type": "",
	"reason_code": "",
	"reason_reference_type": "",
	"reason_reference": "",
	"basis_type": "",
	"basis": "",
	"prediction": "",
	"mitigation": "",
	"note": "",
	"fhir_serverid": ""
	}

	def test_get_body(self):
		riskassessment = RiskAssessment
		result = self.data_model
		self.assertEqual(riskassessment.get_body(self.data_model).get("status"), result.get("status"))

	@patch('requests.put', side_effect=mocked_requests_get)
	def test_before_save(self, mock_put):
		
		print(self.data_model)
		riskassessment = RiskAssessment
		class result:
			status = "in-progress"
			name = "RSKA-LIO-101"
			fhir_serverid = 101
			get_body = MagicMock(return_value=self.data_model)
		riskassessment.before_save(result)
		result.get_body()
		result.get_body.assert_called_once()
		# print(result.get_body)

	def test_get_prediction(self):
		riskassessment = RiskAssessment
		copy_self = self.data_model.copy()
		copy_self["get_code"] = MagicMock(return_value={
			"code": "",
			"system": "",
			"display": ""
		})
		prediction_dict = {
			"outcome": "",
			"probabilityDecimal": "",
			"probabilityRange": "",
			"qualitativeRisk": "",
			"relativeRisk": "",
			"whenPeriod": "",
			"whenRange": "",
			"rationale": ""
		}
		prediction_result = {
			"outcome": [{
				"coding": []
			}],
			"probabilityDecimal": "",
			"probabilityRange": "",
			"qualitativeRisk": [{
				"coding": []
			}],
			"relativeRisk": "",
			"whenPeriod": "",
			"whenRange": "",
			"rationale": ""
		}
		self.assertEqual(riskassessment.get_prediction(copy_self, prediction_dict), prediction_result)

if __name__ == '__main__':
    unittest.main()
