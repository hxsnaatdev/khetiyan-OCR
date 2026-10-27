# Runtime Flow

This document explains how a request moves through the Khetiyan backend, how
the main land-record workflows behave, and how the API maps onto the database.
Design rationale is in [decisions.md](decisions.md).

## 1. System at a glance

```
Browser / mobile client / Swagger UI
              |
              |  HTTP + JSON, Bearer JWT
              v
        FastAPI application
   main.py -> routers -> deps.py
              |            |
              |            +-- JWT decode, role checks, 404/DB error helpers
              v
        Pydantic schemas
              |
              v
     SQLAlchemy Session
              |  PyMySQL, utf8mb4
              v
     MySQL 8 database
   tables + triggers + views
```

The API does not create tables at startup. The schema is loaded once from
`db/schema.sql`.

## 2. Startup and configuration

1. `backend/app/config.py` loads `backend/.env` through `pydantic-settings`.
   Settings: `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`,
   `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`.
2. `backend/app/database.py` creates the SQLAlchemy engine and a session factory.
   `get_db()` yields one session per request and always closes it.
3. `backend/app/main.py` registers the CORS middleware and includes every router.
4. `GET /api/health` executes `SELECT 1` to prove the database connection works.

Because `.env` is resolved relative to the current working directory, run
`uvicorn` from the `backend/` directory (or set the environment variables
explicitly).

## 3. Request lifecycle

For a typical protected write request:

```
POST /api/mutations/{id}/approve
  |
  | 1. CORS middleware
  | 2. route match -> mutations.approve_mutation
  | 3. dependency: get_db() opens Session
  | 4. dependency: get_current_user()
  |       decode JWT -> load app_user from MySQL -> reject inactive users
  | 5. dependency: require_roles(admin, tehsildar)
  | 6. Pydantic validates path/query/body
  | 7. handler runs SQLAlchemy statements
  | 8. commit or rollback
  | 9. response_model serializes ORM/row data to JSON
  | 10. get_db() finally closes the Session
  v
JSON response
```

Notes:

- The session uses `autoflush=False`. Flushes are explicit where ordering
  matters (the mutation approval flow).
- `get_current_user` reads the user from MySQL on every request. Authorization
  therefore uses the current database role, not the role claim inside the token.
- Response models are separate from ORM classes, so serialization does not
  trigger lazy relationship queries. The models intentionally define no ORM
  relationships.

## 4. Authentication and authorization

### Login

`POST /api/auth/login` (`backend/app/routers/auth.py:16`) accepts OAuth2 form
fields, not JSON:

```text
username=admin
password=admin123
```

Flow:

1. Find `app_user` by username.
2. Verify the bcrypt hash with `bcrypt.checkpw`.
3. Reject inactive accounts.
4. Issue an HS256 JWT with `sub`, `role`, `name`, `iat`, `exp`.
5. Return the token and the public user object.

### Protected requests

Send `Authorization: Bearer <token>`.

`get_current_user` (`backend/app/deps.py:24`):

1. Decodes the token with the configured secret and algorithm.
2. Converts `sub` to an integer user id.
3. Loads `AppUser` from MySQL.
4. Returns 401 if the token is invalid, expired or the account is missing or
   inactive.

Role dependencies wrap this function:

| Group           | Members                     | Used for                              |
| --------------- | --------------------------- | ------------------------------------- |
| `EDITOR_ROLES`  | admin, tehsildar, patwari   | Create/update land master data        |
| `MANAGER_ROLES` | admin, tehsildar            | Approve/reject mutations              |
| `ADMIN_ROLES`   | admin                       | Direct ownership inserts              |

Every read endpoint requires a valid logged-in user, including `viewer`.

## 5. Read flows

### Current owners of a plot

`GET /api/khasras/{id}/owners` and `GET /api/persons/{id}/lands` read
`v_current_ownership` (`db/schema.sql:337`). The view already joins khasra,
village, tehsil, district, khata and person and filters `to_date IS NULL`, so
the router only adds the id filter and ordering.

