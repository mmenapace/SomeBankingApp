# FastAPI Banking Portal

This is the Angular frontend for a simple banking application that communicates with a FastAPI backend running at `http://127.0.0.1:8000`.

The purpose of the app is to simulate common banking actions:

- create a user and bank account
- transfer funds between IBAN accounts
- issue a payment card
- recharge a card from an IBAN
- make a card payment
- review recent transaction audit logs

The app is intentionally lightweight and acts as a control panel for the backend banking logic rather than a full production banking dashboard.

## How the app is structured

The frontend is a single standalone Angular component (`AppComponent`) that holds all the forms and frontend state in memory.

### Main files

- `src/app/app.ts` — contains the core logic and form handling
- `src/app/app.html` — UI layout and all banking forms
- `src/app/core/services/bank.services.ts` — HTTP client service that calls the backend
- `src/app/core/models/bank.models.ts` — TypeScript interfaces for request/response data
- `src/app/app.scss` — styling for the portal

## Core logic flow

### 1. User creation

The user form requests:

- `full_name`
- `email`

When the form is valid, `createUser()` triggers a POST to:

```http
POST /users/
```

The request body is built from the form values. If the backend succeeds, the app shows a message like:

```text
User Created! IBAN: <generated-iban>
```

The response contains:

- `user_id`
- `name`
- `iban`

This is the foundational step that creates a customer and their bank account.

### 2. IBAN transfer

The transfer form requires:

- `sender_iban`
- `receiver_iban`
- `amount`
- optional `description`

On submit, `transferIban()` calls:

```http
POST /transfers/iban
```

This simulates moving money from one account to another. After a successful transfer, the UI:

- shows a success message
- clears the form
- reloads the audit logs so the transaction history updates immediately

### 3. Card issuance

To issue a payment card, the app asks for a `user_id` and calls:

```http
POST /cards/issue
```

The backend returns a card payload that includes data such as:

- `id`
- `card_number`
- `expiry_month`
- `expiry_year`
- `balance`
- `is_active`

The frontend displays the card number in a success banner.

### 4. Card recharge

The recharge form requires:

- `card_number`
- `source_iban`
- `amount`

This calls:

```http
POST /cards/recharge
```

The logic behind this action is that a customer funds a card using money already available in an IBAN account. Once the backend approves it, the app resets the form and refreshes the audit list.

### 5. Card payment

For a payment, the form collects:

- `card_number`
- `cvv`
- `expiry_month`
- `expiry_year`
- `merchant_name`
- `amount`

The UI sends this payload to:

```http
POST /cards/pay
```

This represents a payment authorization flow where the app validates the card details and merchant information before the backend applies the debit.

### 6. Audit logs and transaction history

On initialization, `ngOnInit()` calls `loadLogs()`:

```http
GET /transactions/audit
```

The app stores the returned entries in `logs`, an array of `TransactionLog` objects, and renders them on the right side of the screen.

Each log includes:

- `tx_type`
- `source_identifier`
- `destination_identifier`
- `amount`
- `description`
- `timestamp`

The audit panel acts like a live ledger and provides a quick view of all operations performed in the system.

## Frontend state and validation

The Angular component defines multiple reactive forms using `FormBuilder`:

- `userForm`
- `transferForm`
- `cardForm`
- `rechargeForm`
- `paymentForm`

Each form uses validation rules such as:

- required fields
- email validation
- minimum amounts greater than zero
- month range `1-12`

If a form is invalid, the submit button stays disabled. This prevents invalid requests from reaching the backend.

## Feedback mechanism

The app has a shared `feedbackMessage` field used for short success/error notifications. When an action succeeds or fails, the UI sets this message and clears it automatically after 5 seconds using `setTimeout()`.

This creates a simple, user-friendly response experience without a dedicated state-management library.

## Service layer

`BankService` is the single access point for API calls. It wraps Angular's `HttpClient` and exposes methods such as:

- `createUser()`
- `transferIban()`
- `issueCard()`
- `rechargeCard()`
- `payWithCard()`
- `getLogs()`

All endpoints are pointed to the backend base URL:

```ts
private apiUrl = 'http://127.0.0.1:8000';
```

This keeps the frontend clean and makes the backend integration easy to replace or extend.

## Data model overview

The model layer defines the structure of data used by the app:

- `UserCreate` and `UserResponse`
- `IBANTransfer`
- `CardCreate` and `CardResponse`
- `CardRecharge`
- `CardPayment`
- `TransactionLog`

These interfaces ensure the frontend understands the shape of every request and response returned by the backend.

## Application behavior in one sentence

This banking portal is a frontend simulator that lets a user create accounts, move money, manage cards, process payments, and inspect a transaction audit trail through a single set of reactive forms connected to a FastAPI backend.

## Running the app

From the frontend project root, start the Angular development server:

```bash
npm install
ng serve
```

Then open:

```text
http://localhost:4200/
```

Make sure the FastAPI banking backend is also running on `http://127.0.0.1:8000` or the requests will fail.

## Notes

- The frontend does not persist data locally; it depends on the backend for actual banking state.
- The UI is a control panel, not a production-grade banking system.
- The app is designed to demonstrate the logic of account management, payments, and transaction auditing in a simple, readable way.
