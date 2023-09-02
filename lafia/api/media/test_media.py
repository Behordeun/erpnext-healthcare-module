import frappe
import unittest
from lafia.api.media import media
from unittest.mock import Mock, MagicMock, patch

example_start_datetime = "2015-01-17T16:00:00+10:00"
example_end_datetime = "2015-01-17T16:30:00+10:00"

mock_data = {
  "resourceType": "Media",
  "id": "1.2.840.11361907579238403408700.3.1.04.19970327150033",
  "status": "completed",
  "modality": {
    "coding": [
      {
        "system": "http://dicom.nema.org/resources/ontology/DCM",
        "code": "US"
      }
    ]
  },
  "view": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "399067008",
        "display": "Lateral projection"
      }
    ]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "device": {
    "display": "G.E. Medical Systems"
  },
  "height": 480,
  "width": 640,
  "content": {
    "contentType": "application/dicom",
    "url": "http://imaging.acme.com/wado/server?requestType=WADO&contentType=application%2Fdicom&studyUid=1.2.840.113619.2.21.848.34082.0.538976288.3&seriesUid=1.2.840.113619.2.21.3408.700.0.757923840.3.0&objectUid=1.2.840.11361907579238403408700.3.1.04.19970327150033"
  }
}

class MockGetDoc:
    fhir_serverid = "223",
    def insert(self):
        data = {
            "fhir_serverid": self.fhir_serverid
        }
        return data
class TestMedia(unittest.TestCase):

	@patch('frappe.get_doc', side_effect=MagicMock(return_value=MockGetDoc()))
	def test_create(self, mock_get_doc):
            media.fhir_serverid = "test"
            called_response = media.create_media(mock_data)
            self.assertEqual(called_response.fhir_serverid[0], "223")

if __name__ == '__main__':
    unittest.main()