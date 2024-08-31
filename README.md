# Relatiebeheer Systeem

## AI generated
This system has been generated with Claude 3.5 Sonnet. Not in one go but in many sessions in which I told the AI what I wanted and it generated the code. I used a project but finaly had to use 3 project in which I had to start over again and 'feed' the AI with the data/code sofar. Thids was because of Claude prompt/token 'exhaustion'.
I created the database model. I also told the AI to use Python, fastAPI and SQLModel. Also I wanted it to use bootstrap 5.
The AI mainly generated 98% of the code. I provide about 2% of the code in the rare cases I wanted to be the code differently.

## Overzicht

Het Relatiebeheer Systeem is een webapplicatie ontwikkeld met Python en FastAPI, ontworpen om families, personen, en hun onderlinge relaties te beheren. Het systeem biedt functionaliteiten voor het bijhouden van familiegegevens, persoonlijke informatie, jubilea, en verschillende soorten relaties tussen personen.

## Kenmerken

- Beheer van families en personen
- Registratie van jubilea en belangrijke datums
- Definieren en beheren van verschillende relatietypes
- Gebruikersauthenticatie via Google OAuth
- Responsieve webinterface

## Technologiestack

- Backend: Python 3.12, FastAPI
- Database: SQLite met SQLModel ORM
- Frontend: HTML, CSS (Bootstrap), Jinja2 templates
- Authenticatie: Google OAuth
- Containerisatie: Docker

## Vereisten

- Docker en Docker Compose
- Python 3.12 (voor lokale ontwikkeling)
- Een Google Cloud Platform account (voor OAuth configuratie)

## Installatie en Opstarten

1. Clone de repository:
   ```
   git clone https://github.com/ealgera/My_Relations.git
   cd My_Relations
   ```

2. Maak een `.env` bestand aan in de hoofddirectory en vul de volgende variabelen in:
   ```
   DATABASE_URL=sqlite:////data/my_relations_app.db
   SECRET_KEY=your_secret_key_here
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   OAUTHLIB_INSECURE_TRANSPORT=1  # Alleen voor ontwikkeling, verwijder in productie
   ```
   SECRET_KEY is produced in the app itself so you can comment this line.

3. Build en start de Docker containers:
   ```
   sudo docker compose up --build
   ```
4. De applicatie is nu toegankelijk via `http://127.0.0.1:8000`
   This id dependant on the Google project 'authorized redirect' uri. I used: http://127.0.0.1:8000/auth

## Gebruik

Na het opstarten van de applicatie:

1. Log in met je Google-account
2. Gebruik het navigatiemenu om verschillende secties van de applicatie te verkennen:
   - Families
   - Personen
   - Jubilea
   - Relaties
   - Jubileumtypes
   - Relatietypes

3. Voeg nieuwe records toe, bewerk bestaande gegevens, of verwijder items waar nodig.
   You can create an 'Administrator' by:
   - if you've started the app once, than the database and tables are created;
   - you must create a record in the SQL-database User table in /data;
     - this record must contain the e-mail adres of the user with wich you want to log into the app (with Google);
     - the role of this User must be 'Administrator';
   - After that you can login with Google and a new menu item becomes visible with which you can create new users.
   - This part of the app will be modified to make this more user friendly. 

## Ontwikkeling

Voor lokale ontwikkeling zonder Docker:

1. Voer de bovenstaande eerste 2 stapen uit (clone en .env)

2. Maak een virtuele omgeving aan:
   ```
   python -m venv venv
   source venv/bin/activate  # Op Windows gebruik: venv\Scripts\activate
   ```

3. Installeer de vereiste packages:
   ```
   pip install -r requirements.txt
   ```

4. Voeg een admin gebruiker toe met 'create_admin_and_roles.py'

5. Start de applicatie:
   ```
   uvicorn app.main:app --reload
   ```

## Bijdragen

Bijdragen aan dit project zijn welkom! Gelieve de volgende stappen te volgen:

1. Fork de repository
2. Maak een nieuwe branch voor je feature (`git checkout -b feature/AmazingFeature`)
3. Commit je wijzigingen (`git commit -m 'Add some AmazingFeature'`)
4. Push naar de branch (`git push origin feature/AmazingFeature`)
5. Open een Pull Request

## Licentie

Dit project is gelicentieerd onder de MIT Licentie - zie het [LICENSE](LICENSE) bestand voor details.

## Contact

Eric Algera - [eric@algera.nl](mailto:eric@algera.nl)

Project Link: [https://github.com/ealgera/My_Relations](https://github.com/ealgera/My_Relations)
