# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from .group import Group

class TestGroup(unittest.TestCase):
	def setUp(self):
		# frappe.db.sql("""delete from `tabGroup`""")
		frappe.db.sql("""delete from `tabPatient` where first_name = '_Test Patient 1'""")

		
		self.patient, self.practitioner = create_healthcare_docs(id=1)
		self.data = {
			"members" : [
				{
					"entity_type": "Healthcare Practitioner",
					"entity": self.practitioner,
					"active": 0
				},
				{
					"entity_type": "Patient",
					"entity": self.patient,
					"active": 1,
					"start_date": "10-11-2022",
					"end_date": "11-12-2022"
				}
			]
		}
	
	def test_get_members(self):
		pat_id = frappe.get_doc("Patient",self.patient).fhir_serverid
		prac_id = frappe.get_doc("Healthcare Practitioner",self.practitioner).fhir_serverid
		result = [
			{
				'entity': {'reference':f'Practitioner/{prac_id}'},
				'inactive': True,
				"period": ""
			},
			{
				'entity': {'reference':f'Patient/{pat_id}'},
				'inactive': False,
				"period": {"start":"2022-10-11","end":"2022-11-12"}
			}
		]
		a = Group.get_members(self.data)
		self.assertEqual(a,result)



def create_healthcare_docs(id=0):
	patient = create_patient(id, email='_testpat5@mail.com')
	practitioner = create_practitioner(id, email='_testprat5@mail.com')

	return patient, practitioner


def create_patient(id=0, patient_name=None, email=None, mobile=None, customer=None, create_user=True):
	if frappe.db.exists('Patient', {'first_name':f'_Test Patient {str(id)}'}):
		patient = frappe.db.get_value('Patient', {'first_name': f'_Test Patient {str(id)}'}, ['name'])
		return patient

	patient = frappe.new_doc('Patient')
	patient.first_name = patient_name if patient_name else f'_Test Patient {str(id)}'
	patient.sex = 'Female'
	patient.mobile = mobile
	patient.email = email
	patient.customer = customer
	patient.invite_user = create_user
	patient.save(ignore_permissions=True)

	return patient.name


def create_practitioner(id=0, email=None, medical_department=None):
	if frappe.db.exists('Healthcare Practitioner', {'first_name':f'_Test Healthcare Practitioner {str(id)}','email':email}):
		practitioner = frappe.db.get_value('Healthcare Practitioner', {'first_name':f'_Test Healthcare Practitioner {str(id)}'}, ['name'])
		return practitioner

	practitioner = frappe.new_doc('Healthcare Practitioner')
	practitioner.first_name = f'_Test Healthcare Practitioner {str(id)}'
	practitioner.gender = 'Female'
	practitioner.department = medical_department
	practitioner.email = email
	practitioner.save(ignore_permissions=True)

	return practitioner.name
