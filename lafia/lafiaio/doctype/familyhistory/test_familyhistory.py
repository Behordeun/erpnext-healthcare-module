
# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest
from unittest.mock import Mock, MagicMock, patch
from lafia.lafiaio.doctype.familyhistory.familyhistory import FamilyHistory


def mocked_requests_get(*args, **kwargs):
	print(args[0])
	class MockResponse:
		def __init__(self, json_data, status_code):
			self.json_data = json_data
			self.status_code = status_code

		def json(self):
			return self.json_data

	if args[0] == 'https://api.lafia.io/fhir/FamilyHistory/620':
			return MockResponse({"key1": "value1"}, 200)
	

	return MockResponse(None, 404)


class TestFamilyHistory(unittest.TestCase):

	data_model = {
	"identifier": "",
	"instantiates_canonical": "",
	"instantiates_uri": "",
	"status": "",
	"absent_reason": "",
	"patient": "",
	"date": "",
	"member_name": "",
	"relationship": "",
	"sex": "",
	"born_section": "",
	"born_period": "",
	"born_date": "",
	"born_string": "",
	"age_section": "",
	"age": "",
	"age_range": "",
	"age_string": "",
	"estimated_age": "",
	"deceased_section": "",
	"deceased_boolean": "",
	"deceased_age": "",
	"deceased_range": "",
	"deceased_date": "",
	"deceased_string": "",
	"reason_code": "",
	"reason_reference_type": "",
	"reason_reference": "",
	"note": "",
	"condition": "",
	"fhir_serverid": ""
	}

	def test_get_body(self):
		familyhistory = FamilyHistory
		result = self.data_model
		self.assertEqual(familyhistory.get_body(self.data_model).get("status"), result.get("status"))

	@patch('requests.put', side_effect=mocked_requests_get)
	def test_before_save(self, mocked_requests_get):
		familyhistory = FamilyHistory
		class result:
			status = "partial"
			name = "FMH-LIO-620"
			fhir_serverid = 620
			get_body = MagicMock(return_value=self.data_model)
		familyhistory.before_save(result)
		result.get_body()
		result.get_body.assert_called_once()

	def test_get_condition(self):
		familyhistory = FamilyHistory
		copy_self = self.data_model.copy()
		copy_self["get_code"] = MagicMock(return_value={
			"code": "",
			"system": "",
			"display": ""
		})
		condition_dict = {
			"code": "",
			"outcome": "",
			"contributedToDeath": "",
			"onsetAge": "",
			"onsetRange": "",
			"onsetPeriod": "",
			"onsetString": ""
		}
		condition_result = {
			"code": [{
				"coding": []
			}],
			"outcome": [{
				"coding": []
			}],
			"contributedToDeath": "",
			"onsetAge": "",
			"onsetRange": "",
			"onsetPeriod": "",
			"onsetString": ""
		}
		self.assertEqual(familyhistory.get_condition(copy_self, condition_dict), condition_result)

if __name__ == '__main__':
    unittest.main()
