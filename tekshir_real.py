import hashlib, hmac
from urllib.parse import parse_qsl

INIT = "query_id=AAF08F1JAwAAAHTwXUl_aBHA&user=%7B%22id%22%3A7673344116%2C%22first_name%22%3A%22Javohir%20Azamov%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22javohirazam0v%22%2C%22language_code%22%3A%22ru%22%2C%22is_premium%22%3Atrue%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FmxOX8CnWz2mY2aq9gVKsFUhanlVYdbgcgPDKIes9yazmRJqMehQ22GXAm41U6j7U.svg%22%7D&auth_date=1781595198&signature=eVvGdIhtoEyNj_WvOnI-0QOLNoOGI7GQV_Jh0E7bSiyC1M7cTKW5Bga4LJqG4M7RHTTM0Cu0wDCKcMWlds6cDg&hash=cc45053126cd97e3d5260a950d35574e19d315772e4db27fdfcd817077dfdb76"

TOKEN = "8973148764:AAHRFJ4JTexGglSV5IsGasaVdJBMo0K--sA"  # @Husmas_bot

parsed = dict(parse_qsl(INIT, strict_parsing=False))
received = parsed.pop("hash")
secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()

p1 = {k: v for k, v in parsed.items() if k != "signature"}
dcs1 = "\n".join(f"{k}={v}" for k, v in sorted(p1.items()))
calc1 = hmac.new(secret, dcs1.encode(), hashlib.sha256).hexdigest()

dcs2 = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
calc2 = hmac.new(secret, dcs2.encode(), hashlib.sha256).hexdigest()

print("Kelgan hash:", received)
print("Variant 1 (signaturesiz):", "MOS" if calc1 == received else "mos emas")
print("Variant 2 (signature bilan):", "MOS" if calc2 == received else "mos emas")
