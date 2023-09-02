import frappe
import sys
import requests
import json
import os
from dotenv import load_dotenv
from lafia.api.services.brokers.producer import producer
from lafia.utils.fhir_utils import get_code, get_identifier, get_fullname, get_telecom,\
    random_string,get_addresses,ext_code_list,get_coms,retrieve_addresses
from lafia.api.users.users import sign_up
from frappe.utils import get_site_name,get_date_str,today,add_to_date
# from erpnext.accounts.doctype.subscription.subscription import  
from frappe.desk.form.save import set_local_name,send_updated_docs
from frappe.desk.form.load import run_onload        


load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

company = frappe.db.get_value("Employee",{'user_id':frappe.session.user},'company') \
        or frappe.defaults.get_user_default('company')

def fhir_object(doc):
    fhir_schema = {
        "resourceType": "Practitioner",
        "identifier": get_identifier(doc.get("identifier") if doc.get("identifier") else []),
        "active": False if doc.status == "Disabled" else True,
        "name": get_fullname(doc.first_name, doc.last_name, doc.middle_name),
        "telecom": get_telecom(doc.get("email"),doc.get("mobile_phone") if doc.get("mobile_phone") else doc.get("residence_phone")),
        "gender": doc.gender.lower() if doc.gender else "",
        "birthDate": get_date_str(doc.get("birthdate")) if doc.birthdate else "",
        "address": get_addresses(doc.get("address")) if doc.address else "",
        "qualification": get_qualifications(doc.get("qualification")) if doc.get("qualification") else "",
        "communication": get_practitioner_communication(doc.get("communication")) if doc.get("communication") else "",
        "extension": get_practitioner_extension(doc)
    }
    print(fhir_schema)
    return fhir_schema

def get_practitioner_extension(doc):
    extension_list = []
    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/lafiaPractitionerMaritialStatus",
        "valueCodeableConcept": {
            "coding": [get_code("Marital Status Code",doc.marital_status)] if doc.marital_status else []
        }
    }) 

    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/lafiaCareTypesAndInterests",
        "valueCodeableConcept": {
            "coding": ext_code_list("Healthcare Service Specialty",doc.get('specialty'),'specialty')
        } if doc.get('specialty') else []
    }) 

    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/lafiaUserAnthropometry",
        "extension":[
            {
                "url": "height",
                "valueQuantity": {
                "value": doc.height,
                "unit": "ft",
                "system": "http://unitsofmeasure.org",
                "code": "ft_i"
                }
            },
            {
                "url": "weight",
                "valueQuantity": {
                "value": doc.weight,
                "unit": "kg",
                "system": "http://unitsofmeasure.org",
                "code": "kg"
                }
            }
        ]
    })

    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/practitioner-managing-organization",
        "valueReference": {
                "reference":"Organization" + "/" + frappe.get_doc("Company",company).get('fhir_serverid'),
                "type": "Organization"
        } if company else {}
    })
    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/practitioner-consulting-charge",
        "valueMoney": {
            "value": doc.op_consulting_charge,
            "currency": frappe.get_doc("Company",company).get('default_currency') if company else ""
        }
    })
    # frappe.errprint(extension_list)
    return extension_list



def practitioner_lafia_before_insert_script(doc, method):
    if not doc.fhir_serverid:
        fhir_schema = fhir_object(doc)
        print(lafia_base_url)

        response = requests.post(
            lafia_base_url + '/Practitioner', json=fhir_schema)
        
        practitioner_fhir_object = response.json()
        print(practitioner_fhir_object)
        
        if response.status_code == 201:
            doc.fhir_serverid = practitioner_fhir_object.get("id")
            
        else:
            frappe.throw("An error occured")
            print(response.__dict__)

def practitioner_on_update(doc, method):
    if doc.fhir_serverid:
        fhir_schema = fhir_object(doc)
        fhir_schema["id"] = doc.fhir_serverid
        
        url = lafia_base_url + '/Practitioner/' + doc.fhir_serverid
        response = requests.put(url, json=fhir_schema)    
        print(response.json())

        print(doc)

    if doc.role:
        create_practitioner_role(doc)
    
def practitioner_on_delete(doc, method):
    response = requests.delete(
        lafia_base_url + '/Practitioner/' + doc.fhir_serverid)
    
    print(response.json())


def get_relationship_code(relationship):
    return {
        "code": relationship.get("code"),
        "system": relationship.get("system"),
        "display": relationship.get("display")
    }


def get_period(period):
    return {
        "start": str(period[0].get("start")).replace(" ", "T") if len(period) and period[0].get("start") else '',
        "end": str(period[0].get("end")).replace(" ", "T") if len(period) and period[0].get("end") else ''
    }


