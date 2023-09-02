import sys
import os, frappe
from frappe import whitelist
from dotenv import load_dotenv

@whitelist(allow_guest=True)
def create_patient_video(video_data):
  patient = frappe.db.get_value("Patient",{"fhir_serverid":video_data["patientId"]},"name")
  # company = frappe.db.get_value("Patient",{'name': patient},'organization')
  patient_video_data = {
    "doctype": "Patient Video",
    "patient": patient,
    "video_url": video_data["videoUrl"],
    "duration": video_data["videoTime"],
    # "video_thumbnail": video_data["video_thumbnail"],
    "name": video_data["videoUrl"].split("/")[-1],
    # "company": company if company else frappe.defaults.get_user_default('company')
  }
  patient_video_doc = frappe.get_doc(patient_video_data)
  patient_video_doc.insert()
  return patient_video_doc.name
