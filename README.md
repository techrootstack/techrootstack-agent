# Techrootstack Instagram posting agent

Posts the carousels in `schedule.csv` to Instagram on time, using the official Instagram Graph API.
Captions come from `content/captions.md`. Posted items are logged in `posted.json` so nothing posts twice.

## One-time setup
1. Create a **public** GitHub repo and upload this whole folder.
2. Repo Settings -> Pages -> deploy from the `main` branch (root). Your images will be at `https://<user>.github.io/<repo>/content/carousels/...`
3. Repo Settings -> Secrets and variables -> Actions:
   - Secrets: `IG_USER_ID` (Instagram Business account ID), `IG_ACCESS_TOKEN` (long-lived token)
   - Variables: `PUBLIC_BASE_URL` = `https://<user>.github.io/<repo>`, `TOKEN_EXPIRES` = date your token expires (YYYY-MM-DD)
4. Actions tab -> run **Post Techrootstack carousels** once with "Run workflow" to test.

## Daily use
- Add new carousels as `content/carousels/<name>/slide_01.jpg ...` (2-10 JPEGs, 1080x1350).
- Add a `## <name>` caption section in `content/captions.md`.
- Add a row in `schedule.csv` (`carousel,date,time_ist`).
- It checks every 20 minutes and posts one due carousel per run. Raise `MAX_PER_RUN` to post more at once.

## Test without posting
`DRY_RUN=1 python post.py`

## Notes
- Instagram limit: about 50 API posts per 24 hours.
- Tokens last ~60 days: renew and update the secret and `TOKEN_EXPIRES`. The log warns 10 days before expiry.
- Never commit your token to the repo.
