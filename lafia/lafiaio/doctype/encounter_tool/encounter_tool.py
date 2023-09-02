# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EncounterTool(Document):
	def before_insert(self):
		self.patient = frappe.db.get_value("Patient", {"uid":self.p_uid}, 'name')
		self.provider = frappe.db.get_value("Healthcare Practitioner",{"uid":self.prov_id}, 'name')
		self.organization = frappe.db.get_value("Organization",{"uid":self.org_id}, 'name')

	
	def after_insert(self):
		start_date = (self.get('start').replace("T", " ").replace("Z", "")).split(" ")
		encounter_doc_data = {
			"doctype": "Patient Encounter",
			"uid": self.uid,
			"class": self.get("class"),
			"patient": self.patient,
			"practitioner": self.provider,
			"service_provider": self.organization,
			"encounter_date": start_date[0],
			"encounter_time": start_date[1],
			"encounter_end_date": self.get('stop').replace("T", " ").replace("Z", ""),
			"reason_code": self.reason_code,
			"docstatus": 1
		}
		encounter_doc = frappe.get_doc(encounter_doc_data)
		encounter_doc.save()
		print("encounter_doc")
		print(encounter_doc)
