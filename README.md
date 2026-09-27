# Mini CRM

Internship topshirig‘i uchun sodda Django + Django REST Framework + SQLite ilovasi.
Login, lead CRUD, status almashish, qidiruv, status filtri va pagination mavjud.
Interfeys o‘zbekcha, Django/DRF standart autentifikatsiya va ayrim maydon xatolari inglizcha.

## O‘rnatish va ishga tushirish

Python 3.10+ (bu muhitda Python 3.14 bilan tekshirildi).
Loyiha papkasida:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/setup_env.py
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Ilova: http://127.0.0.1:8000/
- Login: http://127.0.0.1:8000/accounts/login/
- Admin: http://127.0.0.1:8000/admin/
- Ko‘rish va sinash mumkin bo‘lgan API: http://127.0.0.1:8000/api/

Yaratgan admin login/parolingiz bilan veb ilovaga ham kirasiz. Tayyor yoki umumiy parol yo‘q.
Oddiy foydalanuvchini admin orqali yarating. Barcha tizimga kirgan foydalanuvchilar
bir xil leadlar bazasini ko‘radi va tahrirlaydi. Ro‘yxatdan o‘tish va tenant/owner rollari bu topshiriq doirasiga kirmaydi.

`setup_env.py` tasodifiy kalit bilan `.env` yaratadi; mavjud faylni o‘zgartirmaydi.
`.env.example` faqat sozlama nomlarini ko‘rsatadi. `.env` avtomatik yuklanadi;
terminaldagi environment qiymatlari undan ustun. Kalit bo‘lmasa ilova aniq xato bilan to‘xtaydi.
Mahalliy ishlab chiqishda `DJANGO_DEBUG=True`. Ommaviy serverda `False`, aniq
`DJANGO_ALLOWED_HOSTS`, HTTPS va production WSGI/ASGI server kerak; `runserver` development uchun.

## Arxitektura va data model

```text
config/                 settings va umumiy URL marshrutlari
leads/models.py         Lead, kontakt validatsiyasi, DB cheklovlari
leads/forms.py          veb formalar
leads/views.py          login bilan himoyalangan Django view funksiyalari
leads/serializers.py    API maydonlari va kontakt validatsiyasi
leads/api.py            DRF ModelViewSet, qidiruv va status filtri
leads/migrations/       versiyalangan DB sxemasi
leads/tests.py          17 ta avtomatik test
templates/             serverda render qilinadigan HTML
static/app.css          moslashuvchan interfeys; tashqi CDN talab qilmaydi
scripts/                .env tayyorlash va ixtiyoriy brauzer tekshiruvi
```

| Maydon | Turi / qoida |
|---|---|
| id | Avtomatik primary key |
| name | Majburiy, 150 belgigacha |
| phone | 30 belgigacha, bo‘sh bo‘lishi mumkin |
| email | Email formatida, bo‘sh bo‘lishi mumkin |
| source | Erkin matn, 100 belgigacha |
| note | Ixtiyoriy matn |
| status | New (default), Contacted, Qualified, Won, Lost |
| created_at | Avtomatik yaratilish vaqti |
| updated_at | Avtomatik oxirgi saqlash vaqti |

Telefon yoki emaildan kamida bittasi kerak. Telefon xalqaro formatlar uchun erkin
matn bo‘lib, maxsus mamlakat regexi qo‘llanmagan. Kontaktlar unique emas.
Veb ModelForm va API serializer umumiy `validate_contact` funksiyasidan foydalanadi.
PATCH mavjud qiymatlarni ham hisobga oladi: oxirgi kontaktni o‘chirish mumkin emas.
DB check constraint bo‘sh kontakt juftligi va noto‘g‘ri statusni bloklaydi.
To‘g‘ridan-to‘g‘ri ORM `save()` `full_clean()` chaqirmaydi; maxsus import yozilganda
avval `full_clean()` ishlating (masalan, faqat probeldan iborat matn uchun).

