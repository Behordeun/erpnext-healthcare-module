import frappe
from frappe.permissions import add_permission,update_permission_property
from frappe.utils import get_datetime, add_to_date


def add_perms():
    update_permission_property("Practitioner Schedule","Physician",0,'if_owner',1)
    add_permission("Sales Invoice",'Guest',0,ptype='create')
    frappe.errprint("Added")


def hide_modules():
   workspace = frappe.db.sql(""" Select name from `tabWorkspace` where name != 'Healthcare'""",as_dict=1)
   for space in workspace:
      doc = frappe.get_doc("Workspace",space.get('name'))
      doc.db_set('public',0,commit=True)


def delete_record_access():
   data = frappe.get_all("Patient Record",fields=["*"])
   for doc in data:
      last_login = frappe.db.get_value("User", {'name':doc.email},'last_login')
      if last_login:
        expiry = add_to_date(last_login, minutes=doc.get('expiry'))
        print(expiry)
        if get_datetime() > get_datetime(expiry):
            frappe.delete_doc("User",doc.email,force=1)
            print('user deleted')