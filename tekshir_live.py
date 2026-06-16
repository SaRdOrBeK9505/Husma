import json
from urllib import request as u, error as e

INIT = "query_id=AAF08F1JAwAAAHTwXUl_aBHA&user=%7B%22id%22%3A7673344116%2C%22first_name%22%3A%22Javohir%20Azamov%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22javohirazam0v%22%2C%22language_code%22%3A%22ru%22%2C%22is_premium%22%3Atrue%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FmxOX8CnWz2mY2aq9gVKsFUhanlVYdbgcgPDKIes9yazmRJqMehQ22GXAm41U6j7U.svg%22%7D&auth_date=1781595198&signature=eVvGdIhtoEyNj_WvOnI-0QOLNoOGI7GQV_Jh0E7bSiyC1M7cTKW5Bga4LJqG4M7RHTTM0Cu0wDCKcMWlds6cDg&hash=cc45053126cd97e3d5260a950d35574e19d315772e4db27fdfcd817077dfdb76"

req = u.Request("http://127.0.0.1:8000/api/auth/telegram/",
                data=json.dumps({"init_data": INIT}).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
try:
    r = u.urlopen(req, timeout=10)
    print("STATUS:", r.status)
    print(r.read().decode())
except e.HTTPError as ex:
    print("STATUS:", ex.code, ex.read().decode())
