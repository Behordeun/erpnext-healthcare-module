# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals
from .healthcare_service import HealthcareService

import unittest

class TestHealthcareService(unittest.TestCase):
    def test_before_insert(self):
        class Info:
            email = "@mail.com"
            name1 = "Test HealthcareService"
            id = "123456789"
            phone = "123456789"

            def __init__(self):
                self.fhir_serverid = "123456789"
                self.identifier = ""
            
            def get(self, attr):
                    return getattr(self, attr)
		
        info = Info()
        HealthcareService.before_insert(info)
        self.assertEqual(info.fhir_serverid, "123456789")

    def test_after_save(self):
        class Info:
            email = "@mail.com"
            name1 = "Test HealthcareService"
            id = "123456789"
            phone = "123456789"

            def __init__(self):
                self.fhir_serverid = "123456789"
                self.identifier = ""
            
            def save(self):
                    data = {
                            "name": self.name,
                            "fhir_serverid": self.fhir_serverid
                    }
                    return data
            
            def get(self, attr):
                    return getattr(self, attr)
        
        info = Info()
        HealthcareService.after_insert(info)
        self.assertEqual(info.fhir_serverid, "123456789")

    def setUp(self):
        self.data = {
            "availabletime":[{
                'weeks': 'tue',
                'days': 0,
                'openingtime': '08:00:00',
                'closingtime': ''
            }],
            "notavailable": [
                {
                    'description': 'Test 1',
                    'start': '04-10-2022 03:22:38',
                    'end': '10-10-2022 03:22:38'
                },
                {
                    'description': 'Test 2',
                    'start': '04-11-2022 03:22:38',
                    'end': '10-11-2022 03:22:38'
                }
            ]

        }
		
    def test_hours_of_operation(self):        
        result = [{
            'daysOfWeek': ['tue'],
            'allDay': False,
            'openingTime': '8:0:0',
            'closingTime': ''
        }]
        a = HealthcareService.hours_of_operation(self.data)
        self.assertEqual(a,result)
    
    def test_unavailability(self):
        result = [
            {
                'description': 'Test 1',
                'during': {
                    'start': '04-10-2022T03:22:38Z',
                    'end': '10-10-2022T03:22:38Z'
                }
            },
            {
                'description': 'Test 2',
                'during': {
                    'start': '04-11-2022T03:22:38Z',
                    'end': '10-11-2022T03:22:38Z'
                }
            }
        ]
        a = HealthcareService.unavailability(self.data)
        self.assertEqual(a,result)
    
	


