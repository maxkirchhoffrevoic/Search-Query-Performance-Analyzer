# 📊 Amazon Search Query Performance Analyzer

Ein intelligentes Tool zur Analyse von Amazon Search Query Performance Reports mit AI-gestützter Kategorisierung und visuellen Dashboards.

## 🚀 Features

### 🔹 Smart Ingestion Engine
- **Drag & Drop**: Sofortige Verarbeitung von Amazon SQP Reports (.csv/.xlsx)
- **Batch Processing**: Mehrere Wochen/Monate gleichzeitig hochladen für historische Trends
- **Privacy First**: Alle Datenverarbeitung erfolgt lokal in deiner Browser-Session

### 🔹 AI-Powered Categorization
- **GPT-5.1 Thinking**: Nutzt die neueste GPT-5.1 Thinking Technologie für tiefgreifende Analyse und präzise Kategorisierung
- **Auto-Grouping**: Die KI gruppiert automatisch tausende rohe Search Terms in logische Produktkategorien
- **Niche Discovery**: Trennt sofort "Generic" Traffic von "Branded" Traffic ohne manuelles Tagging
- **Reasoning Effort**: Konfigurierbare Reasoning-Tiefe (high empfohlen) für optimale Ergebnisse

### 🔹 Visual Intelligence Dashboard
- **Opportunity Matrix**: Bubble Chart visualisiert High Volume vs. Low Market Share Nischen
- **Market Trend Analysis**: Dual-Axis Charts vergleichen Market Volume vs. Sales Velocity über Zeit
- **Share of Voice Tracking**: Überwache deinen Brand Share (Impression % vs. Sales %) auf Kategorie-Ebene

### 🔹 Deep Dive Analytics
- **Search Term Granularity**: Drill-Down von Kategorie-Ebene zu einzelnen Search Terms
- **Performance Metrics**: Sofortige Ansicht von Total Volume, Market Sales und deinem spezifischen Share für jede Query

## 📋 Voraussetzungen

- Python 3.8 oder höher
- OpenAI API Key mit Zugriff auf GPT-5.1 (für AI-Kategorisierung)

## 🛠️ Installation

1. **Repository klonen oder Dateien herunterladen**

2. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

3. **Umgebungsvariablen einrichten:**

   **Option A: Für lokale Entwicklung** - Erstelle eine `.env` Datei im Hauptverzeichnis:
```env
OPENAI_API_KEY=dein-api-key-hier
OPENAI_MODEL=gpt-5.1
REASONING_EFFORT=high
```

   **Option B: Für Streamlit Cloud/GitHub Deployment** - Setze die Secrets direkt in Streamlit:
   - Gehe zu deiner Streamlit App → Settings → Secrets
   - Füge folgende Secrets hinzu:
   ```toml
   OPENAI_API_KEY = "dein-api-key-hier"
   OPENAI_MODEL = "gpt-5.1"
   REASONING_EFFORT = "high"
   ```
   
   **REASONING_EFFORT Optionen** (nur für GPT-5.1):
   - `none`: Kein zusätzliches Reasoning
   - `minimal`: Minimales Reasoning
   - `low`: Geringes Reasoning
   - `medium`: Mittleres Reasoning
   - `high`: Tiefes Reasoning (empfohlen für komplexe Kategorisierungen)
   
   **Hinweis:** Die App unterstützt beide Methoden automatisch. Für Deployment auf Streamlit Cloud reicht es, die Secrets in Streamlit zu setzen - keine `.env` Datei nötig!

4. **App starten:**
```bash
streamlit run app.py
```

Die App öffnet sich automatisch in deinem Browser unter `http://localhost:8501`

## 📖 Verwendung

### 1. Data Ingestion
- Navigiere zur "📤 Data Ingestion" Seite
- Lade eine oder mehrere CSV/XLSX Dateien hoch
- Die Daten werden automatisch bereinigt und standardisiert

### 2. AI Categorization
- Gehe zur "🤖 AI Categorization" Seite
- Klicke auf "🚀 Starte AI-Kategorisierung"
- Die KI kategorisiert alle Search Terms automatisch

### 3. Dashboard
- Auf der "📊 Dashboard" Seite findest du:
  - Opportunity Matrix für Revenue-Opportunities
  - Trend-Analysen
  - Share of Voice Tracking
  - Performance Heatmaps

### 4. Deep Dive Analytics
- Die "🔍 Deep Dive Analytics" Seite ermöglicht:
  - Filterung nach Kategorie, Search Term, Impressions
  - Detaillierte Performance-Metriken pro Query
  - Export der gefilterten Daten

## 🚀 Deployment auf Streamlit Cloud

1. **GitHub Repository erstellen** und Code pushen
2. **Streamlit Cloud** öffnen: https://share.streamlit.io
3. **New App** erstellen und Repository verbinden
4. **Secrets setzen**:
   - Gehe zu Settings → Secrets
   - Füge folgende Secrets hinzu:
   ```toml
   OPENAI_API_KEY = "dein-api-key-hier"
   OPENAI_MODEL = "gpt-5.1"
   REASONING_EFFORT = "high"
   ```
5. **Deploy** - Die App wird automatisch deployed!

**Wichtig:** Die Secrets werden sicher in Streamlit Cloud gespeichert und sind nicht im Code sichtbar.

## 🔐 Privacy & Security

- **Lokale Verarbeitung**: Alle Daten werden nur in deiner Browser-Session verarbeitet
- **Keine Speicherung**: Keine Daten werden auf dem Server gespeichert
- **API Calls**: Nur für AI-Kategorisierung werden Search Terms an die OpenAI API gesendet
- **Sichere Secrets**: API Keys werden über Streamlit Secrets verwaltet (nicht im Code)

## 🔮 Zukünftige Features

- [ ] Supabase Datenbank-Integration für persistente Speicherung
- [ ] Multi-User Support mit Authentifizierung
- [ ] Automatische Report-Generierung
- [ ] Email-Benachrichtigungen für neue Opportunities
- [ ] Historische Trend-Vergleiche über mehrere Perioden

## 📝 Projektstruktur

```
Search-Query-Performance-Analyzer/
├── app.py                 # Haupt-Streamlit-App
├── config.py              # Konfigurationsdatei
├── requirements.txt        # Python Dependencies
├── .env                   # Umgebungsvariablen (nicht im Repo)
├── README.md              # Diese Datei
└── utils/
    ├── data_processor.py  # Datenverarbeitungs-Engine
    ├── ai_categorizer.py  # AI-Kategorisierungs-Engine
    └── visualizations.py  # Visualisierungs-Engine
```

## 🐛 Troubleshooting

### OpenAI API Fehler
- Stelle sicher, dass dein API Key in der `.env` Datei korrekt gesetzt ist
- Überprüfe dein API-Kontingent bei OpenAI

### Datei-Upload Probleme
- Stelle sicher, dass die Datei ein gültiges Amazon SQP Report Format hat
- Überprüfe, ob die Datei nicht zu groß ist (empfohlen: < 50MB)

### Performance Probleme
- Bei großen Datensätzen: Reduziere die Batch Size für AI-Kategorisierung
- Verwende Filter auf der Deep Dive Seite für bessere Performance

## 📄 Lizenz

Dieses Projekt ist für den internen Unternehmensgebrauch bestimmt.

## 🤝 Support

Bei Fragen oder Problemen, kontaktiere das Entwicklungsteam.

---

**Erstellt mit ❤️ für bessere Amazon Performance Analyse**

