# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os, json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_reference,format_datetime
from lafia.api.services.brokers.producer import producer
from dotenv import load_dotenv

load_dotenv()
lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class AllergyIntolerance(Document):

	def fhir_object(self):
		fhir_schema = {
			"resourceType": "AllergyIntolerance",
			"identifier": get_identifier(self.identifier),
			"clinicalStatus": {"text": self.status} if self.status else "",
			"verificationStatus":  {"text": self.verificationstatus} if self.verificationstatus else "",
			"type": {"text": self.type} if self.type else "",
			"category": [(self.category).lower()],
			"criticality": (self.criticality).lower(),
			"recordedDate": format_datetime(self.recordeddate),
			"lastOccurrence": format_datetime(self.lastoccurrence),
			"patient": get_reference("Patient", self.patient),
			"encounter": get_reference("Patient Encounter", self.encounter) if self.encounter else '',
			"code": {"coding": [get_code("Allergy Code", self.get("code"))]} if  self.code else "",
			"participant": get_participant(self.get("participants")) if self.get("participants") else "",
			"note": [{'text': self.note}],
			"reaction": self.get_reactions()
		}
		print(fhir_schema)
		return fhir_schema

	def get_reactions(self):
		reaction_list = []
		for reaction in self.get('reactions'):
			reaction_list.append({
				"substance": {"coding": [get_code("Substance Code",
					reaction.get('substance'))]} if reaction.get('substance') else "",
				"manifestation": [get_reference("Observation",reaction.get('manifestation'))],
				"description": reaction.get('description'),
				"onset": format_datetime(reaction.get("onset")) if reaction.get("onset") else '',
				"severity": (reaction.get("severity")).lower(),
				"exposureRoute": {"coding": [get_code("Exposure Route",
					reaction.get('exposureroute'))]} if reaction.get('exposureroute') else ""
			})
		return reaction_list

	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
					lafia_base_url + '/fhir/AllergyIntolerance',
					json=fhir_schema, verify=False)
			
			allergy_object = response.json()
			frappe.errprint(allergy_object)
		
			if allergy_object.get("status") == 201:
				self.fhir_serverid = allergy_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")

	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/AllergyIntolerance/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		allergy_object = response.json()
		print(allergy_object)

	
	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/fhir/AllergyIntolerance/' + self.fhir_serverid, verify=False)		
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type" : "allergy",
			"resource_id": self.fhir_serverid,
			"data" : {
				"name": self.patient
			}

		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


def get_participant(participants):
	participant_list = []
	for part in participants:
		participant_list.append({
			"actor": get_reference(part.get("participant_role"),part.get("participant")),
			"function": {
				"coding": [get_code("Participant Type", part.get("function"))]
				} if part.get("function") else ""
		})
	return participant_list