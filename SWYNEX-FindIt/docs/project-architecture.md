# FindIt – Project Architecture (Starter)

## Goal
A public platform for reporting lost/found belongings, searching listings and safely processing ownership claims.

## Stack
- Frontend: HTML, CSS, JavaScript, Jinja templates
- Backend: Python Flask
- ORM/database: Flask-SQLAlchemy; SQLite for local setup, MySQL supported through `DATABASE_URL`
- Image uploads: local development folder (use private/object storage for production)

## Main entities
- User: identity, unique email, password hash and role
- Item: reporter, LOST/FOUND type, category, description, approximate location, date, image and status
- Claim: claimant, found item, private proof and review status
- Flag: report moderation request

## Main workflow
1. User registers or signs in.
2. User submits a LOST or FOUND report.
3. Public visitors search and filter open reports.
4. A signed-in user submits a private claim on a FOUND report.
5. The finder reviews the claim; accepted claims can proceed to a safe handover.
6. Owner closes the report as returned.
7. Admin reviews flags and hides inappropriate listings.

## API
- `GET /api/v1/items` – list open items as JSON
- HTML form routes are implemented for the full MVP user journey.

## Production additions
CSRF protection, email verification, migrations, rate limiting, secure cookie settings, object storage, malware scanning, backups, logging and monitoring.
