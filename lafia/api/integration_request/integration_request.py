import frappe,json
from frappe.utils import today


def payment_entry(doc, method):
    data = json.loads(doc.data)
    customer = ""
    """Subscription for New Practitioner"""
    if doc.status == "Completed" and ("Healthcare Practitioner" in data.get('description')) :
        customer += frappe.get_doc("Healthcare Practitioner", data.get('order_id')).customer_account

    """Subscription Renewal"""
    if doc.status == "Completed" and ("Subscription" in data.get('description')):
        customer += frappe.get_doc("Subscription Web", data.get('order_id')).customer
        
    if customer:
        # create_payment_entry(invoice,data)
        invoice = frappe.get_all("Sales Invoice",filters={'customer':customer},fields=['name'])[0]
        frappe.db.set_value("Sales Invoice",invoice.name,'status','Paid')
        frappe.db.commit()
    


def create_payment_entry(invoice,data):
    sales_invoice = frappe.get_doc("Sales Invoice",invoice)
    entry = {
        'doctype': 'Payment Entry',
        'posting_date': today(),
        'payment_type': 'Receive',
        'company': sales_invoice.company,
        'party_type': 'Customer',
        'party': sales_invoice.customer,
        'paid_amount': data.get('amount'),
        'references': [{
            'reference_doctype': 'Sales Invoice',
            'reference_name': invoice,
            'allocated_amount': sales_invoice.total
        }],
        'reference_no': data.get('transaction_id'),
        'reference_date': today(),
        'cost_center': 'Main - LIO',
        'received_amount': data.get('amount'),
        'paid_from': 'Debtors - LIO',
        'paid_from_account_currency': frappe.defaults.get_user_default('default_currency'),

        'docstatus': 1
    }
    entry_doc = frappe.get_doc(entry)
    entry_doc.insert(ignore_permissions=True, ignore_mandatory=True)
    frappe.db.commit()
