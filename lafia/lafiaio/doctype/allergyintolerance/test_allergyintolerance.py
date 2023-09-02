# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and Contributors
# See license.txt
from __future__ import unicode_literals


import frappe
from frappe.model.document import Document
import unittest
from unittest.mock import Mock, MagicMock, patch
from lafia.lafiaio.doctype.allergyintolerance.allergyintolerance import AllergyIntolerance


class TestAllergyIntolerance(unittest.TestCase):
	def setUp(self):
		self.data = [{
			"reactions": ''
		}]

	def test_get_reactions(self):
		result = [{}]
