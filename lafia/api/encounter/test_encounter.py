import frappe
import unittest
from lafia.api.encounter import encounter
from unittest.mock import Mock, MagicMock, patch

example_start_datetime = "2015-01-17T16:00:00+10:00"
example_end_datetime = "2015-01-17T16:30:00+10:00"

mock_data = {
  "resourceType": "Encounter",
  "id": "home",
  "status": "finished",
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "HH",
    "display": "home health"
  },
  "subject": {
    "reference": "Patient/example"
  },
  "participant": [
    {
      "period": {
        "start": example_start_datetime,
        "end": example_end_datetime
      },
      "individual": {
        "reference": "Practitioner/example",
        "display": "Dr Adam Careful"
      }
    }
  ],
  "period": {
    "start": example_start_datetime,
    "end": example_end_datetime
  },
  "location": [
    {
      "location": {
        "reference": "#home",
        "display": "Client's home"
      },
      "status": "completed",
      "period": {
        "start": example_start_datetime,
        "end": example_end_datetime
      }
    }
  ]
}

class MockGetDoc:
    status = "Scheduled",
    name = "ENC-LIO-223",
    fhir_serverid = "223",
    def save(self):
        data = {
            "status": self.status,
            "name": self.name,
            "fhir_serverid": self.fhir_serverid
        }
        return data
class TestPatientEncounter(unittest.TestCase):

	@patch('frappe.get_doc', side_effect=MagicMock(return_value=MockGetDoc()))
	def test_create(self, mock_get_doc):
            encounter.fhir_serverid = "test"
            called_response = encounter.create_encounter(mock_data)
            self.assertEqual(called_response.status[0], "Scheduled")

if __name__ == '__main__':
    unittest.main()