Bitta `leads` ilovasi yetarli: keraksiz service/repository qatlamlari yo‘q.
Django template/formlari frontend build va JavaScript framework talab qilmaydi.
DRF ModelViewSet standart CRUD beradi. SQLite lokal topshiriqni server bazasisiz
ishga tushirishni soddalashtiradi. Status filtri bitta maydon uchun qo‘lda yozilgan;
qo‘shimcha filter paketi kerak emas. Yangi leadlar avval, teng vaqt bo‘lsa ID bo‘yicha
saralanadi. Har sahifa 10 yozuv. Vaqtlar Asia/Tashkent bo‘yicha ko‘rsatiladi.

## API

Barcha lead endpointlari authentication talab qiladi. Veb uchun Django session
va CSRF; API uchun `Authorization: Token ...` yoki session ishlatiladi.
Session orqali yozuvchi so‘rovlarga CSRF token ham kerak. Token parol kabi maxfiy;
HTTPS orqali uzating. Token muddati avtomatik tugamaydi; zaruratda Django admin
Tokens bo‘limidan o‘chiring. Veb logout sessionni tugatadi, API tokenni bekor qilmaydi.
Token olish endpointida 10/min IP throttling bor (lokal cache; production brute-force himoyasi o‘rnini bosmaydi).

| Method | Endpoint | Amal |
|---|---|---|
| POST | `/api/auth/token/` | Login/parol orqali token olish |
| GET | `/api/leads/` | Ro‘yxat |
| POST | `/api/leads/` | Yaratish |
| GET | `/api/leads/{id}/` | Tafsilot |
| PUT | `/api/leads/{id}/` | Tahrirlash; name va kontakt yuboring |
| PATCH | `/api/leads/{id}/` | Qisman tahrirlash yoki status almashtirish |
| DELETE | `/api/leads/{id}/` | O‘chirish |

Token olish (`YOUR_PASSWORD` o‘rniga o‘z parolingizni yozing):

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"YOUR_PASSWORD"}'
```

Javobdagi tokenni shell o‘zgaruvchisiga kiriting:

```bash
read -rs -p 'API token: ' TOKEN
export TOKEN

curl -X POST http://127.0.0.1:8000/api/leads/ \
  -H "Authorization: Token $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Ali Valiyev","phone":"+998901234567","source":"Telegram","note":"Demo lead","status":"New"}'

curl -H "Authorization: Token $TOKEN" \
  'http://127.0.0.1:8000/api/leads/?search=Ali&status=New&page=1'

# 1 o‘rniga yaratilgan lead id sini qo‘ying.
curl -H "Authorization: Token $TOKEN" http://127.0.0.1:8000/api/leads/1/

curl -X PUT http://127.0.0.1:8000/api/leads/1/ \
  -H "Authorization: Token $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Ali Valiyev","phone":"+998901234567","email":"ali@example.com","source":"Website","note":"Qayta bog‘lanish","status":"Contacted"}'

curl -X PATCH http://127.0.0.1:8000/api/leads/1/ \
  -H "Authorization: Token $TOKEN" -H 'Content-Type: application/json' \
  -d '{"status":"Won"}'