### Plot summary and reports

`v_khasra_summary` (`db/schema.sql:362`) aggregates each plot:

- area and land type name
- allocated current share (`SUM(share_percentage)`, normally 100 or 0)
- distinct current owner count
- dispute flag

`GET /api/reports/khasra-summary` filters this view by `village_id` or dispute
status. `GET /api/reports/villages/{id}/land` groups plots by land type.
`GET /api/reports/dashboard` counts villages, plots, persons, pending mutations
and disputed plots, and sums total plot area.

### Hierarchy and search

- States -> districts -> tehsils -> villages are simple filtered selects.
- `GET /api/persons?q=` searches both Hindi and English names.
- `GET /api/persons?village_id=` joins ownership and khasra and de-duplicates.
- `GET /api/khasras` filters by village, land type, dispute flag and khasra
  number.
- `GET /api/crop-cycles` joins crop names and can filter by khasra, village,
  season and year.
- `GET /api/khatas/{id}/khasras` joins the summary view to current ownership rows
  for that khata.

## 6. Standard write flows

Most writes follow the same pattern:

```
validate referenced rows (get_or_404)
        |
        v
build SQLAlchemy object / apply PATCH fields
        |
        v
db.add / mutate -> db.commit()
        |
        +-- IntegrityError -> rollback -> 409 with a domain message
        |
        +-- DBAPIError     -> rollback -> db_error() mapping
        |
        v
db.refresh() -> response_model
```

### Create a person

`POST /api/persons` (`backend/app/routers/persons.py:44`):

1. Accept an optional 12-digit Aadhaar.
2. Store `SHA-256(aadhaar)` in `aadhaar_hash` and the last four digits in
   `aadhaar_last4`.
3. The unique index on `aadhaar_hash` blocks duplicates; the router returns 409.
4. Responses never include the hash or the full number.

`PATCH /api/persons/{id}` applies only fields sent by the client. Sending
`"aadhaar": null` clears the stored hash and last-four values.

### Create a plot, khata, crop cycle or document

- **Khasra** (`POST /api/khasras`): requires an existing village and land type.
  `(village_id, khasra_no)` is unique. `boundary` is a JSON array of coordinate
  pairs; there is no spatial indexing.
- **Khata** (`POST /api/khatas`): requires an existing village.
  `(village_id, khata_no)` is unique.
- **Crop cycle** (`POST /api/khasras/{id}/crops`): requires an existing crop.
  `(khasra_id, crop_id, season, crop_year)` is unique.
- **Document** (`POST /api/khasras/{id}/documents`): stores metadata only.
  `uploaded_by` comes from the authenticated user. No file bytes are handled.

### Direct ownership insert (admin only)

`POST /api/ownership` (`backend/app/routers/ownership.py:51`):

1. Verify khasra, khata and person exist.
2. Verify the khata and khasra belong to the same village.
3. Insert the ownership row.
4. The database trigger rejects the insert if current shares would exceed 100%;
   the router maps this to HTTP 409.

This endpoint is for initial/corrective data entry. Normal transfers should go
through the mutation workflow.

## 7. Mutation workflow

A mutation is a requested change of ownership. It starts as `pending` and only
changes land records when a manager approves it.

### 7.1 Create a mutation

`POST /api/mutations` (`backend/app/routers/mutations.py:73`):

1. Khasra and destination person must exist.
2. For every type except `correction`, `from_person_id` is required and must
   differ from `to_person_id`.
3. The API checks that the seller currently holds at least the requested share.
   This is an early warning only.
4. If `mutation_no` is absent, generate
   `MUT-YYYYMMDD-XXXXXX` using `secrets.token_hex(3)`.
5. Insert with `status = pending`. No ownership row is touched.

Example:

```json
{
  "khasra_id": 1,
  "from_person_id": 1,
  "to_person_id": 3,
  "share_percentage": 10,
  "mutation_type": "sale",
  "order_date": "2026-10-25",
  "remarks_hi": "परीक्षण हस्तांतरण"
}
```

