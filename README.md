# FinoPal Python SDK

کیت توسعه‌ی پایتون برای **درگاه پرداخت اینترنتی فینوپال** — نوشته‌شده بر اساس
[مستندات رسمی فینوپال](https://finopal.ir/docs).

معماری این SDK از [Zarinpal Python SDK](https://github.com/ZarinPal/Zarinpal-Python-Sdk)
الگو گرفته است (یک کلاینت، منابع تنبل‌ساز، متدهای `create` / `verify` / `inquire` /
`reverse` / `calculate`) اما API آن دقیقاً همان چیزی است که فینوپال ارائه می‌دهد و
با SDK موجود PHP در افزونه‌ی ووکامرس همین پروژه (`finopay-plugins/finopal-woocommerce`)
هم‌خوان است.

```bash
pip install finopal-py-sdk
```

تا زمان انتشار روی PyPI، بسته را از همین پوشه نصب کنید:

```bash
pip install .
```

---

## فهرست

- [نصب](#نصب)
- [شروع سریع](#شروع-سریع)
- [جریان کامل پرداخت](#جریان-کامل-پرداخت)
- [منابع API](#منابع-api)
- [حالت Sandbox](#حالت-sandbox)
- [تبدیل مبلغ (تومان ↔ ریال)](#تبدیل-مبلغ-تومان--ریال)
- [مدیریت خطا](#مدیریت-خطا)
- [کدهای خطا](#کدهای-خطا)
- [تست‌ها](#تست‌ها)
- [ساختار پروژه](#ساختار-پروژه)
- [English summary](#english-summary)

---

## نصب

نیازمندی: **Python 3.9+** و `pip`. وابستگی زمان اجرا بسته‌ی `requests` است.

```bash
pip install finopal-py-sdk
```

یا:

```bash
pip3 install finopal-py-sdk
```

تا زمان انتشار روی PyPI:

```bash
pip install .
# حالت توسعه، همراه با تست‌ها
pip install -e ".[dev]"
```

برای اجرای مثال Flask:

```bash
pip install ".[flask]"
```

---

## شروع سریع

```python
from finopal import FinoPal, Config

finopal = FinoPal(Config(
    merchant_id="fino-xxxx-xxxx-xxxx-xxxx",  # از پنل کاربری فینوپال
    sandbox=True,                            # برای محیط آزمایشی
))

payment = finopal.payments.create({
    "amount": 1_100,                                       # مبلغ به ریال
    "callback_url": "https://shop.example.com/payment/callback",
    "order_id": "ORD-1001",
    "description": "خرید شماره ۱۰۰۱",
})

print(payment.authority)    # FP_636E4A5CBBCE0F222B46829BD74AB4A9
print(payment.payment_url)  # کاربر را به این آدرس هدایت کنید
```

هر پاسخ، هم‌زمان با دسترسی دیکشنری و هم با دسترسی ویژگی قابل استفاده است و
پیلود خام گیت‌وی همیشه در `raw` نگه داشته می‌شود:

```python
payment.authority      # → "FP_636E..."
payment["authority"]   # → "FP_636E..."
payment.raw            # → {"success": True, "code": 100, "data": {...}}
payment.is_successful  # → True
```

---

## جریان کامل پرداخت

```
  ┌──────────┐   1. request    ┌────────────┐
  │  سایت شما │ ───────────────▶│  فینوپال   │
  └──────────┘  authority +     └────────────┘
       │        payment_url           │
       │  2. هدایت کاربر (302)        │
       └─────────────────────────────▶│  صفحه پرداخت
                                      │
  ┌──────────┐  3. callback    ┌──────┴─────┐
  │  سایت شما │ ◀───────────────│  فینوپال   │
  └──────────┘  ?Authority=..   └────────────┘
       │        &Status=OK
       │  4. verify (فقط اگر Status=OK باشد)
       └─────────────────────────────▶ ref_id
```

### ۱) ساخت درخواست پرداخت

```python
payment = finopal.payments.create({
    "amount": 120_000,          # ریال — الزامی
    "callback_url": "...",      # الزامی، باید با دامنه‌ی ثبت‌شده یکی باشد
    "order_id": "ORD-1001",     # الزامی
    "description": "...",       # الزامی، حداکثر ۲۵۵ کاراکتر
    "mobile": "09121234567",    # اختیاری
    "email": "a@b.com",         # اختیاری
    "metadata": {"user_id": "960", "product_id": "123"},
})

redirect(payment.payment_url)   # کاربر را هدایت کنید
```

میان‌بر با آرگومان‌های کلیدواژه‌ای:

```python
payment = finopal.payments.request(
    amount=120_000,
    callback_url="https://shop.example.com/callback",
    order_id="ORD-1001",
)
```

### ۲) بازگشت کاربر و تأیید (verify)

فینوپال کاربر را با کوئری‌استرینگ برمی‌گرداند. قالب پارامترها در محیط واقعی و
آزمایشی متفاوت است و `parse_callback` هر دو را یکسان می‌کند:

| محیط | کوئری‌استرینگ | نشانه‌ی موفقیت |
|---|---|---|
| واقعی | `?Authority=...&Status=OK` | `Status=OK` |
| آزمایشی | `?authority=...&status=0&sandbox=1` | `status=0` |

```python
from finopal import parse_callback

cb = parse_callback(request.args)

if not cb.is_success:
    return render_template("payment_failed.html")

result = finopal.verifications.verify({
    "authority": cb.authority,
    "amount": order.amount_rial,   # دقیقاً همان مبلغ مرحله‌ی اول
})

print(result.ref_id)               # شماره تراکنش برای نمایش به کاربر
```

> **مهم:** متد `verify` را فقط زمانی صدا بزنید که `Status=OK` (یا در سندباکس
> `status=0`) باشد. کد `100` یعنی «تازه تأیید شد» و کد `101` یعنی «قبلاً تأیید
> شده بود» — **هر دو یعنی پرداخت موفق است**.

### ۳) استعلام (اختیاری ولی توصیه‌شده)

اگر `verify` با خطای شبکه برگشت، **هرگز** دوباره درخواست پرداخت نسازید؛ وضعیت
واقعی را استعلام کنید:

```python
status = finopal.inquiries.inquire({"authority": cb.authority})
print(status.status)   # pending | successful | failed | cancelled | refunded | callback
print(status.is_paid)  # True فقط وقتی status == "successful"
```

### ۴) ریورس (لغو تراکنش تأییدشده)

```python
finopal.reversals.reverse({"authority": "FP_636E4A5C..."})
```

- فقط روی تراکنش **verify‌شده** و در بازه‌ی کوتاه (۱۵ دقیقه بر اساس مستندات) کار می‌کند.
- بعد از موفقیت، وضعیت تراکنش `refunded` می‌شود و تکرار درخواست خطای `-1551` می‌دهد.
- انقضای مهلت → خطای `-1552`.

### ۵) محاسبه کارمزد (قبل از پرداخت)

```python
fee = finopal.fees.calculate({"amount": 1_000_000})
print(fee.fee, fee.fee_type)      # 20000 Merchant
print(fee.is_paid_by_customer)    # False → کارمزد روی پذیرنده است
```

---

## منابع API

| منبع | متدها | اندپوینت |
|---|---|---|
| `finopal.payments` | `create()` / `request()` / `redirect_url()` | `POST /api/v1/payment/request` |
| `finopal.verifications` | `verify()` / `verify_authority()` / `is_verified()` | `POST /api/v1/payment/verify` |
| `finopal.inquiries` | `inquire()` / `status_of()` | `POST /api/v1/payment/inquiry` |
| `finopal.reversals` | `reverse()` / `reverse_authority()` | `POST /api/v1/payment/reverse` |
| `finopal.fees` | `calculate()` / `calculate_amount()` | `POST /api/v1/payment/feeCalculation` |

اندپوینت جدیدی که هنوز پوشش داده نشده است:

```python
finopal.request("POST", "/api/v1/payment/anything", {"foo": "bar"})
```

---

## حالت Sandbox

```python
Config(merchant_id="...", sandbox=True)     # → https://sandbox.finopal.ir
Config(merchant_id="...")                   # → https://payment.finopal.ir
Config(merchant_id="...", base_url="http://localhost:8000")  # میزبان دلخواه
```

ساختار API در سندباکس یکسان است؛ فقط مقصد نهایی بانک شبیه‌سازی می‌شود. در صفحه‌ی
آزمایشی می‌توانید نتیجه را انتخاب کنید:

| دکمه | نتیجه در Callback |
|---|---|
| پرداخت موفق | `Status=0` / `status=OK` |
| پرداخت ناموفق | `Status=-1` / `status=NOK` |
| انصراف | `status=-138` |

مدت اعتبار نشست سندباکس ۱۰ دقیقه است.

---

## تبدیل مبلغ (تومان ↔ ریال)

فینوپال همه‌ی مبلغ‌ها را **ریال و به‌صورت عدد صحیح** می‌پذیرد. برای جلوگیری از
اشتباه ضریب ده، از این توابع استفاده کنید:

```python
from finopal import to_rial, to_toman

to_rial(12_000, "TOMAN")   # → 120000
to_rial(5, "IRHT")         # → 50000   (هزار تومان)
to_rial(1_100)             # → 1100    (پیش‌فرض ریال)
to_toman(120_000)          # → 12000.0
```

مبالغ مجاز: حداقل `1,000` ریال و حداکثر `1,000,000,000` ریال (۱۰۰ میلیون تومان).

---

## مدیریت خطا

```python
from finopal import FinoPalError, FinoPalException, ValidationError, TransportError

try:
    result = finopal.verifications.verify({"authority": authority, "amount": amount})
except ValidationError as exc:
    # ورودی نامعتبر — هیچ درخواستی به گیت‌وی ارسال نشده است
    ...
except FinoPalException as exc:
    # گیت‌وی پاسخ success=false یا کد غیر ۱۰۰ داده است
    print(exc.code, exc.message, exc.describe(), exc.scope)
except TransportError as exc:
    # خطای شبکه / پاسخ غیر JSON / خطای 5xx — نتیجه نامعلوم است
    # → قبل از هر تصمیمی استعلام بگیرید
    print(exc.status_code, exc.message)
```

| کلاس | معنا |
|---|---|
| `ValidationError` | اعتبارسنجی سمت کلاینت؛ درخواستی ارسال نشده است |
| `FinoPalException` | گیت‌وی درخواست را رد کرده؛ دارای `code` و `message` |
| `TransportError` | عدم دسترسی به گیت‌وی یا پاسخ نامعتبر؛ دارای `status_code` |

`describe()` توضیح انگلیسی کد خطا را از فهرست رسمی برمی‌گرداند و `scope` مشخص
می‌کند کد مربوط به کدام بخش API است (`PaymentRequest`، `PaymentVerify`، ...).

---

## کدهای خطا

فهرست کامل در `src/finopal/utils/error_codes.py` قرار دارد. مهم‌ترین‌ها:

| کد | توضیح |
|---|---|
| `100` | عملیات موفق |
| `101` | تراکنش قبلاً تأیید شده است (پرداخت موفق است) |
| `-9` | خطای اعتبارسنجی (مرچنت‌کد، callback، توضیحات، مبلغ) |
| `-10` | مرچنت‌کد یا آی‌پی پذیرنده صحیح نیست |
| `-11` | مرچنت‌کد فعال نیست / تراکنش یافت نشد |
| `-13` | محدودیت تراکنش ترمینال |
| `-14` | دامنه‌ی callback با دامنه‌ی ثبت‌شده مغایرت دارد |
| `-15` | درگاه در حالت تعلیق |
| `-16` / `-17` | سطح تأیید پذیرنده نامعتبر / محدودیت سطح آبی |
| `-18` | عدم تطابق آدرس referrer با دامنه‌ی ثبت‌شده |
| `-19` | ایجاد تراکنش برای این ترمینال مجاز نیست |
| `-30` … `-41` | خطاهای ساخت درخواست پرداخت (تسهیم، کارمزد، سقف مبلغ) |
| `-50` | مبلغ وریفای با مبلغ پرداخت‌شده یکسان نیست |
| `-51` | پرداخت ناموفق / نشست فعال نیست |
| `-53` | پرداخت متعلق به این مرچنت‌کد نیست |
| `-54` | authority نامعتبر |
| `-55` | تراکنش مورد نظر یافت نشد |
| `-60` … `-63` | خطاهای ریورس |
| `-1551` | تراکنش قبلاً برگشت داده شده است |
| `-1552` | تراکنش verify نشده یا مهلت ریورس تمام شده است |

---

## تست‌ها

```bash
pip install -e ".[dev]"
pytest
```

مجموعه‌ی تست آفلاین و قطعی است: کلاس `FakeGateway` (در `tests/conftest.py`) نقش
گیت‌وی را بازی می‌کند و لایه‌ی HTTP واقعی هم با `requests_mock` تست می‌شود.

---

## ساختار پروژه

```
finopal-python-sdk/
├── src/finopal/
│   ├── __init__.py            # API عمومی
│   ├── finopal.py             # کلاس FinoPal (ورودی اصلی)
│   ├── models.py              # پاسخ‌های نرمال‌شده (ApiResponse و ...)
│   ├── errors/exceptions.py   # سلسله‌مراتب خطاها
│   ├── http/
│   │   ├── transport.py       # Transport، RequestsTransport، CallableTransport
│   │   └── client.py          # HttpClient
│   ├── resources/             # payments, verifications, inquiries, reversals, fees
│   └── utils/                 # config, validator, amount, callback, error_codes, enums
├── examples/                  # ۶ مثال قابل اجرا (شامل جریان کامل Flask)
└── tests/                     # pytest + FakeGateway
```

---

## English summary

A Python SDK for the [FinoPal](https://finopal.ir/docs) online payment gateway,
modelled on the ZarinPal Python SDK and consistent with the FinoPal WooCommerce
plugin already in this repository.

```python
from finopal import FinoPal, Config, parse_callback, to_rial

finopal = FinoPal(Config(merchant_id="fino-xxxx-xxxx-xxxx-xxxx", sandbox=True))

payment = finopal.payments.create({
    "amount": to_rial(12_000, "TOMAN"),
    "callback_url": "https://shop.example.com/callback",
    "order_id": "ORD-1001",
})
# -> redirect the buyer to payment.payment_url

cb = parse_callback(request.args)
if cb.is_success:
    result = finopal.verifications.verify({
        "authority": cb.authority,
        "amount": 120_000,
    })
    print(result.ref_id)
```

**Coverage:** `request`, `verify`, `inquiry`, `reverse`, `feeCalculation`.
**Extras:** Rial/Toman conversion, live+sandbox callback normalisation, the full
published error catalogue, pluggable transports, and a fully offline test suite.

---

## مجوز

MIT — see [LICENSE](LICENSE).