def get_practitioner_communication(communications):
    communication_list = []
    for communication in communications:
        communication_code = get_code(
            'Language Code', communication.get("language"))
        communication_list.append({
            "coding": get_communication_code(communication_code),
            "text": communication_code.get("display")
        })
    return communication_list


def get_communication_code(communication):
    return {
        "code": communication.get("code"),
        "system": communication.get("system"),
        "display": communication.get("display")
    }

def get_practitioner_qualifications(qualification):
    qualification_code = get_code("Qualification Code", qualification)
    return {
        "coding": [qualification_code],
        "text": qualification_code.get("display")
    }


def get_codeable_concept(doctype, qualification):
    qualification_code = get_code(doctype, qualification)
    return {
        "coding": [qualification_code],
        "text": qualification_code.get("display")
    }


def get_qualifications(qualifications):
    qualification_list = []
    for qualification in qualifications:
        qualification_list.append({
            "identifier": [
                {
                    "system": "http://example.org/UniversityIdentifier",
                    "value": "12345"
                }
            ],
            "code": get_practitioner_qualifications(qualification.get("code")),
            "period": {
                "start": get_date_str(qualification.get("start")) if qualification.get("start") else "",
                "end": get_date_str(qualification.get("end")) if qualification.get("end") else ""
            },
            "issuer": {
                "display": qualification.get("issuer") if qualification.get("issuer") else ""
            }
        })
    return qualification_list

def get_email(telecom):
    email_addresses = []
    for comms in telecom:
        if comms.get("system") == "email":
            email_addresses.append(comms.get("value"))
    return email_addresses


def get_phone(telecom):
    phone_numbers = []
    for comms in telecom:
        if comms.get("system") == "phone":
            phone_numbers.append(comms.get("value"))
    return phone_numbers


def practitioner_lafia_after_save(doc, method):
    email = doc.email
    last_name = doc.last_name
    first_name = doc.first_name
    password = random_string(15)
    phone = doc.mobile_phone if doc.mobile_phone else doc.residence_phone
    
    
    event_body = {
        "resource_type": "Practitioner",
        "resource_id": doc.fhir_serverid,
        "data": {
            "last_name": last_name,
            "first_name": first_name,
            "email": email,
            "password": password,
            "gender": doc.gender.lower() if doc.gender else "",
            "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
            "phone": phone,
            "organization_id": frappe.get_doc("Company",company).get('fhir_serverid')
        }
    }
    print(event_body)
    producer('{0}-createResources'.format(os.environ.get("SERVER_ENV")), json.dumps(event_body))

    """Create a User account"""
    sign_up(email, first_name, last_name, password, doc.gender,'practitioner', ["Physician","Accounts User"])
    user_doc = frappe.get_doc("User", email)
    doc.user_id = user_doc.get("name") if user_doc.get("name") else email
    doc.save()
    # frappe.db.set_value('Healthcare Practitioner', doc.name, 'user_id', user_doc.get("name") if user_doc.get("name") else email)
    
    """Create Employee account if Checked"""
    if doc.register_as_employee:
        create_employee(doc)

    frappe.db.commit()
    
    if not doc.customer_account:
        create_customer(doc)

    """Create Subscription"""
    if doc.account_type == "Private Practitioner":
        create_subscription(doc)


def create_employee(doc):
    employee_data = {
        "doctype": "Employee",
        "first_name": doc.first_name,
        "last_name": doc.last_name,
        "gender": doc.gender,
        "date_of_birth": doc.birthdate,
        "date_of_joining": today(),
        "user_id": doc.email
    }
    employee_doc = frappe.get_doc(employee_data)
    employee_doc.insert()
    # frappe.db.set_value('Healthcare Practitioner', doc.name, 'employee', employee_doc.get('name'))
    doc.employee = employee_doc.get('name')
    doc.save()
    
def create_practitioner_role(doc):
    role = frappe.db.get_value("PractitionerRole",{'practitioner':doc.name},'name')
    if role:
        role_doc = frappe.get_doc("PractitionerRole",role)
        role_doc.update({
            "roles": [{"role": doc.role}],
            "specialty": doc.get('specialty')
        })
        role_doc.save()
        frappe.db.commit()
    else:
        role_data = {
            "doctype": "PractitionerRole",
            "practitioner": doc.name,
            "organization": company if company else "",
            "specialty": doc.get("specialty") if doc.get("specialty") else [],
            "roles": [{"role": doc.role}]
        }
        role_doc = frappe.get_doc(role_data)
        role_doc.insert()
        frappe.db.commit()
        print("practitioner role created")

