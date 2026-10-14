# SkillSwap

## App overview

SkillSwap is a web app where people can share skills they know and find people who can teach them something new. Members can suggest an exchange, complete it together, and leave a review.

The backend uses Flask and SQLite. The frontend is made with Vue 3.

## Features

- Create an account and sign in with a secure password.
- Add skills you can teach or skills you want to learn.
- Browse and filter skill listings.
- Send, accept, decline, or cancel exchange requests.
- Confirm an exchange as complete. Both people need to confirm.
- Leave a review after an exchange is completed.
- Use an Admin account to approve skill offers and manage accounts.
- Update your profile and see your exchange activity.

Skill offers are hidden until approved by an Admin. Listings for skills people want to learn are visible right away.

## Initial setup

You will need Python 3.10 or newer and Node.js 20 or newer.

From the project folder, set up the backend:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example .env
```

Open `.env` and replace the example secret values. Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` to the login you want for the first Admin. The password must be at least 12 characters. The local SQLite database and Admin account are set up automatically when the backend starts.

Run the backend:

```powershell
flask --app backend\run.py run --debug --port 5001
```

In another terminal, run the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. The frontend sends API requests to the backend running on port 5001.

## API documentation

Protected routes require a SkillSwap access token in the `Authorization` header. Registration creates a regular User account. Admin routes require an Admin account.

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register a User account. |
| POST | `/api/auth/login` | Public | Sign in and receive an access token. |
| GET | `/api/auth/me` | Signed-in user | Get the signed-in user's profile. |
| GET | `/api/profile` | Signed-in user | Get your profile and activity statistics. |
| PUT | `/api/profile` | Signed-in user | Update your profile. |
| GET | `/api/listings` | Public | Browse visible listings. |
| POST | `/api/listings` | Signed-in user | Create an Offer or Want listing. |
| GET | `/api/listings/<id>` | Public or listing owner | Get a listing. Unapproved listings are only visible to their owner. |
| PUT | `/api/listings/<id>` | Listing owner | Update your listing or resubmit a rejected Offer. |
| DELETE | `/api/listings/<id>` | Listing owner | Delete your listing if it is not linked to an exchange. |
| GET | `/api/requests` | Signed-in user | List exchanges you participate in. |
| POST | `/api/requests` | Signed-in user | Request an exchange with another member. |
| PUT | `/api/requests/<id>` | Exchange participant | Accept, decline, cancel, or confirm completion of an exchange. |
| GET | `/api/reviews` | Public | Browse reviews, optionally filtered by member or exchange. |
| POST | `/api/reviews` | Exchange participant | Review another participant after the exchange is completed. |
| GET | `/api/admin/stats` | Admin | View platform statistics. |
| GET | `/api/admin/users` | Admin | List member accounts. |
| PUT | `/api/admin/users/<id>/status` | Admin | Activate or deactivate a member account. |
| GET | `/api/admin/listings/pending` | Admin | List Offers waiting for review. |
| PUT | `/api/admin/listings/<id>/approve` | Admin | Approve or reject an Offer listing. |
