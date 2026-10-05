#!/usr/bin/env python3
"""Provision a fresh Home Assistant test instance and verify the appleJuice Core integration.

Usage: ha_provision.py [PORT] [CORE_HOST] [CORE_PASSWORD]
Defaults: 8123, 198.51.100.30, ha. Login afterwards: admin / admin.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PORT = sys.argv[1] if len(sys.argv) > 1 else "8123"
CORE = sys.argv[2] if len(sys.argv) > 2 else "198.51.100.30"
CORE_PW = sys.argv[3] if len(sys.argv) > 3 else "ha"
B = f"http://127.0.0.1:{PORT}"
CID = B + "/"
P = "_" + CORE.replace(".", "_") + "_9851_"
H = {"Content-Type": "application/json"}


def req(path, data=None, token=None, form=False, method=None):
    headers = dict(H)
    if token:
        headers["Authorization"] = "Bearer " + token
    body = urllib.parse.urlencode(data).encode() if form else (json.dumps(data).encode() if data is not None else None)
    if form:
        headers.pop("Content-Type")
    r = urllib.request.Request(B + path, body, headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:300]}


def token_from_code(code):
    return req("/auth/token", {"grant_type": "authorization_code", "code": code, "client_id": CID}, form=True)["access_token"]


def wait_up():
    for _ in range(90):
        try:
            urllib.request.urlopen(B + "/manifest.json", timeout=3)
            return
        except Exception:
            time.sleep(3)
    sys.exit("HA not reachable")


wait_up()
steps = req("/api/onboarding")
if isinstance(steps, list) and any(not s["done"] for s in steps):
    r = req("/api/onboarding/users", {"client_id": CID, "name": "Admin", "username": "admin", "password": "admin", "language": "de"})
    token = token_from_code(r["auth_code"])
    for step in ("core_config", "analytics"):
        req(f"/api/onboarding/{step}", {}, token, method="POST")
    req("/api/onboarding/integration", {"client_id": CID, "redirect_uri": CID}, token, method="POST")
else:
    f = req("/auth/login_flow", {"client_id": CID, "handler": ["homeassistant", None], "redirect_uri": CID})
    r = req("/auth/login_flow/" + f["flow_id"], {"username": "admin", "password": "admin", "client_id": CID})
    token = token_from_code(r["result"])

version = req("/api/config", token=token)["version"]
print("HA", version)

entries = req("/api/config/config_entries/entry", token=token)
if not any(e["domain"] == "applejuice_core" for e in entries):
    flow = req("/api/config/config_entries/flow", {"handler": "applejuice_core", "show_advanced_options": False}, token, method="POST")
    bad = req("/api/config/config_entries/flow/" + flow["flow_id"], {"url": CORE, "port": 9851, "password": "falsch", "tls": False}, token, method="POST")
    print("wrong password ->", bad.get("errors"))
    ok = req("/api/config/config_entries/flow/" + flow["flow_id"], {"url": CORE, "port": 9851, "password": CORE_PW, "tls": False}, token, method="POST")
    print("config flow ->", ok.get("type"), ok.get("title"))
    time.sleep(8)

states = {s["entity_id"]: s for s in req("/api/states", token=token)}
mine = {k: v for k, v in states.items() if P in k or "applejuice_network" in k}
# Buttons zeigen bis zum ersten Druck "unknown" (HA-intern, state ist final); das ist normal.
broken = [k for k, v in mine.items() if v["state"] in ("unavailable", "unknown") and not k.startswith("button.")]
print(len(mine), "applejuice entities; unavailable/unknown (ohne Buttons):", broken or "keine")


def state(eid):
    return req("/api/states/" + eid, token=token)["state"]


def call(domain, service, data):
    req(f"/api/services/{domain}/{service}", data, token, method="POST")
    time.sleep(2)


checks = [
    ("number", "max_upload", 777, "777"),
    ("number", "max_download", 2048, "2048"),
    ("number", "max_connections", 300, "300"),
    ("number", "speed_per_slot", 20, "20"),
    ("number", "max_new_connections_per_turn", 20, "20"),
    ("number", "max_sources_per_file", 600, "600"),
]
failed = 0
for dom, name, value, expect in checks:
    eid = f"{dom}.applejuice_core{P}{name}"
    call(dom, "set_value", {"entity_id": eid, "value": value})
    got = state(eid)
    failed += got != expect
    print(f"{'OK  ' if got == expect else 'FAIL'} {name} {value} -> {got}")
sw = f"switch.applejuice_core{P}auto_connect"
for svc, expect in (("turn_off", "off"), ("turn_on", "on")):
    call("switch", svc, {"entity_id": sw})
    got = state(sw)
    failed += got != expect
    print(f"{'OK  ' if got == expect else 'FAIL'} auto_connect {svc} -> {got}")
tx = f"text.applejuice_core{P}nickname"
call("text", "set_value", {"entity_id": tx, "value": "test äö"})
got = state(tx)
failed += got != "test äö"
print(f"{'OK  ' if got == 'test äö' else 'FAIL'} nickname -> {got}")
call("button", "press", {"entity_id": f"button.applejuice_core{P}clean_download_list"})
print("OK   clean_download_list pressed")
print("sharecheck button:", any("share_check" in k for k in states))
sys.exit(1 if failed else 0)
