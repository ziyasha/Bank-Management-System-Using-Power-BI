# Bank Management System

A role-based banking backend built in Python and MySQL, with branch-aware
access control and a KYC-first customer onboarding model — built as a
portfolio project to demonstrate SQL schema design, Python application
structure, and the kind of business logic a real banking system needs.

A Streamlit frontend is in progress on top of this backend.

## Features

- **Four roles**: Admin, Manager, Staff, Customer — each with its own
  dashboard and permissions.
- **Branch model**: every user belongs to a branch (chosen from a fixed
  dropdown list, not free text). Staff and managers see their own branch
  by default, with the option to view all branches — except account
  verification, which is branch-exclusive (see below).
- **KYC-gated self-registration**: customers can't just sign up out of
  thin air. Staff first enroll a customer's real details (name, phone,
  date of birth, ID proof) after verifying them in person — mirroring how
  a real bank enrolls a customer at the counter. The customer can only
  create app access afterwards, and only if their phone + DOB + ID proof
  match an enrolled record.
- **Branch-exclusive account approval**: when a customer requests a new
  account (e.g. a fixed deposit account on top of their existing savings
  account), only staff/managers from *that customer's own branch* can see
  and approve the request.
- **Core banking operations**: deposits, withdrawals, transfers (with a
  daily withdrawal limit), balance and transaction history, loan
  applications with a staff-verify → admin-approve pipeline, complaints,
  and in-app notifications.
- **Reporting**: role-scoped CSV export (admin: everything; manager: full
  data for their branch or all branches; staff: customers only) designed
  to feed a Power BI dashboard.

## Tech Stack

- Python 3
- MySQL
- `mysql-connector-python` for the database layer
- `bcrypt` for password and PIN hashing

## Project Structure

```
main.py                    Entry point / top-level menu

services/
  auth_services.py         Registration (KYC-gated) and login
  admin_service.py         Admin dashboard
  manager_service.py       Manager dashboard
  staff_service.py         Staff dashboard
  customer_service.py      Customer dashboard
  account_service.py       Account creation, balance, branch-exclusive verification
  transaction_service.py   Deposit / withdraw / transfer
  loan_service.py          Loan application and approval pipeline
  complaint_service.py     Complaint submission and resolution
  notification_service.py In-app notifications
  bank_customer_service.py Branch-side KYC enrollment
  report_service.py        CSV export for Power BI

utils/
  validators.py            Re-prompting input validation helpers
  branches.py               Fixed branch list + dropdown selector
  password_utils.py         bcrypt hashing/verification
  id_formatter.py            Role-prefixed display IDs (CU/ST/MG/AD)

database/
  connection.py              DB connection (raises a clear error if it fails)
  schema.sql                 Full table definitions — run this on a fresh DB
  seed_data.py                Wipes and reloads ~60 rows of realistic test data
  migration_add_branch.sql    Historical — folded into schema.sql
  migration_bank_customers.sql Historical — folded into schema.sql

config/
  db_config.py                Database connection settings
```

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the database connection** in `config/db_config.py`:
   ```python
   HOST = "localhost"
   USER = "root"
   PASSWORD = "your_mysql_password"
   DATABASE = "banking_system"
   ```

3. **Create the schema**
   ```bash
   mysql -u root -p < database/schema.sql
   ```
   This creates the `banking_system` database and all seven tables. If
   you already have an older version of this database (pre-branch,
   pre-KYC), use `migration_add_branch.sql` and
   `migration_bank_customers.sql` instead to upgrade it in place.

4. **(Optional) Load realistic test data**
   ```bash
   python -m database.seed_data
   ```
   This wipes all tables and inserts ~60 rows across every table —
   admin, managers, staff, and customers spread across three branches,
   plus accounts, transactions, loans, complaints, and notifications.
   Login credentials for every seeded user are printed at the end.

5. **Run the app**
   ```bash
   python main.py
   ```

## How the branch / KYC model works

This mirrors how a real bank actually onboards someone:

1. A customer visits a branch in person with their documents. Staff use
   **Enroll New Customer** to record their name, phone, DOB, and ID proof
   in `bank_customers` — this is *not* an app account yet.
2. The customer downloads the app and registers, entering their phone,
   DOB, and ID proof. The app checks this against `bank_customers`. No
   match → registration is rejected with instructions to visit a branch.
   Match found → an app login (`users` row) is created using the details
   already on file, and the `bank_customers` record is marked as claimed
   so it can't be used to register a second app account.
3. Once logged in, the customer can request additional account types
   (e.g. a fixed deposit account) the same way they applied for their
   first account. That request shows up as **PENDING** and is only
   visible to staff/managers whose branch matches the customer's branch
   — not the whole bank.

## Roadmap

- Streamlit frontend (in progress)
- Branch-scoped reporting extended to loans/complaints/activity tracking
