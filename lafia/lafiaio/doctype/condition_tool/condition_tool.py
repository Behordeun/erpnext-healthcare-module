# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ConditionTool(Document):	
	def before_insert(self):
		self.patient = frappe.db.get_value("Patient", {"uid":self.patient_id}, 'name')
		self.encounter = frappe.db.get_value("Patient Encounter",{"uid":self.encounter_id}, 'name')

	def after_insert(self):
		condition_data = {
			"doctype": "Condition",
			"start": self.start,
			"stop": self.stop,
			"recorded_date": self.start,
			"subject": self.patient,
			"encounter": self.encounter,
			'code': self.code,
			'category': "Encounter-diagnosis",
			'severity': "Moderate",
			'body_site': self.body_site,
			"verification_status": "Confirmed",
			"clinical_status": "Resolved"
		}
		condition_doc = frappe.get_doc(condition_data)
		condition_doc.save()
		

