# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest, os

from dotenv import load_dotenv
from unittest.mock import Mock, MagicMock, patch
from lafia.lafiaio.doctype.careteam.careteam import CareTeam

load_dotenv()

def mocked_requests_get(*args, **kwargs):
	print(args[0])
	class MockResponse:
			def __init__(self, json_data, status_code):
					self.json_data = json_data
					self.status_code = status_code

			def json(self):
					return self.json_data

	if args[0] == '{0}/fhir/CareTeam/474'.format(os.environ.get('LAFIA_SERVER_URL')):
			return MockResponse({"key1": "value1"}, 200)
	print("Errororrrorro")

	return MockResponse(None, 404)
class TestCareTeam(unittest.TestCase):

	data_model = {
	"identifier": "",
  "status": "",
  "category": "",
  "name1": "",
  "subject_type": "",
  "subject": "",
  "column_break_8": "",
  "encounter": "",
  "managingorganization": "",
  "reasoncode": "",
  "reason_reference": "",
  "period": "",
  "note": "",
  "telecom": "",
  "participant": "",
  "fhir_serverid": ""
	}

	def test_get_body(self):
		careteam = CareTeam
		result = self.data_model
		self.assertEqual(careteam.get_body(self.data_model).get("status"), result.get("status"))

	@patch('requests.put', side_effect=mocked_requests_get)
	def test_before_save(self, mock_put):
		print("Ground0")
		print(self.data_model)
		careteam = CareTeam
		class result:
			status = "in-progress"
			name = "CTM-LIO-474"
			fhir_serverid = 474
			get_body = MagicMock(return_value=self.data_model)
		careteam.before_save(result)
		result.get_body.assert_called_once()

	def test_get_participant(self):
		careteam = CareTeam
		copy_self = self.data_model.copy()
		copy_self["get_code"] = MagicMock(return_value={
			"code": "",
			"system": "",
			"display": ""
		})
		participant_dict = {
			"role": "",
			"onbehalfof": "",
			"member_type": "",
			"member": "",
		}
		participant_result = {
			"role": [{
				"coding": []
			}],
			"member":  "",
			"onBehalfOf": "",
			"period": ""
		}
		self.assertEqual(careteam.get_participant(copy_self, participant_dict), participant_result)

if __name__ == '__main__':
    unittest.main()
