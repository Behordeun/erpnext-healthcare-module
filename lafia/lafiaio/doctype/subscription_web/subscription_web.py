# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date
# from erpnext.accounts.doctype.subscription.subscription import get_subscription_updates


class SubscriptionWeb(Document):
	def after_insert(self):
		practitioner = frappe.get_doc("Healthcare Practitioner",self.practitioner)
		if practitioner.account_type == "Private Practitioner":
			if self.customer:
				subscription = {
					'doctype': 'Subscription',
					'party_type': 'Customer',
					'party': self.customer,
					'start_date': self.start_date,
					'end_date': add_to_date(self.start_date,months=1),
					'generate_invoice_at_period_start': 1,
					'cancel_at_period_end': 1,
					'plans': [{
						'plan': "Physician Plan",
						'qty': 1
					}]
				}
				print(subscription)
				subscription_doc = frappe.get_doc(subscription)
				subscription_doc.insert(ignore_permissions=True, ignore_mandatory=True)
				frappe.db.commit()
				# get_subscription_updates(subscription_doc.get('name'))
