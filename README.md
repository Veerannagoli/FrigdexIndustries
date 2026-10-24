# Frigdex Industries — Flask + MySQL

A Flask business website and admin panel backed by MySQL. Public enquiry submissions are stored in MySQL and then open WhatsApp with a pre-filled enquiry message.

## Run locally (Windows PowerShell)
1. Install Python 3.10+ and MySQL 8+.
2. In MySQL Workbench, run `database/frigdex_schema.sql`.
3. Open a terminal in the project folder (the one containing `app.py`) and run:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
4. Edit `.env` with your MySQL credentials, a long random `SECRET_KEY`, the WhatsApp number (digits only, with country code), and the phone number and email you want shown on the website (`SITE_PHONE`, `SITE_EMAIL`, optional `GST_NUMBER`).
5. Create the admin account with `python create_admin.py`.
6. Start locally with `python app.py` and visit `http://127.0.0.1:5000`. Admin login: `/admin/login`.

## WhatsApp enquiry behaviour
When a visitor submits **Send an enquiry**, the app first saves the enquiry in the `enquiries` table. It then opens WhatsApp (`wa.me`) with a message containing the enquiry ID, name, phone, product, and requirement. The visitor still needs to press **Send** inside WhatsApp; websites cannot send a WhatsApp message silently without WhatsApp Business API integration.

Set `WHATSAPP_NUMBER` to the business's WhatsApp number including country code, digits only. Example format for India: `91XXXXXXXXXX` (replace Xs with the real number). Never include `+`, spaces, or hyphens.

## Deploy on Render
**Before deployment:** the app needs a reachable MySQL database. Render's filesystem is not a permanent database, so use an external MySQL provider (for example, an existing hosted MySQL/Aiven database) and make sure its network access permits Render connections. Import `database/frigdex_schema.sql` into that hosted database.

1. Push this project to a GitHub repository. Do not upload `.env`; it is excluded from this ZIP.
2. In Render, choose **New + → Web Service** and connect the repository.
3. Leave **Root Directory** empty if `app.py` is at the top of the repository. If the repository contains this project inside a folder, set Root Directory to that folder.
4. Set **Runtime** to Python 3.12 (if Render offers a runtime selector).
5. Set **Build Command** to `pip install -r requirements.txt`.
6. Set **Start Command** to `gunicorn app:app`.
7. Add these environment variables in Render's Environment tab:
   - `SECRET_KEY` = a long, random secret value
   - `DB_HOST` = hosted MySQL hostname
   - `DB_PORT` = database port (usually `3306`)
   - `DB_USER` = database username
   - `DB_PASSWORD` = database password
   - `DB_NAME` = database/schema name (for example `frigdex`)
   - `WHATSAPP_NUMBER` = Frigdex WhatsApp number with country code, digits only
   - `SITE_PHONE` = phone number as shown to visitors (optional)
   - `SITE_EMAIL` = public email address (optional)
   - `GST_NUMBER` = GSTIN shown in the footer (optional)
   - `FLASK_DEBUG` = `0`
   - `RENDER` = `true`
8. Click **Create Web Service** and wait for the deploy to finish. Open the generated `onrender.com` URL and test the home page, product list, contact form, WhatsApp redirect, and admin login.
9. Create the admin account against the hosted database by running `python create_admin.py` in a one-off shell/console connected to the same service environment, or use Render Shell if available. Do not create the admin against your local database and expect it to exist in production.

## Important deployment notes
- This app uses MySQL; setting only Render variables does not create the schema. Import the SQL schema into the hosted database first.
- Product image uploads are stored under `static/uploads`. Render's local filesystem may be ephemeral, so use persistent disk or external/object storage for production product images.
- Use a strong admin password (12+ characters), HTTPS, and database credentials with limited privileges.
- The WhatsApp form redirects to WhatsApp after the enquiry is saved. It does not send messages automatically on the user's behalf.

## Customising the website
- **Contact details**: set `SITE_PHONE`, `SITE_EMAIL`, `WHATSAPP_NUMBER` and `GST_NUMBER` in `.env`. Call and WhatsApp buttons, the header phone number and the mobile call bar appear automatically once they are set.
- **Home page photo**: drop a photo named `hero.jpg` into `static/` (a wide shot of your products or factory, at least 1600 px wide). It is used behind the home page heading. Without it the heading sits on solid teal.
- **Brands on the home page** come from the Brand field of your visible products. Only brands you enter on products are shown.
- **Price**: a price of 0 shows "Price on request" on the public site.
- **Colours and fonts** are defined at the top of `static/style.css`.
