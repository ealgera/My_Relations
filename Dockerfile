# Gebruik een officiële Python runtime als een parent image
FROM python:3.12-slim

# Stel de werkdirectory in de container in
WORKDIR /app

# Kopieer de requirements file naar de container
COPY requirements.txt .

# Installeer alle benodigde packages gespecificeerd in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode
COPY . .

# Maak de data en sessions directories aan en geef de juiste rechten
RUN mkdir /data /sessions && chown -R 1000:1000 /data /sessions

# Maak de poort 8000 beschikbaar voor de wereld buiten deze container
EXPOSE 8008

# Run de applicatie
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]