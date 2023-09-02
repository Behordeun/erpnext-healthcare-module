import sys, os, requests, json
import frappe
from frappe.utils import get_bench_path,get_site_path
from dotenv import load_dotenv
import lakefs_client
from lakefs_client import models
from lakefs_client.client import LakeFSClient

load_dotenv()
# lakeFS credentials and endpoint
configuration = lakefs_client.Configuration()
configuration.username = os.environ.get("LAKEFS_KEY")
configuration.password = os.environ.get("LAKEFS_SECRET")
configuration.host = os.environ.get("LAKEFS_HOST")

client = LakeFSClient(configuration)

bench_path = get_bench_path()
site_path = get_site_path("private", "files").replace(".","")
repo = os.environ.get("LAKEFS_REPO")
branch = os.environ.get("LAKEFS_BRANCH")

def upload_object(object,resource,file):
    json_object = json.dumps(object)
    object_path = f"{bench_path}/sites/{site_path}/{file}.json"


    with open(object_path, "w") as outfile:
        outfile.write(json_object)
    
    
    with open(object_path, 'rb') as f:
        client.objects.upload_object(repository=repo, branch=branch,
                path=f'{resource}/{file}',content=f)

    print("Upload Successful")
