# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ClaimTool(Document):
	def before_insert(self):
		self.patient = frappe.db.get_value("Patient", {"uid":self.p_uid}, 'name')
		self.organization = frappe.db.get_value("Organization",{"uid":self.org_id}, 'name')


	def after_insert(self):
		claim_data = {
			"doctype": "Claims",
			"uid": self.uid,
			"patient": self.patient,
			"code": "Active",
			"use": "Claim",
			"type": "Institutional",
			"sub_type": "Orthodontic Claim",
			"created": self.get('bill_start').replace("T", " ").replace("Z", ""),
			"billable_start": self.get('bill_start').replace("T", " ").replace("Z", ""),
			"billable_end": self.get('bill_stop').replace("T", " ").replace("Z", ""),
			"provider": self.organization,
			"priority": "Normal",
			"diagnosis": self.diagnosis
		}
		claim_doc = frappe.get_doc(claim_data)
		claim_doc.save()