### 7.2 Approve a mutation

`POST /api/mutations/{id}/approve` (`backend/app/routers/mutations.py:123`),
available to admin and tehsildar.

```text
Manager        API                         MySQL
   |            |                            |
   | approve -->|                            |
   |            | BEGIN                      |
   |            | SELECT mutation ... FOR UPDATE
   |            |---------------------------->| lock mutation row
   |            | status must be pending     |
   |            | SELECT ownership ... FOR UPDATE
   |            |---------------------------->| lock seller's current rows
   |            | verify held share >= request
   |            |                            |
   |            | UPDATE old rows: to_date = order_date
   |            |---------------------------->| flush phase 1
   |            | INSERT retained remainders  |
   |            |---------------------------->| flush phase 2
   |            | INSERT buyer shares         |
   |            |---------------------------->| flush phase 3 (triggers check 100%)
   |            | UPDATE mutation status = approved
   |            | COMMIT                     |
   |<-- 200 -----|                            |
```

Detailed steps:

1. Lock the mutation row with `FOR UPDATE`; reject if it is not `pending`.
2. Load the plot and destination person.
3. If the type is `correction`, set the mutation approved and stop. Corrections
   do not alter ownership.
4. Load all current ownership rows of the seller for that khasra, ordered by
   `from_date` and `id`, also with `FOR UPDATE`.
5. Recompute the seller's held share under the lock. If it is less than the
   requested share, return 400.
6. Walk the seller's rows and take up to the requested share from each:
   - set the old row's `to_date` to the mutation `order_date`
   - record how much was taken and how much is retained
7. Flush the updates so the rows are no longer "current".
8. Insert retained remainder rows for the seller, preserving the old acquisition
   mode, khata and source mutation. Flush.
9. Insert buyer rows with `acquisition_mode` derived from the mutation type and
   `source_mutation_id` pointing at this mutation. Flush.
10. Mark the mutation approved and commit. Any database error rolls back the
    entire approval and is mapped to an HTTP error.

The three flushes are intentional. The insert trigger sums current shares for
the plot. If buyer shares were inserted before the seller's old rows were closed,
the trigger would see more than 100% and reject the transfer. Flushing in phases
keeps the invariant true after every statement.

If a seller's share is spread across multiple ownership rows (for example,
different khatas), the buyer receives one new row per source row. The buyer's
total is still the requested percentage.

### 7.3 Reject a mutation

`POST /api/mutations/{id}/reject` locks the mutation, requires `pending`, sets
`status = rejected`, optionally stores `remarks_hi` from the JSON body, and
commits. Ownership is unchanged.

### 7.4 Status rules

| Current status | Approve | Reject | Create ownership |
| -------------- | :-----: | :----: | :--------------: |
| pending        |   yes   |  yes   |        no        |
| approved       |   no    |   no   |        no        |
| rejected       |   no    |   no   |        no        |

Attempting to act on a non-pending mutation returns 409.

## 8. Database-level behaviour

### Triggers

| Trigger                    | Event                 | Effect                                             |
| -------------------------- | --------------------- | -------------------------------------------------- |
| `trg_ownership_share_ins`  | BEFORE INSERT         | Reject if current shares + new share > 100         |
| `trg_ownership_share_upd`  | BEFORE UPDATE         | Same check, excluding the row being updated        |
| `trg_ownership_audit_ins`  | AFTER INSERT          | Write JSON snapshot to `audit_log`                 |
| `trg_ownership_audit_upd`  | AFTER UPDATE          | Write old and new JSON snapshots                   |
| `trg_ownership_audit_del`  | AFTER DELETE          | Write old JSON snapshot                            |

The share triggers use `SIGNAL SQLSTATE '45000'`, which PyMySQL surfaces as a
`DBAPIError`. `db_error()` turns that into a 409 with a readable message.

### Views

