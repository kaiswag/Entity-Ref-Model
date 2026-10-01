#!/usr/bin/env python3
"""Fetch the entity schema and version of a Shopware 6 instance via the Admin API.

Credentials come from environment variables, nothing is stored:
  SW_URL            e.g. https://shop.example.com
  SW_CLIENT_ID      integration access key ID   (or admin username, see SW_GRANT)
  SW_CLIENT_SECRET  integration secret          (or admin password)
  SW_GRANT          "client_credentials" (default) or "password"
  SW_LABEL          optional label shown on the page, e.g. "Customer X staging"

Writes entity-schema.json and version.json next to this script.
"""
import json, os, sys, urllib.request

url = os.environ.get("SW_URL", "").rstrip("/")
cid, secret = os.environ.get("SW_CLIENT_ID"), os.environ.get("SW_CLIENT_SECRET")
grant = os.environ.get("SW_GRANT", "client_credentials")
if not (url and cid and secret):
    sys.exit("Set SW_URL, SW_CLIENT_ID and SW_CLIENT_SECRET (see docstring).")

def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url + path, method=method, headers=headers,
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

if grant == "password":
    auth = {"grant_type": "password", "client_id": "administration", "username": cid, "password": secret, "scopes": "write"}
else:
    auth = {"grant_type": "client_credentials", "client_id": cid, "client_secret": secret}
token = call("POST", "/api/oauth/token", auth)["access_token"]

here = os.path.dirname(os.path.abspath(__file__))
schema = call("GET", "/api/_info/entity-schema.json", token=token)
version = call("GET", "/api/_info/version", token=token).get("version", "6.x")
json.dump(schema, open(os.path.join(here, "entity-schema.json"), "w"))
json.dump({"version": version, "shop": os.environ.get("SW_LABEL", url.split("//")[-1])},
          open(os.path.join(here, "version.json"), "w"))
print(f"ok: {len(schema)} entities, Shopware {version}")
