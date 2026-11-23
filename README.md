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

## Tipps

- yt-dlp regelmäßig aktualisieren (`pip install -U yt-dlp`), da Plattformen
  wie YouTube und TikTok ihre Seiten oft ändern.
- Maximale Videolänge lässt sich über die Umgebungsvariable `MAX_DURATION`
  (Sekunden, Standard 4 h) einstellen.

## Hinweis

Lade nur Inhalte herunter, an denen du die Rechte hast oder deren Download erlaubt ist.
Beachte das Urheberrecht und die Nutzungsbedingungen der jeweiligen Plattform.
