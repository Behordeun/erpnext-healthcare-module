import os, json, requests, sys, time, pika
from dotenv import load_dotenv
from queue import Queue
# from confluent_kafka import Consumer, KafkaException, KafkaError
from multiprocessing import Process
import frappe
from lafia.api.patient.patient import get_patient_doc,update_patient,create_patient
from lafia.api.practitioner.practitioner import update_practitioner
from lafia.api.encounter.encounter import get_encounter_doc,create_encounter
from lafia.lafiaio.doctype.claims.claims import get_claims_doc,create_claims
from lafia.lafiaio.doctype.organization.organization import get_org_doc,create_organization
from lafia.api.procedure.procedure import create_procedure
from lafia.api.condition.condition import create_condition_request
from lafia.api.medication_request.medication_request import create_medication_request
from lafia.api.appointment.appointment import create_appointment,create_appointment_doc
from lafia.lafiaio.doctype.appointment_response.appointment_response import appointment_response
from lafia.lafiaio.doctype.coverage.coverage import get_coverage,create_coverage
from lafia.lafiaio.doctype.claimresponse.claimresponse import create_claim_response

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")
lafia_app_url = os.environ.get("BASE_URL")
headers = {
      'Authorization': 'token ' + os.environ.get('API_KEY') + ':' + os.environ.get('API_SECRET')
    }

sleepTime = 10
print(' [*] Sleeping for ', sleepTime, ' seconds.')
# time.sleep(sleepTime)

print(' [*] Connecting to server ...')

token_key = "token"

params = pika.URLParameters(os.environ.get('RABBITMQ_URL'))

params.blocked_connection_timeout = 2000
params.heartbeat = 2000

connection = pika.BlockingConnection(params)
channel = connection.channel()

channel.queue_declare(queue="{0}-resourceCreated".format(os.environ.get("SERVER_ENV")))

def login_administrator(base_url):
  url = base_url + '/api/method/login'
  credentials = {"usr":os.environ.get('APP_USER'), "pwd":os.environ.get('PASSWORD')}
  print(credentials)
  response = requests.post(url, json=credentials)
  print(response.__dict__)
  sid = response.headers.get("Set-Cookie").split(";")[0].split("=")[1]
  print(sid)
  print(url)
  return sid

def make_post_request(provider, url_path, json_data):
  print(' [*] Connecting to server ...')

  if provider == "lafia":
    base_url = lafia_app_url
    url = lafia_app_url + url_path

  elif provider == "localhost" or "":
    url = "http://" + "localhost" + url_path
    base_url = provider
  
  else:
    url = "https://" + provider + url_path
    base_url = provider
  # base_url = lafia_app_url
  # url = lafia_app_url + url_path
  
  auth_sid = login_administrator(base_url)
  cookies = {
    "sid": auth_sid
  }
  response = requests.post(url, json=json_data, cookies=cookies)
  print(response.__dict__)
  print(response.text)
  return response.json()

@frappe.whitelist()
def update_patient_id(email):
  try:
    patient_doc = frappe.get_last_doc(doctype='Patient', filters={"email": email})
    patient_doc.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True
    patient_doc.patient_server_id = 'id'
    patient_doc.save()
    return patient_doc
  except:
      e = sys.exc_info()[1]
      frappe.local.response = frappe._dict({
          'status': 'error',
          'message': e
      })
      frappe.local.response['http_status_code'] = 500


def create_patient_request(data):

    patient_data= get_patient_doc(data)#
    url_path = '/api/method/lafia.api.patient.patient.create_patient'
  
    response = make_post_request(data.get("provider"), url_path, patient_data)
    print(response)
    

def create_users_request(data):
    users_data = {
      "email": data.get("email"),
      "gender": data.get("gender"),
      "first_name": data.get("first_name"),
      "last_name": data.get("last_name"),
      "password": data.get("patient_password"),
      "default_role": "Patient"
    }
    print("users_data")
    print("========")
    print(users_data)
    url_path = '/api/method/lafia.api.users.users.sign_up'
    response = make_post_request(data.get("provider"), url_path, users_data)
    print(response)
    

def create_media_request(data):
  url_path = '/api/method/lafia.api.media.media.create_media'
  response = make_post_request(data.get("provider"), url_path, {"media_data": data})
  print(response)

def create_consent_request(data):
  url_path = '/api/method/lafia.api.consent.consent.create_consent'
  response = make_post_request(data.get("provider"), url_path, {"consent_data": data})
  print(response)

def create_patient_video_request(data):
  url_path = '/api/method/lafia.api.patient_video.patient_video.create_patient_video'
  response = make_post_request(data.get("provider"), url_path, {"video_data": data})
  print(response)

