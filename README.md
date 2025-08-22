

## What’s new in this version
- Per-user **trade logs** (visible on dashboard)
- **PnL** (realized) and **last order** snapshot
- **Start/Stop trading** toggle
- **Timezone selector** (users set local time; app schedules accordingly)
- Default **1 trade/day** but **flexible** up to user setting
- PayPal subscription price set to **$14.99/month**


## Deploy on Render (Free plan)
1) Create an account at render.com and add a **New Blueprint** → upload this folder with `render.yaml`.
2) Render will create a **Web Service** and a **Cron Job** that pings `/wake` every minute.
3) Set env vars (populate `ENCRYPTION_KEY`) and hit **Deploy**.
4) The cron ping keeps the service warm and triggers the minute scheduler so **multiple trades/day** are safe and on time.

### Safety & duplicate protection
- Per-user file lock: prevents overlapping orders for the same user.
- Idempotency check: never exceeds each user's `trades_per_day`.
- Schedule window: `/wake` runs each minute and only fires when the user's local clock matches their configured minute.