| View                  | Purpose                                                   |
| --------------------- | --------------------------------------------------------- |
| `v_current_ownership` | Current owners with khasra, khata and hierarchy names      |
| `v_khasra_summary`    | Plot area, land type, allocated share and owner count      |

Both are mapped as read-only ORM classes and are never written by the API.

## 9. Error mapping

| Status | Typical causes                                                          |
| ------ | ----------------------------------------------------------------------- |
| 400    | Requested share exceeds holding; same from/to person; khata/khasra mismatch; referenced row in use |
| 401    | Missing, invalid or expired token; wrong username/password              |
| 403    | Authenticated but role not allowed; inactive account                    |
| 404    | Missing khasra, person, khata, mutation, village, etc.                  |
| 409    | Duplicate khasra/khata/mutation/Aadhaar; share total above 100; non-pending mutation |
| 422    | Pydantic validation failure; missing `from_person_id`; value too long   |
| 500    | Unhandled server or database error                                      |

Some routers replace the generic duplicate message with a domain-specific one
(for example, "Aadhaar is already registered"). Ownership inserts use the shared
`db_error()` mapper.

## 10. Endpoint map

### Public

| Method | Path             | Purpose                  |
| ------ | ---------------- | ------------------------ |
| POST   | `/api/auth/login` | Obtain a JWT            |
| GET    | `/api/health`     | Database connectivity   |
| GET    | `/`               | Service name and docs   |

### Authenticated reads

| Method | Path                                  | Purpose                                  |
| ------ | ------------------------------------- | ---------------------------------------- |
| GET    | `/api/auth/me`                        | Current user                             |
| GET    | `/api/states`                         | States                                   |
| GET    | `/api/districts?state_id=`            | Districts                                |
| GET    | `/api/tehsils?district_id=`           | Tehsils                                  |
| GET    | `/api/villages?tehsil_id=`            | Villages                                 |
| GET    | `/api/land-types`                     | Land type lookup                         |
| GET    | `/api/persons?q=&village_id=`         | Search persons                           |
| GET    | `/api/persons/{id}`                   | Person detail                            |
| GET    | `/api/persons/{id}/lands`             | Current land holdings                    |
| GET    | `/api/khasras?village_id=&q=`         | Search plots                             |
| GET    | `/api/khasras/{id}`                   | Plot detail                              |
| GET    | `/api/khasras/{id}/owners`            | Current owners                           |
| GET    | `/api/khasras/{id}/crops`             | Crop history                             |
| GET    | `/api/khasras/{id}/documents`         | Document metadata                        |
| GET    | `/api/khatas?village_id=`             | Khatas                                   |
| GET    | `/api/khatas/{id}`                    | Khata detail                             |
| GET    | `/api/khatas/{id}/khasras`            | Current plots in a khata                 |
| GET    | `/api/ownership?khasra_id=&person_id=`| Raw ownership rows (current by default)  |
| GET    | `/api/ownership/{id}`                 | Ownership row                            |
| GET    | `/api/mutations?status=&khasra_id=`   | Mutations                                |
| GET    | `/api/mutations/{id}`                 | Mutation detail                          |
| GET    | `/api/crops`                          | Crop lookup                              |
| GET    | `/api/crop-cycles?khasra_id=&season=` | Crop cycles with names                   |
| GET    | `/api/reports/dashboard`              | Counts and total area                    |
| GET    | `/api/reports/villages/{id}/land`     | Area grouped by land type                |
| GET    | `/api/reports/khasra-summary`         | Plot summary view                        |

### Writes

