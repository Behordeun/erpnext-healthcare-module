# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest
from unittest.mock import Mock, MagicMock, patch
from lafia.lafiaio.doctype.detected_issue.detected_issue import DetectedIssue


def mocked_requests_get(*args, **kwargs):
	print(args[0])
	class MockResponse:
		def __init__(self, json_data, status_code):
			self.json_data = json_data
			self.status_code = status_code

		def json(self):
			return self.json_data

	if args[0] == 'https://api.lafia.io/fhir/DetectedIssue/620':
			return MockResponse({"key1": "value1"}, 200)
	

	return MockResponse(None, 404)


class TestDetectedIssue(unittest.TestCase):

	data_model = {
	"identifier": "",
	"status": "",
	"code": "",
	"severity": "",
	"patient": "",
	"identified_datetime": "",
	"identified_period": "",
	"author_type": "",
	"author": "",
	"implicated_type": "",
	"implicated": "",
	"evidence": "",
	"detail": "",
	"reference": "",
	"mitigation": "",
	"fhir_serverid": ""
	}

	def test_get_body(self):
		detectedissue = DetectedIssue
		result = self.data_model
		self.assertEqual(detectedissue.get_body(self.data_model).get("status"), result.get("status"))

	@patch('requests.put', side_effect=mocked_requests_get)
	def test_before_save(self, mocked_requests_get):
		detectedissue = DetectedIssue
		class result:
			status = "registered"
			name = "DIS-LIO-620"
			fhir_serverid = 620
			get_body = MagicMock(return_value=self.data_model)
		detectedissue.before_save(result)
		result.get_body()
		result.get_body.assert_called_once()

	def test_get_evidence(self):
		detectedissue = DetectedIssue
		copy_self = self.data_model.copy()
		copy_self["get_code"] = MagicMock(return_value={
			"code": "",
			"system": "",
			"display": ""
		})
		evidence_dict = {
			"code": "",
			"detail": "",
		}
		evidence_result = {
			"code": [{
				"coding": []
			}],
			"detail": "",
		}
		self.assertEqual(detectedissue.get_evidence(copy_self, evidence_dict), evidence_result)

	def test_get_mitigation(self):
		detectedissue = DetectedIssue
		copy_self = self.data_model.copy()
		copy_self["get_code"] = MagicMock(return_value={
			"code": "",
			"system": "",
			"display": ""
		})
		mitigation_dict = {
			"action": "",
			"date": "",
			"author": "",
		}
		mitigation_result = {
			"action": [{
				"coding": []
			}],
			"date": "",
			"author": "",
		}
		self.assertEqual(detectedissue.get_mitigation(copy_self, mitigation_dict), mitigation_result)

if __name__ == '__main__':
    unittest.main()

