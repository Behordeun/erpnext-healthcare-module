import frappe, sys, os, json
from frappe.utils import get_site_name,cint,today,get_url,get_formatted_email
from lafia.api.services.brokers.producer import producer
from frappe.core.doctype.user.user import User,test_password_strength,\
    handle_password_test_fail,_get_user_for_update_password,reset_user_data
from frappe.utils.password import update_password as _update_password
from frappe import _
from dotenv import load_dotenv
load_dotenv()

lafia_app_url = os.environ.get("BASE_URL")


@frappe.whitelist(allow_guest=True)
def sign_up(email, first_name, last_name, password, gender, template, default_role=None, birth_date=None, phone=None):
  try:
    print("users_data")
    print("========")
    print(password)
    print(template)

    user = frappe.db.get("User", {"email": email})
    if user:
        if user.disabled:
            return 0, _("Registered but disabled")
        else:
            frappe.local.response = frappe._dict({
                    'status': 'error',
                    'message': 'Already Registered'
                })
            frappe.local.response['http_status_code'] = 409;
            return
    else:
        if frappe.db.sql("""select count(*) from tabUser where
			HOUR(TIMEDIFF(CURRENT_TIMESTAMP, TIMESTAMP(modified)))=1""")[0][0] > 300:

            frappe.respond_as_web_page(_('Temporarily Disabled'),
                                       _('Too many users signed up recently, so the registration is disabled. Please try back in an hour'),
                                       http_status_code=429)
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "gender": gender,
            "first_name": first_name,
            "last_name": last_name,
            "birth_date": birth_date,
            "phone": phone,
            "enabled": 1,
            "new_password": password,
            # TODO Remove Test2
            "module_profile": "Test2",
            "send_welcome_email": 0
            # "user_type": "System User"
        })
        user.flags.ignore_permissions = True
        user.flags.ignore_password_policy = True
        user.insert()
        send_user_welcome_email(user.email,user.first_name,user.last_name,password,template)
        frappe.db.commit()
        
        # set default signup role as per Portal Settings
        if not default_role:
            default_role = frappe.db.get_value(
            "Portal Settings", None, "default_role")
            user.add_roles(default_role)
        else:
            for role in default_role:
                user.add_roles(role)

        if user.flags.email_sent:
            return 1, frappe._("Please check your email for verification")
        else:
            return 2, frappe._("Please ask your administrator to verify your sign-up")
        return user
  except:
    e = sys.exc_info()[1]
    frappe.local.response = frappe._dict({
        'status': 'error',
        'message': e
    })
    frappe.local.response['http_status_code'] = 500


"""Sends password change for Practitioner over RabbitbMQ """
class NewUser(User):
    def email_new_password(user,new_password=None):
        if new_password:
            print(new_password)
            if ("Physician" in frappe.get_roles(user.name)):
                resource = "Practitioner"
                id = frappe.db.get_value("Healthcare Practitioner",{"email":user.name},'name')
                doc = frappe.get_doc("Healthcare Practitioner",id)
            
                event_body = {
                    "resource_type": resource,
                    "resource_id": doc.fhir_serverid,
                    "data": {
                        "last_name": doc.last_name,
                        "first_name": doc.first_name,
                        "email": doc.email,
                        "password": new_password,
                        "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
                    }
                }
                producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))
                frappe.errprint(event_body)
                _update_password(user=user.name, pwd=new_password, logout_all_sessions=False)
                user.save()
            else:
                _update_password(user=user.name, pwd=new_password, logout_all_sessions=False)
                user.save()


              
"""Overrides forget password change for Practitioner and sends over RabbitbMQ """
@frappe.whitelist(allow_guest=True)
def update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
	# validate key to avoid key input like ['like', '%'], '', ['in', ['']]
    if key and not isinstance(key, str):
        frappe.throw(_("Invalid key type"))

    result = test_password_strength(new_password, key, old_password)
    feedback = result.get("feedback", None)

    if feedback and not feedback.get("password_policy_validation_passed", False):
        handle_password_test_fail(result)

    res = _get_user_for_update_password(key, old_password)
    if res.get("message"):
        frappe.local.response.http_status_code = 410
        return res["message"]
    else:
        user = res["user"]

    logout_all_sessions = cint(logout_all_sessions) or frappe.db.get_single_value(
        "System Settings", "logout_on_password_reset"
    )
    _update_password(user, new_password, logout_all_sessions=cint(logout_all_sessions))

    if ("Physician" in frappe.get_roles(user)):
        resource = "Practitioner"
        id = frappe.db.get_value("Healthcare Practitioner",{"email":user},'name')
        doc = frappe.get_doc("Healthcare Practitioner",id)
    
        event_body = {
            "resource_type": resource,
            "resource_id": doc.fhir_serverid,
            "data": {
                "last_name": doc.last_name,
                "first_name": doc.first_name,
                "email": doc.email,
                "password": new_password,
                "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
            }
        }
        producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))
        frappe.errprint(event_body)

    user_doc, redirect_url = reset_user_data(user)

    # get redirect url from cache
    redirect_to = frappe.cache().hget("redirect_after_login", user)
    if redirect_to:
        redirect_url = redirect_to
        frappe.cache().hdel("redirect_after_login", user)

    frappe.local.login_manager.login_as(user)

    frappe.db.set_value("User", user, "last_password_reset_date", today())
    frappe.db.set_value("User", user, "reset_password_key", "")

    if user_doc.user_type == "System User":
        return "/app"
    else:
        return redirect_url if redirect_url else "/"


def send_user_welcome_email(email,first_name,last_name,password,template):
    args = {
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
        "user": email,
        "site_url": f"{lafia_app_url}/login",
        "link": "https://play.google.com/store/apps/details?id=com.parralelscore.lafia",
		"created_by": "Administrator"
    }
    print(args)
    sender = frappe.session.user
    print(sender)
    # site_name = frappe.db.get_default("site_name") or frappe.get_conf().get("site_name")
    subject="Welcome to Lafia"
    frappe.sendmail(
        recipients=[email],
        # sender=sender,
        subject=subject,
        template=template,
        args=args,
        header=[subject, "green"],
    )
    print("email sent")


# def create_module_profile(name):
#     module_doc = frappe.get_doc({
#         "module_profile_name": "Physician"
#         "docstatus": 0
#     })