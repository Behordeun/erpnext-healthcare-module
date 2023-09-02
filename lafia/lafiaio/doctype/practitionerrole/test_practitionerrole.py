# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals
from .practitionerrole import PractitionerRole

import unittest

class TestPractitionerRole(unittest.TestCase):
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
        a = PractitionerRole.hours_of_operation(self.data)
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
        a = PractitionerRole.unavailability(self.data)
        self.assertEqual(a,result)
        

