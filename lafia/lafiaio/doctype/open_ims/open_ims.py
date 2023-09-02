# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

import frappe,requests,os
from frappe.model.document import Document
from frappe import get_meta



class OpenIMS(Document):
	def after_insert(self):
		company = frappe.db.get_value("Employee",{'user_id':frappe.session.user},'company')
		fhir_id = frappe.get_doc("Company",company).fhir_serverid
		
		url = "https://143.198.111.7:5000/erp"

		data = {
			"orgId": fhir_id,
			"resources": [resource.resource for resource in self.resources]
		}
		print(data)
		response = requests.post(url, json=data, verify=False)

		print(response)
