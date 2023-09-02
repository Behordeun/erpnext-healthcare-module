# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

import frappe,os,json
from frappe.model.document import Document
from lafia.api.services.brokers.producer import producer
from dotenv import load_dotenv
load_dotenv()

lafia_app_url = os.environ.get("BASE_URL")
producer_queue = os.environ.get("OCR_PUB")

class Records(Document):
	def on_submit(self):
		attachments = frappe.get_all('File', fields=["*"],
			       filters={'attached_to_doctype': self.doctype,
		   					'attached_to_name': self.name})
		if attachments:
			url_list =[]
			for attachment in attachments:
				file = attachment.get('file_url')
				url_list.append(f'{lafia_app_url}/{file}')
			
			event_body = {
				"unique_id": self.name,
				"image_url": url_list
			}
			print(event_body)
			producer(producer_queue, json.dumps(event_body))


