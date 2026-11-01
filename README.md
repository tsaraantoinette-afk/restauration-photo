---
title: Restaura
emoji: 📜
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
---

# Restaura

Retouche d'images, OCR et restauration de photos, sur un vrai serveur Python (Flask) permanent.

- `serveur/app.py` — serveur Flask : API + site web.
- `serveur/restauration.py` — OpenCV / NumPy : pastille par pastille, inpainting (`cv2.inpaint`), filtre bilatéral, LAB + CLAHE, masque de netteté. Toujours en couleur.
- `restaura_bureau.py` — interface de bureau Tkinter.
- Données des utilisateurs stockées sur l'appareil : usage illimité, sans compte.

## Hébergement (un seul service : site + API)
Le `Dockerfile` construit le site puis lance Flask avec gunicorn.

**Render** : New > Blueprint > choisir le dépôt GitHub (`render.yaml` est lu automatiquement). Renseigner `AI_API_KEY`.

**Railway** : New Project > Deploy from GitHub repo (`railway.json` utilise le Dockerfile). Variables > ajouter `AI_API_KEY`.

**Hugging Face Spaces** : Create new Space > SDK « Docker » > envoyer ces fichiers. Settings > Variables and secrets > ajouter le secret `AI_API_KEY`. (L'en-tête de ce README configure le Space sur le port 7860.)

Vérification : `https://<votre-adresse>/api/sante` doit répondre `{"ok": true}`.

### Site séparé (facultatif)
Pour garder le site sur Vercel et l'API sur Render/Railway/HF : définir `VITE_API_URL=https://<adresse-du-serveur>` au build du site, et `CORS_ORIGINES=https://<votre-site>.vercel.app` sur le serveur.

## En local
```
npm install && npm run build
pip install -r serveur/requirements.txt
cd serveur && python app.py        # http://localhost:7860
```

## Interface de bureau (Tkinter)
```
pip install -r requirements-bureau.txt
python restaura_bureau.py
```
