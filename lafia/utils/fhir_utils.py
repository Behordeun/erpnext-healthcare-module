import frappe
from frappe.utils import get_date_str
import random, string

def get_performer(performers):
  return [
    {
      "function":{
        "coding": [get_code("Procedure Performer Code", performer.get("function"))]
        } if performer.get("function") else "",
      "actor": get_optional_doctype(performer.get("actor_type"), performer.get("actor")),
      "onBehalfOf": get_reference("Organization", performer.get("on_behalf_of").split("-")[2])
    } for performer in performers
  ]

def get_optional_doctype(doctype_field, value_field):
  return get_reference(doctype_field, value_field.split("-")[2]) if doctype_field and value_field else ""

# def get_reference(resource_type, fhir_id):
#   resource = resource_type if resource_type != "Patient_LafiaIO" else "Patient"
#   return { "reference": resource.replace(" ", "").replace("FHIR", "").replace("_", "") + "/" + fhir_id }

def get_code(doctype, name):
  code_doc = frappe.get_doc(doctype, name)
  return {
    "code": code_doc.get("code"),
    "display": code_doc.get("display"),
    "system": code_doc.get("system")
  }


def get_code_list(doctype, code_concepts, code_key):
  code_list = []
  for code_concept in code_concepts:
    code_concept_code = get_code(doctype, code_concept.get(code_key))
    code_list.append({
        "coding": code_concept_code,
        "text": code_concept_code.get("display")
    })
  return code_list
  
def get_identifier(identifiers):
  identifier_list = []
  for identifier in identifiers:
      print("++++++++++")
      print(identifier.__dict__)
      identifier_list.append({
          "use": identifier.get("use").lower(),
          "type": {
              "coding": [get_code("Identifier Code", identifier.get("type"))],
              "text": get_code("Identifier Code", identifier.get("type")).get("display")
          },
          "system": "urn:oid:1.2.36.146.595.217.0.1",
          "value": identifier.get("value") if identifier.get("value") else "",
          "period": {
              "start": get_date_str(identifier.get("start")) if identifier.get("start") else '',
              "end": get_date_str(identifier.get("end")) if identifier.get("end") else ''
          },
          "assigner": {
              "display": identifier.get("assigner") if identifier.get("assigner") else "LafiaIO"
          }
      })
  return identifier_list


def get_marital_status_code(status):
  marital_status = {
    "coding": [get_code("Marital Status Code", status)],
    "text": get_code("Marital Status Code", status).get("display")
  }
  return marital_status


def get_contact(contacts):
  contact_list = []
  for contact in contacts:
    contact_list.append({
      "name": contact.get("human_name"),
      "relationship": {
        "coding": [get_code("Relationship Code", contact.get("relationship"))],
        "text": get_code("Relationship Code", contact.get("relationship")).get("display")
      } if contact.get("relationship") else "",
      "telecom": get_telecom(contact.get("email"), contact.get("mobile")),
      "address": {
        "use": "home",
        "type": "both",
        "line": contact.get("address"),
        "city": contact.get("city"),
        "state": contact.get("state"),
        "country": contact.get("country")
      }
    })
  return contact_list
  
# def get_patient(id):
# 	patient = frappe.db.get_value("Patient", {"fhir_serverid": id}, "name")
# 	return patient

# def get_practitioner(id):
# 	patient = frappe.db.get_value("Healthcare Practitioner", {"fhir_serverid": id}, "name")
# 	return patient

def get_fhir_doc(doctype, id):
  doc = frappe.db.get_value(doctype, {"fhir_serverid": id}, "name")
  return doc

def get_fullname(first_name, last_name=None, other_name=None, fullname=None):
    print(first_name, last_name, other_name)
    if fullname:
        name_list = []
        for name in fullname:
            print(name.get("given"))
            name_list.append({
                "use": name.get("use"),
                "family": name.get("family"),
                "given": " ".join(name.get("given")) if name.get("given") else '',
                "text": name.get("family") + " " + " ".join(name.get("given"))
            })
        return name_list
    else:
        name_list = [
            {
                "use": "official",
                "family": last_name,
                "given": [first_name, other_name],
                "text": first_name + " " + last_name if last_name else ''
            }
        ]
        return name_list


def get_period(period):
    return {
        "start": get_date_str(period[0].get("start")) if len(period) and period[0].get("start") else '',
        "end": get_date_str(period[0].get("end")) if len(period) and period[0].get("end") else ''
    }

def period(start,stop):
  return {
    "start": get_date_str(start),
    "end": get_date_str(stop)
  }


def get_telecom(email=None, phone=None, fax=None):
  telecom_list = []
  if email:
    telecom_list.append({
      "system": "email",
      "use": "home",
      "rank" : 0,
      "value": email
    })
  if phone:
    telecom_list.append({
      "use": "mobile",
      "rank" : 0,
      "system": "phone",
      "value": phone
    })
  if fax:
    telecom_list.append({
      "use": "mobile",
      "rank" : 0,
      "system": "fax",
      "value": fax
    })
  
  return telecom_list


