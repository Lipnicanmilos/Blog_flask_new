# Blog Flask App

Jednoduchá blogovacia aplikácia postavená na Flasku — registrácia a prihlásenie používateľov, tvorba príspevkov s rich-text editorom (CKEditor), komentáre, lajky, reset hesla cez e-mail a jednoduchý real-time chat (Flask-SocketIO).

## Funkcie

- Registrácia / prihlásenie / odhlásenie (Flask-Login, hashované heslá cez Bcrypt)
- Tvorba, úprava a mazanie príspevkov
- Komentáre a lajky k príspevkom
- Upload profilového obrázka
- Reset zabudnutého hesla cez e-mail (časovo obmedzený token)
- Real-time chat medzi prihlásenými používateľmi (Socket.IO)

## Technológie

- Python, Flask, Flask-SQLAlchemy
- Flask-Login, Flask-Bcrypt
- Flask-Mail, Flask-SocketIO, Flask-CKEditor
- SQLite

## Lokálne spustenie

1. Naklonuj repozitár a vytvor virtuálne prostredie:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Skopíruj `.env.example` na `.env` a doplň vlastné hodnoty (secret key, e-mailové prihlasovacie údaje — pre Gmail použi [App Password](https://myaccount.google.com/apppasswords), nikdy bežné heslo k účtu):
   ```bash
   cp .env.example .env
   ```

3. Spusti aplikáciu:
   ```bash
   python app.py
   ```
   Aplikácia beží na `http://localhost:5000`.

## Poznámka

Toto je cvičný/portfóliový projekt vytvorený pri učení sa Flasku. Databáza (`sqlite.db`) sa vytvorí automaticky pri prvom spustení a nie je súčasťou repozitára.
