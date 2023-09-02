import sys
import requests
import json
import os, frappe
from frappe import whitelist
from dotenv import load_dotenv
from lafia.api.services.brokers.producer import producer
from lafia.api.practitioner.practitioner import get_identifier
from lafia.utils.fhir_utils import get_fhir_doc

@whitelist(allow_guest=True)
def create_media(media_data):
  split_subject = media_data.get("subject").get("reference").split("/")
  split_encounter = media_data.get("encounter").get("reference").split("/") if media_data.get("encounter") else []
  split_operator = media_data.get("operator").get("reference").split("/") if media_data.get("operator") else []
  media_doc_data = {
    "doctype": "Media",
    "status": media_data.get("status").capitalize() if media_data.get("status") else "Completed",
    "type": media_data.get("type").get("coding")[0].get("display") if media_data.get("type") else "",
    # "subject_doctype": "Patient" if split_subject[0] == "Patient" else split_subject[0],
    "patient": get_fhir_doc("Patient", split_subject[1]),
    "encounter": get_fhir_doc("Patient Encounter",split_encounter[1]) if len(split_encounter) > 1 else None,
    "created": media_data.get("createdDateTime").replace("T", " ").replace("Z", "") if media_data.get("createdDateTime") else None,
    "practitioner": get_fhir_doc("Healthcare Practitioner",split_operator[1]),
    "duration": media_data.get("duration") if media_data.get("duration") else 0,
    "video": """    
    <video width="320" height="240" controls>
			<source src=${video_url} type="video/mp4">
					Your browser does not support the video tag.
		</video>
    """.format(video_url=media_data.get("content").get("url")),
    "content": [{
      "content_type": media_data.get("content").get("contentType") if media_data.get("content").get("contentType") else "",
      "url": media_data.get("content").get("url") if media_data.get("content").get("url") else "",
      "size": media_data.get("content").get("size") if media_data.get("content").get("size") else "",
      "title": media_data.get("content").get("title") if media_data.get("content").get("title") else "",
    }],
    "fhir_serverid": media_data.get("id")
  }
  media_doc = frappe.get_doc(media_doc_data)
  media_doc.insert()
  frappe.db.commit()
  return media_doc