def get_addresses(addresses):
    address_list = []
    for address in addresses:
        address_list.append({
            "use": address.get("use").lower(),
            "type": address.get("type").lower(),
            # "text": address.get("text") if address.get("text") else '',
            "text": (address.get("line")),
            "line": [address.get("line"),address.get("postal_code")] if address.get("line") else [],
            "city": address.get("city") if address.get("city") else '',
            # "district": address.get("district") if address.get("district") else '',
            "state": address.get("state") if address.get("state") else '',
            "postalCode": address.get("postal_code") if address.get("postal_code") else '',
            "country": address.get("country") if address.get("country") else '',
            # "period": {
            #     "start": get_date_str(address.get("start_date")) if address.get("start_date") else '',
            #     "end": get_date_str(address.get("end_date")) if address.get("end_date") else '',
            # }
        })
    return address_list

def random_string(length):
  """generate a random string"""
  lowercase_letters = string.ascii_lowercase
  uppercase_letters = string.ascii_uppercase
  digits = string.digits
  symbols = '!@#$%^&*()-_+=?'

  password = random.choice(lowercase_letters)  # Random lowercase letter
  password += random.choice(uppercase_letters)  # Random uppercase letter
  password += random.choice(digits)  # Random digit
  password += random.choice(symbols)  # Random symbol

  remaining_length = length - 4  # Minus 4 for the required characters
  password += ''.join(random.choices(lowercase_letters + uppercase_letters + digits + symbols, k=remaining_length))

  password_list = list(password)
  random.shuffle(password_list)
  password = ''.join(password_list)

  return password

def get_coms(type, telecom):
    for com in telecom:
        if com.get("system") == type:
            return com.get("value")



def retrieve_addresses(addresses):
  address_list = []
  for address in addresses:
      address_list.append({
          "use": address.get("use").capitalize(),
          "type": address.get("type").capitalize(),
          "line": address.get("text") if address.get("text") else '',
          "city": address.get("city") if address.get("city") else '',
          # "district": address.get("district") if address.get("district") else '',
          "state": address.get("state") if address.get("state") else '',
          "postal_code": address.get("postalCode") if address.get("postalCode") else '',
          "country": address.get("country") if address.get("country") else '',
          # "start_date": get_date_str(address.get("start")) if address.get("start") else '',
          # "end": get_date_str(address.get("end")) if address.get("end") else ''          
      })
  return address_list


def get_reference(doctype,docname):
  reference = None
  doc = frappe.get_doc(doctype, docname)
  if doctype == "Healthcare Practitioner":
    doct = "Practitioner"
  elif doctype == "Patient Encounter":
    doct = "Encounter"
  elif doctype == "Locations":
    doct = "Location"
  elif doctype == "Patient Appointment":
    doct = "Appointment"
  elif doctype == "Company":
    doct = "Organization"
  else:
    doct = doctype
  
  reference = str(doct) + "/" + doc.get("fhir_serverid")
  return {
		"reference": reference
		}

def get_reference_list(doctype, references, reference_key):
  reference_list = []
  print(references)
  for reference in references:
    reference_list.append(get_reference(doctype, reference.get(reference_key)))
  return reference_list


def get_practitioner(subject):
  reference = None
  doc = frappe.get_doc("Healthcare Practitioner", subject)
  reference = "Practitioner/" + doc.get("fhir_serverid")
  return {
    "reference": reference
    }
def get_encounter(subject):
  reference = None
  doc = frappe.get_doc("Patient Encounter", subject)
  reference = "Encounter/" + doc.get("fhir_serverid")
  return {
    "reference": reference
    }


def get_reference_table(references):
  reference_list = []
  for reference in references:
    reference_list.append(
      get_reference(reference.get('ref_type'),reference.get('ref_name'))
    )
  return reference_list

def format_datetime(date):
  return date.replace(" ","T") + "Z"

def get_annotation(annotations):
  annotation_list = []
  for annotation in annotations:
    annotation_list.append({
      "authorReference": get_reference(annotation.get('author_ref'),annotation.get('author')) if annotation.get('author') else "",
      "time": format_datetime(annotation.get('time')) if annotation.get('time') else "",
      "text": annotation.get('text')
    })
  return annotation_list

def get_contact_point(contacts):
  contact_list = []
  for contact in contacts:
    contact_list.append({
      "system": (contact.get("system")).lower(),
      "value": contact.get("value"),
      "use": (contact.get("use")).lower(),
      "rank": contact.get("rank"),
      "period": {
					"start": format_datetime(contact.get("start_date")) if contact.get("start_date") else "",
					"end": format_datetime(contact.get("end_date")) if contact.get("end_date") else ""
				}
    })
  return contact_list

def get_contact_detail(name,contact=None):
  return {
    "name":name,
    "telecom": get_contact_point(contact) if contact else ""
  }

def get_ratio(num,den):
  return {
    "numerator": {"value":num},
    "denominator": {"value":den}
  }

def ext_code_list(doctype, code_concepts, code_key):
  code_list = []
  for code_concept in code_concepts:
    code_list.append(get_code(doctype, code_concept.get(code_key)))
  return code_list

def get_codable(data,field):
    return data.get(field).get("coding")[0].get('display')
