# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

import frappe,os
from frappe.model.document import Document
from frappe.utils import today
from dotenv import load_dotenv
load_dotenv()

lafia_app_url = os.environ.get("BASE_URL")

class OrganizationOnboarding(Document):
	def on_submit(self):
		self.create_company()
		if self.admin_email:
			self.create_admin_account()
			self.create_employee()
			self.reload()


	def after_insert(self):
		args = {
			"site_url": f"{lafia_app_url}/app/organization-onboarding/{self.name}",
			"hospital": self.hospital_name
		}
		
		frappe.sendmail(
			recipients=['hello@lafia.io','sales@lafia.io'],
			subject='New Hospital',
			template='organization_onboarding',
			args=args
		)

	def create_company(self):
		company_doc = frappe.get_doc({
			"doctype": 'Company',
			"company_name": self.hospital_name,
			"default_currency": self.currency if self.currency else 'USD',
			"country": self.country
		}).insert(ignore_permissions=True, ignore_mandatory=True)
		company_doc.save()
		frappe.db.commit()

	def create_admin_account(self):
		user = frappe.get_doc({
			"doctype": "User",
			"email": self.admin_email,
			"first_name": self.first_name,
			"last_name": self.last_name,
			"enabled": 1,
			"module_profile": "Healthcare Admin",
			"role_profile_name": "Healthcare Admin",
			"send_welcome_email": 1
		}).insert(ignore_permissions=True, ignore_mandatory=True)
		user.save()
		frappe.db.commit()

	def create_employee(self):
		employee_data = frappe.get_doc({
			"doctype": "Employee",
			"first_name": self.first_name,
			"last_name": self.last_name,
			"company": self.hospital_name,
			"gender": self.gender,
			"date_of_birth": self.date_of_birth,
			"date_of_joining": today(),
			"user_id": self.admin_email
			}).insert(ignore_permissions=True, ignore_mandatory=True)
		employee_data.save()
		frappe.db.commit()
		
	