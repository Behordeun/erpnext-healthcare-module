# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt
# import frappe

import frappe,requests,os
from frappe.model.document import Document

class TransmitRecords(Document):
	def on_submit(self):
		data = {
			"sourceUrl": self.source_url,
			"destinationUrl": self.destination_url,
			"resources": [resource.resource for resource in self.resources]
		}
		url = "https://143.198.111.7:5000/fhir-to-fhir"
		print(data)
		response = requests.post(url, json=data, verify=False)

		print(response)
