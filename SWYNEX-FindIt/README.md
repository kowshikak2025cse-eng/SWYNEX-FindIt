# FindIt – Smart Lost & Found Portal

A responsive public lost-and-found web application built with **Flask, SQLAlchemy, and MySQL-compatible database configuration**. For a zero-configuration local demo it uses SQLite; switch `DATABASE_URL` to MySQL when ready.

## Features
- User registration, login and logout
- Create LOST and FOUND reports with optional image upload
- Search reports by keyword, type, category and location
- Public item details with privacy-conscious location text
- Private ownership claims on found-item reports
- User dashboard for reports, sent claims and received claims
- Claim review, mark item returned, flag suspicious listings
- Admin moderation dashboard
- JSON endpoint: `GET /api/v1/items`

## Quick start (Windows)
1. Install Python 3.10 or newer.
2. Extract the ZIP and open the `SWYNEX-FindIt` folder in VS Code.
3. Open Terminal and run:

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

4. Open `http://127.0.0.1:5000`.

For macOS/Linux activate with `source .venv/bin/activate`.

## Demo administrator
- Email: `admin@findit.local`
- Password: `Admin@12345`

**Change these credentials in `.env` before sharing or deploying.** The demo admin is created automatically when the database has no admin account.

## Use MySQL
1. Create a database, for example `findit_db`.
2. Install/start MySQL and create a database user with access to it.
3. Edit `.env`:

```env
DATABASE_URL=mysql+pymysql://findit_user:your_password@localhost/findit_db?charset=utf8mb4
```

4. Run `python app.py`. SQLAlchemy creates the initial tables automatically.

## Main routes
| Route | Purpose |
|---|---|
| `/` | Landing page and latest reports |
| `/register`, `/login`, `/logout` | Authentication |
| `/items` | Search and browse reports |
| `/items/<id>` | Item details and claim form |
| `/report` | Create LOST/FOUND report |
| `/dashboard` | My reports and claims |
| `/admin` | Admin moderation |
| `/api/v1/items` | JSON list of open reports |

## Project structure
```text
SWYNEX-FindIt/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── templates/
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── uploads/
└── docs/
    └── project-architecture.md
```

## Important safety and privacy notes
- Do not put phone numbers, identity numbers, serial numbers or exact home addresses in public descriptions.
- Claim proof is private and visible only to the claimant, the report owner and an administrator.
- Arrange handovers in safe public places. Do not share passwords or one-time codes.
- This is an internship starter/MVP. Before public deployment add CSRF protection, email verification, rate limiting, production logging, database migrations, secure cookie settings, malware scanning for uploads, backups and a production-grade secret key.

## Architecture
Browser UI → Flask routes/business logic → SQLAlchemy → SQLite (local) or MySQL (configured); uploaded images are stored under `static/uploads/` for the demo.

## License
Educational internship project starter. Add a license if you plan to publish or reuse it.
