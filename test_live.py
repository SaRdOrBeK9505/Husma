"""Local server'ga real imzolangan initData yuborib /auth/telegram/ ni sinaydi."""
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import hashlib, hmac, json, time
from urllib.parse import urlencode
from urllib import request as urlrequest
from django.conf import settings

token = settings.TELEGRAM_BOT_TOKEN
user = {"id": 123456789, "first_name": "Ali", "last_name": "Valiyev", "username": "ali_uz"}
fields = {"user": json.dumps(user, separators=(",", ":")), "auth_date": str(int(time.time()))}
dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
fields["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
init_data = urlencode(fields)

body = json.dumps({"init_data": init_data}).encode()
req = urlrequest.Request(
    "http://127.0.0.1:8000/api/auth/telegram/",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    with urlrequest.urlopen(req, timeout=10) as resp:
        print("STATUS:", resp.status)
        print(resp.read().decode())
except Exception as e:
    print("XATO:", e)
    if hasattr(e, "read"):
        print(e.read().decode())
