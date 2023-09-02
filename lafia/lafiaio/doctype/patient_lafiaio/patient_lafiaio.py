# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from lafia.api.patient.patient import get_fullname, get_telecom, get_addresses, get_patient_contact
from lafia.utils.fhir_utils import get_identifier

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Patient_LafiaIO(Document):

	def on_update(self):
		print("===Before Save===")
		print(self)
		print("===Before Save===")

		fhir_schema = {
				"resourceType": "Patient",
				"id": self.fhir_serverid,
				"identifier": get_identifier(self.identifier),
				"active": True,
				"name": get_fullname(self.firstname, self.lastname, self.other_name),
				"telecom": get_telecom(self.get("email"), self.get("phone")),
				"gender": self.gender,
				"birthDate": self.birthdate.replace(" ", "T") if self.birthdate else "",
				"deceasedBoolean": False if self.deceased_boolean == 0 else 1,
				"deceasedDatetime": self.deceased_datetime if self.deceased_datetime else '',
				"address": get_addresses(self.get("address")),
				"contact": get_patient_contact(self.contact)
		}
		print(self.fhir_serverid)
		response = requests.put(
				'{0}/fhir/Patient/{1}'.format(lafia_base_url, self.fhir_serverid), json=fhir_schema)
		if not response.status_code == 200:
			print(response.__dict__)
			frappe.throw("An error occured")
	
