# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ProcedureTool(Document):
	def before_insert(self):
		self.patient = frappe.db.get_value("Patient", {"uid":self.patient_id}, 'name')
		self.encounter = frappe.db.get_value("Patient Encounter",{"uid":self.encounter_id}, 'name')
		self.practitioner = frappe.db.get_value("Patient Encounter",{"name":self.encounter}, 'practitioner')

	def after_insert(self):
		start_date = (self.get('start').replace("T", " ").replace("Z", "")).split(" ")
		condition_data = {
			"doctype": "Clinical Procedure",
			"start_date": start_date[0],
			"start_time": start_date[1],
			"end_date": self.get('stop').replace("T", " ").replace("Z", ""),
			"patient": self.patient,
			"encounter": self.encounter,
			"practitioner": self.practitioner,
			'code': self.code,
			'category': self.category,
			'statusreason': self.reason_code,
			'procedure_template': self.procedure_template,
			'docstatus': 1,
			'status': "Completed",
			'status1': "completed"
		}
		condition_doc = frappe.get_doc(condition_data)
		condition_doc.save()
