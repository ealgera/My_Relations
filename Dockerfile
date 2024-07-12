# Gebruik een officiële Python runtime als een parent image
FROM python:3.12-slim

# Stel de werkdirectory in de container in
WORKDIR /app

# Kopieer de huidige directory inhoud naar de container in /app
COPY . /app

# Installeer alle benodigde packages gespecificeerd in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Maak de data directory aan en geef de juiste rechten
RUN mkdir /data && chown -R 1000:1000 /data

# Maak de poort 8000 beschikbaar voor de wereld buiten deze container
EXPOSE 8000

# Definieer omgevingsvariabele
# ENV NAME World

# Run app.py wanneer de container wordt gelanceerd
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]