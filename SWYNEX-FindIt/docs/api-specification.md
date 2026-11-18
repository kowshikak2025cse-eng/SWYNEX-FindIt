# API outline

Base URL: `/api/v1`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/items` | JSON list of open reports (implemented) |

The browser MVP uses Flask form routes for registration, reports, claims and moderation. Extend these into JSON endpoints if a separate SPA/mobile client is added.
