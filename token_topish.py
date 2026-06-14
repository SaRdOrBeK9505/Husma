"""
REAL initData logidan olingan data_check_string va hash bilan
qaysi bot token MOS kelishini topadi.

ISHLATISH:
  .venv\\Scripts\\python.exe token_topish.py
So'ralganda BotFather'dagi token(lar)ingizni bittadan kiriting.
Mos kelsa — aynan o'sha bot Mini App'ni ochishi kerak (yoki .env shu token).
"""
import hashlib
import hmac

# --- Logdan olingan REAL ma'lumot (oxirgi so'rov) ---
DATA_CHECK_STRING = (
    "auth_date=1781459313\n"
    "query_id=AAEloZt7AgAAACWhm3vptfA2\n"
    'user={"id":6368764197,"first_name":"O\u2019tkirbek",'
    '"last_name":"Abdumajidov","username":"frontend_00",'
    '"language_code":"ru","allows_write_to_pm":true,'
    '"photo_url":"https:\\/\\/t.me\\/i\\/userpic\\/320\\/'
    'bLU35WYFC-PjGdaw1kFSpOIsaTh5ZNvSUy0jI7AjbO5nrKNq7JHvqotfzEX_arMb.svg"}'
)
KUTILGAN_HASH = "2b3feb18d86b8778be4ab84cc458cbf9d2ae77c9e3e2f654c1e12549f11cd725"


def tekshir(token: str) -> bool:
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, DATA_CHECK_STRING.encode(), hashlib.sha256).hexdigest()
    print(f"  Token oxiri ...{token[-6:]} -> {calc}")
    return calc == KUTILGAN_HASH


if __name__ == "__main__":
    print("Kutilgan hash:", KUTILGAN_HASH)
    print("\nBotFather token(lar)ini kiriting. Tugatish uchun bo'sh qoldiring.\n")
    while True:
        t = input("Token: ").strip()
        if not t:
            break
        if tekshir(t):
            print("\n  ✅ MOS KELDI! Aynan SHU bot Mini App'ni ochmoqda.")
            print("  Shu tokenni .env dagi TELEGRAM_BOT_TOKEN ga qo'ying.\n")
        else:
            print("  ❌ Mos emas. Bu bot Mini App'ni ochmagan.\n")
