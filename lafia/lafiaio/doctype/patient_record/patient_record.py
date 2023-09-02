# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

import frappe,os
from frappe.model.document import Document
from frappe.share import add
from lafia.utils.fhir_utils import random_string
from dotenv import load_dotenv
load_dotenv()

lafia_app_url = os.environ.get("BASE_URL")


class PatientRecord(Document):	
	
	def after_insert(self):
		self.create_user()
		# add("Patient",self.patient,self.email)
		self.share_documents()

	def create_user(self):
		# password = random_string(15)
		password = "Lafia10#"
		user = frappe.get_doc({
			"doctype": "User",
			"email": self.email,
			"first_name": self.hospital_name,
			"new_password": password,
			# "last_name": self.last_name,
			"module_profile": "Record User",
			"enabled": 1,
			"send_welcome_email": 0
		}).insert(ignore_permissions=True, ignore_mandatory=True)
		user.add_roles("Record User")
		user.save()
		self.send_access_email(password,'hospital_access')
		frappe.db.commit()

	def share_documents(self):
		for doc in self.documents:
			data = frappe.get_all(doc.document,filters={'patient':self.patient},pluck='name')
			if data:
				for name in data:
					add(doc.document,name,self.email)

	
	def send_access_email(self,password,template):
		args = {
			"name": self.hospital_name,
			"patient": self.patient,
			"password": password,
			"user": self.email,
			"expiry": self.expiry,
			"site_url": f"{lafia_app_url}/login",
			"created_by": "Administrator"
		}
		print(args)
		sender = frappe.session.user
		print(sender)
		subject="Document Access"
		frappe.sendmail(
			recipients=[self.email],
			subject=subject,
			template=template,
			args=args,
			header=[subject, "green"],
		)
		print("email sent")

