# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

# import frappe

import frappe,requests,os
from frappe.model.document import Document

class SyncEHRBase(Document):
	def on_submit(self):
		data = {
   		"q": 'select e/ehr_id/value as ehrId, c from EHR e contains COMPOSITION c[openEHR-EHR-COMPOSITION.final_demographics.v0]',
			"resources": [resource.resource for resource in self.resources]
		}
		url = "http://openhim-core.lafia.io:5001/v1"
		print(data)
		response = requests.post(url, json=data, verify=False)

		print(response)
