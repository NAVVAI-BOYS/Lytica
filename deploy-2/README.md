# Lytica · Sourcing Leverage Check

Navvai lead magnet for Lytica. A four minute check that scores four areas of a
buyer's sourcing, prices the gap in their own figures, and names the part of
Lytica accountable for closing each one.

Built on the standing AUDIT-LITE Flask skeleton, so it deploys and behaves the
same way as every other Navvai web app.

---

## Deploy on Render

New → **Web Service** → connect this repo. Not a Static Site: the app needs a
server for lead capture.

| Setting | Value |
| --- | --- |
| Runtime | **Python 3** (not Docker) |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app` |
| Health check path | `/healthz` |
| Instance type | Starter is enough |

### Environment variables

| Key | Required | What it does |
| --- | --- | --- |
| `ADMIN_KEY` | Yes | Gates `/admin/leads`. Use Render's Generate button. |
| `ANTHROPIC_API_KEY` | Reserved | Not used by this build. Kept as a slot so every Navvai service carries the same set. |
| `LEAD_WEBHOOK_URL` | Optional | Every lead is POSTed here as JSON. Point it at Zapier, Make or a Slack workflow. A webhook failure never blocks capture. |

`render.yaml` is included if you would rather deploy this as a Blueprint.

---

## Routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | GET | The app |
| `/healthz` | GET | Render health check |
| `/api/lead` | POST | Called by the front end when someone unlocks their report |
| `/admin/leads` | GET | `/admin/leads?key=YOUR_ADMIN_KEY` returns every lead as JSON, newest first |

## Where the leads actually live

- **The service logs are the durable record.** Every lead prints one line to
  stdout prefixed `LEAD ` followed by JSON. Render keeps stdout, so this
  survives a deploy.
- `leads.jsonl` on disk is a local convenience only. **Render wipes the disk on
  every deploy** unless you attach a disk, so treat it as a cache, not storage.
- For anything permanent, set `LEAD_WEBHOOK_URL` and let the lead land in a
  sheet, a CRM or Slack.

## What a lead contains

Name, company, email, the lane they picked, their seat, the verdict band, the
weakest area and its score, all four area scores, their stated twelve month
goal, and every question with the answer they tapped, anything they typed, and
the score it produced.

---

## Local run

```bash
pip install -r requirements.txt
ADMIN_KEY=localkey gunicorn app:app --bind 127.0.0.1:8000
```

Then open http://127.0.0.1:8000

`static/index.html` also opens straight off disk with no server. Everything
works except lead capture, and the report says so rather than pretending
something was sent.

## Editing the app

The whole front end is one file: `static/index.html`. No build step, no
bundler, no dependencies to install. Open it, edit it, refresh.

## Before it goes to the client

- [ ] Point the "Book the working session" button at the right Lytica URL. It
      currently opens `https://lytica.com/book-a-demo/`.
- [ ] Set `LEAD_WEBHOOK_URL` so leads reach a human rather than only the logs.
- [ ] Decide whether the report should email itself. Not wired: the app captures
      the lead and the report says plainly that nothing was emailed.
- [ ] Remove the "Demo preview" pill at the bottom right of the page when it
      stops being a demo. It is the only place the word demo appears.