curl -X DELETE -H "Authorization: Token $TOKEN" http://127.0.0.1:8000/api/leads/1/
unset TOKEN
```

`search` ism, telefon, email va manbadan qidiradi. API DRF SearchFilter ko‘p so‘zli
qidiruv qoidalaridan foydalanadi; veb qidiruv to‘liq matn bo‘lagini qidiradi.
`status` qiymati registrga sezgir. `page` 1 dan boshlanadi.
Ro‘yxat shakli: `{"count": 12, "next": "...page=2", "previous": null, "results": [...]}`.

Xatolar HTTP statusi va JSON tanasi bilan qaytadi:

- `400`: maydon xatolari, masalan `{"email":["Enter a valid email address."]}`.
- `400`: kontaktsiz lead — `{"non_field_errors":["Telefon yoki emaildan kamida bittasini kiriting."]}`.
- `400`: noto‘g‘ri status filtri yoki login/parol.
- `401`: lead API uchun authentication yo‘q yoki token noto‘g‘ri.
- `403`: session so‘rovida CSRF tekshiruvi o‘tmadi.
- `404`: lead topilmadi (`detail` xabari) yoki API sahifa raqami mavjud emas.
- `429`: token olish so‘rovlari limiti oshdi.

Vebda xatolar formaning yonida ko‘rsatiladi, noto‘g‘ri pagination birinchi/oxirgi
sahifaga olib boradi. Maxsus tushunarli 404 sahifa `DEBUG=False` holatida ishlaydi.
O‘chirish va status o‘zgartirish faqat POST bilan, CSRF himoyasi ostida bajariladi.

## Tekshirish va natijalar

```bash
python manage.py test --verbosity 2
python manage.py check
python manage.py makemigrations --check --dry-run
```

17 test o‘tdi: login/logout, token/session authentication, barcha CRUD amallariga
ruxsatsiz kirishni rad etish, CSRF, API va veb CRUD, barcha statuslar, kontakt/email/
name validatsiyasi, PATCH kontakt holati, read-only vaqt, search/filter, pagination,
404, DB constraints va HTML escaping. `check`: 0 muammo; migratsiya tafovuti yo‘q.
Ishlayotgan serverda login HTTP 200 va anonymous API HTTP 401 tasdiqlandi.
Haqiqiy Chrome brauzerida login, yaratish, tahrirlash, status, search/filter,
o‘chirish va logout oqimi o‘tdi. Desktop (1440px) va mobil (390px) ko‘rinishlar
tekshirildi; sahifa overflow va JavaScript xatolari topilmadi.

Ixtiyoriy haqiqiy Chrome brauzer testi (server boshqa terminalda ishlasin):

```bash
python -m pip install playwright==1.63.0
python scripts/browser_smoke.py
```

Google Chrome o‘rnatilgan bo‘lishi kerak. Test vaqtinchalik user va lead yaratadi,
oxirida tozalaydi; faqat development bazada ishga tushiring. Skrinshotlar
`/tmp/minicrm-desktop.png` va `/tmp/minicrm-mobile.png` ichida saqlanadi.

## AI yordamidan foydalanish

Kod, UI, testlar va ushbu README AI (Codex) yordamida yaratildi. Natija faqat AI
bayonotiga tayanib qabul qilinmadi: migratsiyalar real SQLite bazada qo‘llandi,
17 avtomatik test va ishlayotgan serverga HTTP so‘rovlari bajarildi.
Bu foydalanuvchi kodning har bir qatorini mustaqil yozgan degan da’vo emas.
Suhbatga tayyorlanishda model → form/serializer → view → URL → template oqimini,
PATCH validatsiyasi va session/token farqini tushuntirish tavsiya qilinadi.

## Git va GitHub

`.env`, `.env.*`, SQLite fayllari, virtual environment va IDE fayllari `.gitignore`da.
`.env.example` maxfiy qiymatsiz commit qilinadi. Yuborishdan avval:

```bash
git status --short
git ls-files .env db.sqlite3
git check-ignore .env db.sqlite3
git log --oneline
```

Ikkinchi buyruq hech narsa chiqarmasligi kerak. Ushbu muhitda GitHub CLI (`gh`)
va sozlangan remote yo‘q; public repository yaratilmagan, URL berilmagan.
GitHub CLI o‘rnatilgan o‘z terminalingizda, loyiha papkasida:

```bash
gh auth login
gh repo create mini-crm --public --source=. --remote=origin --push
gh repo view --json url --jq .url
```

Agar `mini-crm` nomi band bo‘lsa, boshqa nom tanlang. Oxirgi buyruq haqiqiy URLni
chiqaradi. Muqobil: GitHub saytida bo‘sh public repository yarating (README qo‘shmang),
so‘ng saytdagi haqiqiy URL bilan:

```bash
git remote add origin https://github.com/YOUR_USERNAME/mini-crm.git
git push -u origin main
```

Yuqoridagi URL shablon, mavjud repository haqidagi da’vo emas. Ariza yuborilmagan.

Rasmiy manbalar: [Django 5.2](https://docs.djangoproject.com/en/5.2/),
[DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/),
[DRF pagination](https://www.django-rest-framework.org/api-guide/pagination/).
