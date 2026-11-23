# ⬇ Extractor – Video & Audio Downloader

Webseite zum Herunterladen von Videos und Musik per Link – von **TikTok, YouTube,
Instagram, X/Twitter, Facebook, Vimeo, Reddit, Twitch, SoundCloud, Dailymotion,
Pinterest, Bilibili, Snapchat, Threads, Bandcamp, Streamable** und über 1000
weiteren Seiten (alles, was [yt-dlp](https://github.com/yt-dlp/yt-dlp) unterstützt).

## Funktionen

- Link einfügen → Titel, Vorschaubild, Dauer und Plattform werden angezeigt
- **Video-Formate:** MP4, WebM, MKV, MOV, AVI
- **Auflösung:** Beste, 4K (2160p), 2K (1440p), 1080p, 720p, 480p, 360p, 240p, 144p
  (verfügbare Auflösungen werden mit ✓ markiert)
- **Audio-Formate:** MP3, M4A, WAV, FLAC, OGG, OPUS, AAC
- **Audio-Bitrate:** 320 / 256 / 192 / 128 / 96 kbit/s
- Fortschrittsanzeige mit Geschwindigkeit und Restzeit
- Cover-Bild und Metadaten werden in MP3/M4A/FLAC eingebettet
- Heruntergeladene Dateien werden nach 30 Minuten automatisch vom Server gelöscht

## Starten

Voraussetzungen: Python 3.10+ und **ffmpeg** (`sudo apt install ffmpeg`, `brew install ffmpeg`
bzw. unter Windows von ffmpeg.org).

```bash
pip install -r requirements.txt
python app.py
```

Dann im Browser öffnen: http://localhost:5000

### Mit Docker

```bash
docker build -t extractor .
docker run -p 5000:5000 extractor
```

## Online stellen (über GitHub)

GitHub Pages geht nicht, da die Seite einen Python-Server + ffmpeg braucht.
Stattdessen:

### Option 1: Render (kostenlos, öffentliche URL)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/camery12/extractor)

1. Auf den Button klicken und mit GitHub bei Render anmelden
2. „Apply“ klicken – Render baut die Seite aus dem `Dockerfile` (`render.yaml` ist schon dabei)
3. Nach ein paar Minuten ist sie unter `https://extractor-xxxx.onrender.com` erreichbar

Hinweis: Der Gratis-Plan schläft nach 15 Min. Inaktivität ein (erster Aufruf dauert dann ~1 Min.).
Das Repo muss dafür **öffentlich** sein oder Render Zugriff darauf haben.

### Option 2: GitHub Codespaces (läuft im Browser)

Im Repo auf **Code → Codespaces → Create codespace** klicken. ffmpeg und alle
Pakete werden automatisch installiert, die Seite startet von selbst und öffnet sich
in einem neuen Tab.

## YouTube auf dem Server: „Bot-Schutz“-Fehler beheben

YouTube blockiert Anfragen von Hosting-Anbietern wie Render. Abhilfe: Cookies eines
eingeloggten YouTube-Kontos hinterlegen.

> ⚠️ Am besten ein **Zweit-Google-Konto** verwenden – YouTube kann Konten, die für
> Downloads genutzt werden, einschränken.

1. Im Browser (Chrome/Edge/Firefox) ein **privates Fenster** öffnen und bei YouTube einloggen.
2. Die Erweiterung **„Get cookies.txt LOCALLY“** installieren (im privaten Fenster erlauben).
3. Auf youtube.com die Erweiterung öffnen → **Export** → Datei `cookies.txt` speichern.
4. Das private Fenster **schließen, ohne dich auszuloggen** (sonst werden die Cookies ungültig).
5. Bei Render: Service → **Environment** → **Secret Files** → **Add Secret File**
   - Filename: `cookies.txt`
   - Contents: kompletten Inhalt der Datei einfügen → **Save Changes**
6. Render startet die Seite neu – danach funktioniert YouTube.

Cookies laufen irgendwann ab (meist nach Wochen bis Monaten). Kommt der Fehler wieder,
einfach die Schritte 1–5 wiederholen. Lokal (`python app.py` auf dem eigenen PC) sind
keine Cookies nötig. Alternativ kann der Pfad auch über die Umgebungsvariable
`COOKIES_FILE` gesetzt werden.

## Tipps

- yt-dlp regelmäßig aktualisieren (`pip install -U yt-dlp`), da Plattformen
  wie YouTube und TikTok ihre Seiten oft ändern.
- Maximale Videolänge lässt sich über die Umgebungsvariable `MAX_DURATION`
  (Sekunden, Standard 4 h) einstellen.

## Hinweis

Lade nur Inhalte herunter, an denen du die Rechte hast oder deren Download erlaubt ist.
Beachte das Urheberrecht und die Nutzungsbedingungen der jeweiligen Plattform.