def create_encounter_request(data):
  # encounter_data = get_encounter_doc(data)
  url_path = '/api/method/lafia.api.encounter.encounter.create_encounter'
  response = make_post_request(data.get("provider"), url_path, data)
  print(response)

def create_claim_request(data):
  claim_data = get_claims_doc(data)
  url_path = '/api/method/lafia.lafiaio.doctype.claims.claims.create_claims'
  response = make_post_request(data.get("provider"), url_path, claim_data)
  print(response)

def create_organization_request(data):
  org_data = get_org_doc(data)
  url_path = '/api/method/lafia.lafiaio.doctype.organization.organization.create_organization'
  response = make_post_request(data.get("provider"), url_path, org_data)
  print(response)

def consumer_callback(ch, method, properties, body):
  print(body)
  print(" [x] Received %r" % body.decode())
  time.sleep(body.count(b'.'))
  print(" [x] Done")
  # ch.basic_ack(delivery_tag=method.delivery_tag)

  data = json.loads(body)
  print(data)
  if data["status"] == "success":
    if data.get("resource_type"):
      if data["resource_type"].lower() == "patient":
        if data.get("patient_password"):
          create_patient(data)
          # create_users_request(data)
        else:
          update_patient(data)
        # create_users_request(data)
        # create_patient_request(data)
      elif data["resource_type"].lower() == "practitioner":
        update_practitioner(data)
      elif data["resource_type"].lower() == "encounter":
        create_encounter(data['data'])
      elif data["resource_type"].lower() == "media":
        create_media_request(data["data"])
      elif data["resource_type"].lower() == "claim":
        create_claims(data["data"])
      elif data["resource_type"].lower() == "claimresponse":
        create_claim_response(data["data"])
      elif data["resource_type"].lower() == "organization":
        create_organization(data)
      elif data["resource_type"].lower() == "procedure":
        create_procedure(data["data"])
      elif data["resource_type"].lower() == "condition":
        create_condition_request(data["data"])
      elif data["resource_type"].lower() == "medicationrequest":
        create_medication_request(data["data"])
      elif data["resource_type"].lower() == "appointment":
        create_appointment_doc(data["data"])
      elif data["resource_type"].lower() == "appointment_response":
        appointment_response(data["data"])
      elif data["resource_type"].lower() == "coverage":
        create_coverage(data["data"])
    elif data["videoUrl"]:
      create_patient_video_request(data)

def patient_consumer():
  channel.basic_qos(prefetch_count=1)

  channel.basic_consume(on_message_callback=consumer_callback, queue="{0}-resourcesCreated".format(os.environ.get("SERVER_ENV")), auto_ack=True)
  
  print(' [*] Waiting for messages. To exit press CTRL+C')
  channel.start_consuming()
  connection.close()

# def patient_consumer():
#   topics = os.environ.get("KAFKA_TOPICS").split(",")

#   # Consumer configuration
#   # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
#   conf = {
#       'bootstrap.servers': os.environ.get("KAFKA_URL"),
#       'security.protocol': "PLAINTEXT",
#       'group.id': "%s-consumer" % "prod",
#       'session.timeout.ms': 60000,
#       'default.topic.config': {'auto.offset.reset': 'earliest'},
#       # 'sasl.mechanisms': 'SCRAM-SHA-256',
#       # 'sasl.username': "ms48nmc7",
#       # 'sasl.password': "rd9RwmTYPoYgSWR5ZCaS8xhmfSU5IJve",
#   }

#   c = Consumer(**conf)
#   c.subscribe(topics)
#   print(' [*] Waiting for messages. To exit press CTRL+C')
#   try:
#       while True:
#           msg = c.poll(timeout=10.0)
#           if msg is None:
#               continue
#           if msg.error():
#               # Error or event
#               if msg.error().code() == KafkaError._PARTITION_EOF:
#                   # End of partition event
#                   sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
#                                     (msg.topic(), msg.partition(), msg.offset()))
#               elif msg.error():
#                   # Error
#                   raise KafkaException(msg.error())
#           else:
#               # Proper message
#               sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
#                                 (msg.topic(), msg.partition(), msg.offset(),
#                                 str(msg.key())))
#               print(json.loads(msg.value()))
#               consumer_callback(msg.value())

#   except KeyboardInterrupt:
#       sys.stderr.write('%% Aborted by user\n')

#   # Close down consumer to commit final offsets.
#   c.close()
  # channel.basic_qos(prefetch_count=1)

  # channel.basic_consume(on_message_callback=consumer_callback, queue="resourceCreated", auto_ack=True)
  


if __name__ == "__main__":
    patient_consumer()