def create_customer(doc):
    customer = frappe.get_doc({
        'doctype': 'Customer',
        'customer_name': doc.practitioner_name,
        'customer_group': frappe.db.get_single_value('Selling Settings', 'customer_group'),
        'territory' : frappe.db.get_single_value('Selling Settings', 'territory'),
        'customer_type': 'Individual',
        'default_currency': frappe.get_doc("Company",company).get('default_currency'),
        'default_price_list': frappe.db.get_single_value('Selling Settings', 'selling_price_list')
    }).insert(ignore_permissions=True, ignore_mandatory=True)

    # frappe.db.set_value('Healthcare Practitioner', doc.name, 'customer_account', customer.name)
    doc.customer_account = customer.name
    doc.save()

def create_subscription(doc):
    subscription = {
        'doctype': 'Subscription',
        'party_type': 'Customer',
        'party': frappe.db.get_value(doc.doctype,doc.name,'customer_account'),
        'start_date': today(),
        'end_date': add_to_date(today(),months=1),
        'generate_invoice_at_period_start': 1,
        'cancel_at_period_end': 1,
        'plans': [{
            'plan': "Physician Plan",
            'qty': 1
        }]
    }
    print(subscription)
    subscription_doc = frappe.get_doc(subscription)
    subscription_doc.insert(ignore_permissions=True, ignore_mandatory=True)
    frappe.db.commit()
    # get_subscription_updates(subscription_doc.get('name'))
    

def update_practitioner(data):
    name = frappe.db.get_value("Healthcare Practitioner",{"fhir_serverid":data.get('id')},'name')
    if name:
        practitioner = frappe.get_doc("Healthcare Practitioner",name)
        doc = practitioner_doc(data)
        practitioner.update(doc)
        practitioner.save()
        frappe.db.commit()
    return


def practitioner_doc(data):
    practitioner_doc_ = {
        "first_name": data.get("name")[0].get("given")[0],
        "middle_name": data.get("name")[0].get("given")[1] if data.get("name")[0].get("given")[1] else "",
        "last_name": data.get("name")[0].get("family"),
        "mobile_phone": get_coms("phone", data.get("telecom")),
        "gender": data.get("gender").capitalize(),
        "marital_status": data.get("extension")[0].get("valueCodeableConcept").get("coding")[0].get('display') if data.get("extension")[0].get("valueCodeableConcept").get("coding")[0] else "",
        "birthdate": data.get("birthDate"),
        "height": data.get("extension")[2].get("extension")[0].get("valueQuantity").get("value") if data.get("extension")[2].get("extension") else 0,
        "weight": data.get("extension")[2].get("extension")[1].get("valueQuantity").get("value") if data.get("extension")[2].get("extension")[1] else 0,
        "specialty": get_care_type(data) if data.get("extension")[0].get("valueCodeableConcept").get("coding") else [],
        "address": retrieve_addresses(data.get("address")) if data.get("address") else [],   
    }
    return practitioner_doc_

def get_care_type(data):
    care_list = []    
    for care in data.get("extension")[1].get("valueCodeableConcept").get("coding"):
        care_list.append({
            "specialty": care.get('display')
        })
    return(care_list)

"""Validate Subscription"""
@frappe.whitelist()
def validate_subscription():
    user = frappe.session.user
    if user != "Administrator" and "Physician" in frappe.get_roles(user):
        name,customer,account_type = frappe.db.get_value("Healthcare Practitioner",
                                        {'user_id':user},['name','customer_account','account_type'])
    
        if account_type == "Private Practitioner":
            subscription = frappe.db.sql(f""" SELECT * FROM `tabSubscription` WHERE 
            (party_type='Customer' and party='{customer}') AND 
            ('{today()}' = current_invoice_start OR '{today()}' BETWEEN current_invoice_start AND current_invoice_end) AND 
            status='Active' """,
            as_dict=True) if customer else ""
            
            msg = "User do not have an active Subscription"
            if not subscription:
                # return "no subscription"
                frappe.throw(msg)

            if subscription:
                print(subscription)
                valid = ""
                for sub in subscription:
                    invoices = frappe.get_doc("Subscription", sub.get('name')).invoices
                    if invoices:
                        sales_invoice = frappe.get_doc("Sales Invoice",invoices[0].get('invoice'))
                        if sales_invoice.status == "Paid":
                            valid += "Paid"
                if not valid:
                    frappe.throw(msg)


@frappe.whitelist()
def savedocs(doc, action):
    """save / submit / update doclist"""
    try:
        doc = frappe.get_doc(json.loads(doc))
        set_local_name(doc)

        # action
        doc.docstatus = {"Save": 0, "Submit": 1, "Update": 1, "Cancel": 2}[action]

        # validate subscription
        # validate_subscription()
        
        if doc.docstatus == 1:
            doc.submit()
        else:
            doc.save()

        # update recent documents
        run_onload(doc)
        send_updated_docs(doc)
        

        frappe.msgprint(frappe._("Saved"), indicator="green", alert=True)
    except Exception:
        frappe.errprint(frappe.utils.get_traceback())
        raise


