import frappe, twilio, os, sys

from dotenv import load_dotenv

load_dotenv()

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant

# Substitute your Twilio AccountSid and ApiKey details
ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
API_KEY_SID = os.environ.get("TWILIO_API_KEY_SID")
API_KEY_SECRET = os.environ.get("TWILIO_API_KEY_SECRET")

print(ACCOUNT_SID, API_KEY_SID)

@frappe.whitelist(allow_guest=True)
def get_twilio_auth_token(username, room=None):
  # Create an Access Token
  token = AccessToken(ACCOUNT_SID, API_KEY_SID, API_KEY_SECRET)

  # Set the Identity of this token
  token.identity = username

  # Grant access to Video
  grant = VideoGrant(room= room if room else 'cool room')
  token.add_grant(grant)

  # Serialize the token as a JWT
  jwt = token.to_jwt()
  print(jwt)
  return(jwt.decode())

@frappe.whitelist(allow_guest=True)
def create_patient_video(patient, video_url, video_time):
  # try :
    patient_video_doc = frappe.get_doc({
      "doctype": "Patient Video",
      "patient": patient,
      "video": """<video width="320" height="240" controls>
        <source src={video_url} type="video/mp4">
        Your browser does not support the video tag.
      </video>""".format(video_url=video_url)
                
    })
    patient_video_doc.insert()
    patient_video_doc.save()
    return patient_video_doc


@frappe.whitelist(allow_guest=True)
def make_call(username, room=None):
  print("=======")
  print(username)
  # Create an Access Token
  token = AccessToken(ACCOUNT_SID, API_KEY_SID, API_KEY_SECRET)

  # Set the Identity of this token
  token.identity = username

  # Grant access to Video
  grant = VideoGrant(room= room if room else 'cool room')
  token.add_grant(grant)

  # Serialize the token as a JWT
  jwt = token.to_jwt()
  frappe.publish_realtime('call', {"username": username, "room": room, "token": jwt.decode()})
  print(jwt)
  return(jwt.decode())