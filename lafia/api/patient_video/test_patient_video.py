import frappe
import unittest
from lafia.api.patient_video import patient_video
from unittest.mock import Mock, MagicMock, patch


mock_data = {
  "patient": "PAT-LIO-223",
  "video_url": "http://imaging.acme.com/wado/videoid1256782",
  "video_thumbnail": "http://imaging.acme.com/wado/videoid1256782"
}

def mocked_get_doc(*args, **kwargs):
	class MockGetDoc:
			name = ""

			def __init__(self, data):
					self.name = data.get("name")
					self.doctype = data.get("doctype")
			
			def insert(self):
					data = {
							"name": self.name
					}
					return data
			def get(self, attr):
					return getattr(self, attr)
	return MockGetDoc(args[0])
class TestMedia(unittest.TestCase):

	@patch('frappe.get_doc', side_effect=mocked_get_doc)
	def test_create(self, mock_get_doc):
            called_response = patient_video.create_patient_video(mock_data)
            self.assertEqual(called_response, "videoid1256782")

if __name__ == '__main__':
    unittest.main()