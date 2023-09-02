# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import unittest, os
from dotenv import load_dotenv
from unittest.mock import Mock, MagicMock, patch
from lafia.lafiaio.doctype.encounter.encounter import Encounter

load_dotenv()
mock_data = {
	"status": "Scheduled",
	# "get_body": MagicMock(return_value={})
}

def mocked_requests_get(*args, **kwargs):
	print(args[0])
	class MockResponse:
			def __init__(self, json_data, status_code):
					self.json_data = json_data
					self.status_code = status_code

			def json(self):
					return self.json_data

	if args[0] == '{0}/fhir/Encounter/223'.format(os.environ.get('LAFIA_SERVER_URL')):
			return MockResponse({"key1": "value1"}, 200)

	return MockResponse(None, 404)

class TestEncounter(unittest.TestCase):

	def test_get_body(self):
		encounter = Encounter
		result = mock_data
		self.assertEqual(encounter.get_body(mock_data).get("status"), result.get("status"))

	@patch('requests.put', side_effect=mocked_requests_get)
	def test_before_save(self, mock_put):
		encounter = Encounter
		result = {
			"status": "Scheduled",
			"name": "ENC-LIO-223",
			"fhir_serverid": "223",
			"get_body": MagicMock(return_value=mock_data)
		}
		encounter.fhir_serverid = "test"
		encounter.before_save(result)
		result.get("get_body").assert_called_once()

if __name__ == '__main__':
    unittest.main()
