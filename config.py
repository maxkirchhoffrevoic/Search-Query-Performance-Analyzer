"""
Konfigurationsdatei für die Search Query Performance Analyzer App
Unterstützt sowohl Streamlit Secrets (für Deployment) als auch .env (für lokale Entwicklung)
"""
import os
from dotenv import load_dotenv

# Lade .env für lokale Entwicklung (wird in Streamlit Cloud ignoriert)
load_dotenv()

def get_secret(key: str, default: str = None):
    """
    Holt einen Secret-Wert, zuerst aus Streamlit Secrets, dann aus .env
    """
    try:
        import streamlit as st
        # Versuche Streamlit Secrets (für Deployment)
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except (ImportError, RuntimeError):
        # Streamlit nicht verfügbar oder nicht im Streamlit-Kontext
        pass
    
    # Fallback auf .env (für lokale Entwicklung)
    return os.getenv(key, default)

# OpenAI API Konfiguration
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
OPENAI_MODEL = get_secret("OPENAI_MODEL", "gpt-5.1")
REASONING_EFFORT = get_secret("REASONING_EFFORT", "high")  # none, minimal, low, medium, high

# Supabase Konfiguration (für später)
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

# App Konfiguration
APP_TITLE = "Amazon Search Query Performance Analyzer"
APP_ICON = "📊"

