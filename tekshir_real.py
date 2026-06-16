import hashlib, hmac
from urllib.parse import parse_qsl

INIT = "query_id=AAGp_w9HAwAAAKn_D0cengDC&user=%7B%22id%22%3A7634681769%2C%22first_name%22%3A%22Sardorbek%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22sardorbek_9505%22%2C%22language_code%22%3A%22uz%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FLtVyaiFrofKad660TOT1-ex0NlF7uHebZqzHy97vaxee7QX8cRLD6whear0EbuC6.svg%22%7D&auth_date=1781590625&signature=cXcfbqMLH-upz6e6wEC3Y2rkvkzSZdFlwz3rvHU-fwsluxCpmgIj34_mdmJYP6DT2pKoi_5GS34L-QtnVwJ2CA&hash=29e84bd420da35d59447d4590a687ac7d45cd24268d2655aae2bbd5c5de59eb6"

TOKEN = "8973148764:AAHRFJ4JTexGglSV5IsGasaVdJBMo0K--sA"  # @Husmas_bot

parsed = dict(parse_qsl(INIT, strict_parsing=False))
received = parsed.pop("hash")

print("Kelgan hash:", received)
print("Kalitlar:", list(parsed.keys()))
print()

# Variant 1: signature OLIB TASHLANADI (joriy kodingiz)
p1 = {k: v for k, v in parsed.items() if k != "signature"}
dcs1 = "\n".join(f"{k}={v}" for k, v in sorted(p1.items()))
secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
calc1 = hmac.new(secret, dcs1.encode(), hashlib.sha256).hexdigest()
print("VARIANT 1 — signature olib tashlangan:")
print("  data_check_string:")
print("   ", repr(dcs1))
print("  mos:", calc1 == received, calc1)
print()

# Variant 2: signature QOLDIRILADI (data_check_string da)
dcs2 = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
calc2 = hmac.new(secret, dcs2.encode(), hashlib.sha256).hexdigest()
print("VARIANT 2 — signature qoldirilgan:")
print("  mos:", calc2 == received, calc2)
print()

# Variant 3: faqat hash olib tashlanadi (signature qoladi) — variant 2 bilan bir xil
# Variant 4: query_id ham olib tashlanadi
p4 = {k: v for k, v in parsed.items() if k not in ("signature", "query_id")}
dcs4 = "\n".join(f"{k}={v}" for k, v in sorted(p4.items()))
calc4 = hmac.new(secret, dcs4.encode(), hashlib.sha256).hexdigest()
print("VARIANT 4 — signature va query_id olib tashlangan:")
print("  mos:", calc4 == received, calc4)
