# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
import sys
import requests
import json
import os, frappe
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_telecom,get_addresses,get_code,get_reference,get_reference_list,format_datetime,period
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Group(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Group",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"active": True if self.active == 1 else False,
			"type": (self.type).lower(),
			"membership": self.membership,
			"name": self.name1,
			"description": self.description,
			"quantity": self.quantity,
			"code": {"coding": [get_code("Group Kind", self.get("code"))] if self.get("code") else [] },
			"managingEntity": get_reference(self.entity_type,self.entity) if self.entity else "",
			"characteristic": [{"code":{"text":self.characteristic}}],
			"member": self.get_members() if self.members else []
		}
		print(fhir_schema)
		return fhir_schema


	def get_members(self):
		member_list = []
		for member in self.get('members'):
			member_list.append({
				"entity": get_reference(member.get('entity_type'),member.get('entity')),
				"inactive": True if member.get('active') == 0 else False,
				"period": period(member.get('start_date'),member.get('end_date')) if member.get('start_date') and member.get('end_date') else "",
			})
		return member_list

	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/Group',
				json=fhir_schema, verify=False)
		
			group_object = response.json()
			frappe.errprint(group_object)
		
			if group_object.get("status") == 201:
				self.fhir_serverid = group_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/Group/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		group_object = response.json()
		print(group_object)

	def after_insert(self):
		event_body = {
			"resource_type": "Group",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.name1,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/fhir/Group/' + self.fhir_serverid, verify=False)		
		print(response.json())



