# 1) Construction du site (React / Vite)
FROM node:20-slim AS site
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# 2) Serveur Python complet (Flask + OpenCV)
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PORT=7860
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# On copie tout le depot puis on verifie que le dossier serveur/ est bien present
COPY . /tmp/src
RUN test -f /tmp/src/serveur/requirements.txt || (echo "ERREUR : le dossier 'serveur/' est absent du depot GitHub. Envoyez-le (serveur/app.py, restauration.py, requirements.txt, consignes.json)." && exit 1) \
    && cp -r /tmp/src/serveur ./serveur && rm -rf /tmp/src \
    && pip install --no-cache-dir -r serveur/requirements.txt
COPY --from=site /app/dist ./dist
WORKDIR /app/serveur
EXPOSE 7860
CMD gunicorn app:app --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 300