| Method | Path                              | Allowed roles              |
| ------ | --------------------------------- | -------------------------- |
| POST   | `/api/villages`                   | admin, tehsildar, patwari  |
| POST   | `/api/persons`                    | admin, tehsildar, patwari  |
| PATCH  | `/api/persons/{id}`               | admin, tehsildar, patwari  |
| POST   | `/api/khasras`                    | admin, tehsildar, patwari  |
| PATCH  | `/api/khasras/{id}`               | admin, tehsildar, patwari  |
| POST   | `/api/khasras/{id}/crops`         | admin, tehsildar, patwari  |
| POST   | `/api/khasras/{id}/documents`     | admin, tehsildar, patwari  |
| POST   | `/api/khatas`                     | admin, tehsildar, patwari  |
| POST   | `/api/ownership`                  | admin only                 |
| POST   | `/api/mutations`                  | admin, tehsildar, patwari  |
| POST   | `/api/mutations/{id}/approve`     | admin, tehsildar           |
| POST   | `/api/mutations/{id}/reject`      | admin, tehsildar           |

There are no DELETE endpoints for land records.

## 11. File map

| File                              | Responsibility                                                |
| --------------------------------- | ------------------------------------------------------------- |
| `backend/app/main.py`             | App creation, CORS, router registration, health              |
| `backend/app/config.py`           | Environment settings                                         |
| `backend/app/database.py`         | Engine, session factory, `Base`, `get_db`                    |
| `backend/app/enums.py`            | Shared domain enums                                          |
| `backend/app/models.py`           | SQLAlchemy mappings for tables and views                     |
| `backend/app/schemas.py`          | Pydantic request/response contracts                          |
| `backend/app/security.py`         | Aadhaar hashing, password hashing/verification, JWT creation |
| `backend/app/deps.py`             | Current user, role guard, `get_or_404`, DB error mapping     |
| `backend/app/routers/auth.py`     | Login and current-user endpoint                              |
| `backend/app/routers/hierarchy.py`| State/district/tehsil/village/land-type endpoints            |
| `backend/app/routers/persons.py`  | Person CRUD and holdings                                     |
| `backend/app/routers/khasras.py`  | Plot CRUD, owners, crops, documents                          |
| `backend/app/routers/khatas.py`   | Khata CRUD and plots in a khata                              |
| `backend/app/routers/ownership.py`| Read ownership plus admin-only direct insert                 |
| `backend/app/routers/mutations.py`| Mutation workflow and transactional approval                 |
| `backend/app/routers/crops.py`    | Crop lookup and crop-cycle listing                           |
| `backend/app/routers/reports.py`  | Dashboard, village land, plot summary                        |
| `db/schema.sql`                   | DDL, triggers, views                                         |
| `db/seed.sql`                     | Demo hierarchy, people, plots, ownership, crops, users       |
| `db/reseed.py`                    | Resets MySQL to pristine seed state (see §13)                |

## 12. Running locally

```zsh
mysql -uroot -p < db/schema.sql
mysql -uroot -p < db/seed.sql

cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit DATABASE_URL and JWT_SECRET in .env
uvicorn app.main:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs`.

Seed accounts:

| Username | Password    | Role    |
| -------- | ----------- | ------- |
| `admin`  | `admin123`  | admin   |
| `patwari`| `patwari123`| patwari |

Change both passwords and `JWT_SECRET` before deploying anywhere real.

## 13. Quick troubleshooting

| Symptom                              | Check                                                        |
| ------------------------------------ | ------------------------------------------------------------ |
| `Access denied for user`             | `DATABASE_URL` username/password/host                        |
| `Unknown database 'khetiyan'`        | Run `db/schema.sql` first                                    |
| `Can't connect to MySQL server`      | MySQL is running and the port/socket matches `DATABASE_URL`  |
| Demo data is tampered/mid-workflow   | `python ../db/reseed.py` — drops khetiyan, replays both SQL   |
| `1050 Table ... already exists`      | `CREATE TABLE` is not idempotent; use `db/reseed.py` (drops first) |
| `ModuleNotFoundError: app`           | Run `uvicorn` from `backend/` or set `PYTHONPATH=backend`     |
| Hindi text appears as `????`         | Ensure `charset=utf8mb4` in the URL and `utf8mb4` in MySQL   |
| 409 on ownership or approval         | Current shares for the plot are already at 100%              |
| 0 rows in views                      | Seed data was not loaded, or all ownership rows are historical |
