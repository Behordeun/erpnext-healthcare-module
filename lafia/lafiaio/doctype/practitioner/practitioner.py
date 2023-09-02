# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from lafia.api.patient.patient import get_addresses, get_patient_contact
from lafia.api.practitioner.practitioner import get_qualifications, get_practitioner_communication
from lafia.utils.fhir_utils import get_identifier, get_period, get_fullname, get_telecom

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Practitioner(Document):

	def on_update(self):
	
		fhir_schema = {
				"resourceType": "Practitioner",
				"id": self.get("fhir_serverid"),
				"identifier": get_identifier(self.identifier),
				"active": False if self.active == 0 else True,
				"name": get_fullname(self.firstname, self.lastname, self.other_name),
				"telecom": get_telecom(self.get("email"), self.get("phone")),
				"gender": self.gender,
				"birthDate": self.birthdate.replace(" ", "T") if self.birthdate else "",
				"address": get_addresses(self.get("address")),
				"qualification": get_qualifications(self.get("qualification")),
				"communication": get_practitioner_communication(self.get("communication"))
		}
		print(self.fhir_serverid)
		response = requests.put(
				'{0}/fhir/Practitioner/{1}'.format(lafia_base_url, self.fhir_serverid), json=fhir_schema)
		if not response.status_code == 200:
			print(response.__dict__)
			frappe.throw("An error occured")
