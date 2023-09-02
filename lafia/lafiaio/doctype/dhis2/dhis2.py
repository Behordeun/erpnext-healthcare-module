# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

import frappe,requests
from frappe.model.document import Document

class DHIS2(Document):
	def before_insert(self):
		if self.patient and self.organization:
			frappe.throw("You can only request for one resource per time")
	
	def after_insert(self):
		url = 'https://143.198.111.7:5000/dhis2-to-fhir'
		
		if self.patient:
			data = {
				"trackedEntityInstances": True,
				"organisationUnits": True
			}
			print(data)
			response = requests.post(url, json=data)
			print(response.status_code)
		
		if self.organization:
			data = {
				"trackedEntityInstances": False,
				"organisationUnits": True
			}
			print(data)
			response = requests.post(url, json=data, verify=False)
			print(response.status_code)

		
		frappe.msgprint("Request sent successfully")
