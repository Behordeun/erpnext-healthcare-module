# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest
from unittest.mock import Mock, MagicMock, patch
from lafia.lafiaio.doctype.adverse_event.adverse_event import AdverseEvent


def mocked_requests_get(*args, **kwargs):
	print(args[0])
	class MockResponse:
		def __init__(self, json_data, status_code):
			self.json_data = json_data
			self.status_code = status_code

		def json(self):
			return self.json_data

	if args[0] == 'https://api.lafia.io/fhir/AdverseEvent/620':
			return MockResponse({"key1": "value1"}, 200)
	

	return MockResponse(None, 404)


class TestAdverseEvent(unittest.TestCase):

	data_model = {
	"identifier": "",
	"actuality": "",
	"category": "",
	"event": "",
	"subject_type": "",
	"subject": "",
	"encounter": "",
	"date": "",
	"detected": "",
	"recorded_date": "",
	"resulting_condition": "",
	"location": "",
	"seriousness": "",
	"severity": "",
	"outcome": "",
	"recorder_type": "",
	"recorder": "",
	"contributor_type": "",
	"contributor": "",
	"suspect_entity": "",
	"subject_medical_history_type": "",
	"subject_medical_history": "",
	"reference_document": "",
	"study": "",
	"fhir_serverid": ""
	}

	def test_get_body(self):
		adverseevent = AdverseEvent
		result = self.data_model
		self.assertEqual(adverseevent.get_body(self.data_model).get("actuality"), result.get("actuality"))

	@patch('requests.put', side_effect=mocked_requests_get)
	def test_before_save(self, mocked_requests_get):
		adverseevent = AdverseEvent
		class result:
			status = "partial"
			name = "ADVE-LIO-620"
			fhir_serverid = 620
			get_body = MagicMock(return_value=self.data_model)
		adverseevent.before_save(result)
		result.get_body()
		result.get_body.assert_called_once()

	def test_get_suspect_entity(self):
		adverseevent = AdverseEvent
		copy_self = self.data_model.copy()
		copy_self["get_code"] = MagicMock(return_value={
			"code": "",
			"system": "",
			"display": ""
		})
		suspect_entity_dict = {
			"instance": "",
			"instance_type":"",
			"causality": "",
		}
		suspect_entity_result = {
			"instance": "",
			"causality": [{
				"coding": []
			}]
		}
		self.assertEqual(adverseevent.get_suspect_entity(copy_self, suspect_entity_dict), suspect_entity_result)

if __name__ == '__main__':
    unittest.main()
