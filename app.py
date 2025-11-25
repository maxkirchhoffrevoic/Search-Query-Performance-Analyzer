"""
Amazon Search Query Performance Analyzer
Streamlit Haupt-App - Alle Sections auf einer Seite
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_processor import DataProcessor
from utils.ai_categorizer import AICategorizer
from utils.visualizations import VisualizationEngine
from config import APP_TITLE, APP_ICON
import time


# Page Config
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'all_processed_data' not in st.session_state:
    st.session_state.all_processed_data = []  # Liste aller hochgeladenen Datensätze
if 'categorized_data' not in st.session_state:
    st.session_state.categorized_data = None
if 'categories' not in st.session_state:
    st.session_state.categories = None
if 'processor' not in st.session_state:
    st.session_state.processor = DataProcessor()
if 'categorizer' not in st.session_state:
    st.session_state.categorizer = AICategorizer()
if 'viz_engine' not in st.session_state:
    st.session_state.viz_engine = VisualizationEngine()

# Header
st.markdown(f'<div class="main-header">{APP_ICON} {APP_TITLE}</div>', unsafe_allow_html=True)

st.info("""
**Privacy First**: Alle Daten werden nur in deiner Browser-Session verarbeitet.
Keine Daten werden gespeichert oder an externe Server gesendet (außer ChatGPT API für Kategorisierung).
""")

# ============================================================================
# SECTION 1: DATA INGESTION
# ============================================================================
st.header("📤 Smart Ingestion Engine")

st.markdown("""
### Drag & Drop Upload
Lade deine Amazon Search Query Performance Reports hoch (.csv oder .xlsx).

**Mehrere Monate kombinieren**: Du kannst alle monatlichen Reports auf einmal auswählen und hochladen - sie werden automatisch kombiniert!
""")

# Button zum Zurücksetzen aller Daten
if st.session_state.processed_data is not None:
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Alle Daten zurücksetzen", type="secondary"):
            st.session_state.all_processed_data = []
            st.session_state.processed_data = None
            st.session_state.categorized_data = None
            st.rerun()

uploaded_files = st.file_uploader(
    "Wähle Dateien aus",
    type=['csv', 'xlsx', 'xls'],
    accept_multiple_files=True,
    help="Unterstützt CSV und Excel Dateien"
)

if uploaded_files:
    with st.spinner("Verarbeite Dateien..."):
        try:
            # Lade alle Dateien (einzeln oder mehrere auf einmal)
            if len(uploaded_files) == 1:
                df = st.session_state.processor.load_file(uploaded_files[0])
                st.success(f"✅ Datei geladen: {uploaded_files[0].name}")
            else:
                df = st.session_state.processor.load_multiple_files(uploaded_files)
                st.success(f"✅ {len(uploaded_files)} Dateien geladen und kombiniert")
            
            # Daten bereinigen
            df_cleaned = st.session_state.processor.clean_data(df)
            
            # Kombiniere mit bereits vorhandenen Daten (falls vorhanden)
            if st.session_state.processed_data is not None:
                # Kombiniere neue Daten mit bestehenden
                df_combined = pd.concat([st.session_state.processed_data, df_cleaned], ignore_index=True)
                # Entferne Duplikate basierend auf Search Query + Month
                search_col = 'Search Query' if 'Search Query' in df_combined.columns else 'Search Term'
                if 'Month' in df_combined.columns and search_col in df_combined.columns:
                    df_combined = df_combined.drop_duplicates(subset=[search_col, 'Month'], keep='last')
                elif search_col in df_combined.columns:
                    df_combined = df_combined.drop_duplicates(subset=[search_col], keep='last')
                st.session_state.processed_data = df_combined
                st.info(f"📊 Neue Daten hinzugefügt. Total: {len(df_combined)} Zeilen aus allen hochgeladenen Reports")
            else:
                st.session_state.processed_data = df_cleaned
            
            # Zeige Zusammenfassung
            st.subheader("📈 Datenübersicht")
            stats = st.session_state.processor.get_summary_stats(df_cleaned)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Queries", f"{stats['total_queries']:,}")
            with col2:
                st.metric("Total Impressions", f"{stats['total_impressions']:,.0f}")
            with col3:
                st.metric("Total Orders", f"{stats['total_orders']:,}")
            with col4:
                st.metric("Total Sales", f"€{stats['total_sales']:,.2f}")
            
            # Zeige Vorschau
            st.subheader("👀 Datenvorschau")
            st.dataframe(st.session_state.processed_data.head(20), use_container_width=True)
            
            # Monatliche Trend-Analyse
            if 'Month' in st.session_state.processed_data.columns or 'Reporting Date' in st.session_state.processed_data.columns:
                st.subheader("📅 Monatliche Trend-Analyse")
                try:
                    # Prüfe ob Methode existiert
                    if hasattr(st.session_state.viz_engine, 'create_monthly_trends'):
                        fig_monthly = st.session_state.viz_engine.create_monthly_trends(
                            st.session_state.processed_data,
                            date_col='Month' if 'Month' in st.session_state.processed_data.columns else None
                        )
                        st.plotly_chart(fig_monthly, use_container_width=True)
                    else:
                        st.warning("⚠️ Methode create_monthly_trends nicht gefunden. Bitte App neu starten.")
                except Exception as e:
                    st.warning(f"⚠️ Monatliche Trend-Analyse konnte nicht erstellt werden: {e}")
                    st.exception(e)
            
            # Download Option
            csv = df_cleaned.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Bereinigte Daten als CSV herunterladen",
                data=csv,
                file_name="cleaned_sqp_data.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"❌ Fehler beim Verarbeiten der Dateien: {str(e)}")
            st.exception(e)

st.divider()

# ============================================================================
# SECTION 2: AI CATEGORIZATION
# ============================================================================
st.header("🤖 AI-Powered Categorization")

if st.session_state.processed_data is None:
    st.warning("⚠️ Bitte lade zuerst Daten hoch.")
else:
    df = st.session_state.processed_data
    
    st.markdown("""
    ### Automatische Kategorisierung
    Die KI kategorisiert automatisch alle Search Queries in logische Produktkategorien.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"📊 {len(df)} Search Queries bereit zur Kategorisierung")
    
    with col2:
        # Modell-Auswahl
        model_choice = st.selectbox(
            "AI-Modell",
            ["gpt-4-turbo-preview", "gpt-5.1"],
            index=1 if "gpt-5" in st.session_state.categorizer.model.lower() else 0,
            help="GPT-4 Turbo: Schneller & günstiger. GPT-5.1: Präziser durch Reasoning."
        )
        
        # Reasoning Effort nur für GPT-5.1
        if "gpt-5" in model_choice.lower():
            reasoning_effort = st.selectbox(
                "Reasoning Effort",
                ["low", "medium", "high"],
                index=2,
                help="Höher = präziser aber langsamer"
            )
        else:
            reasoning_effort = None
        
        batch_size = st.number_input("Batch Size", min_value=20, max_value=200, value=100, step=10, help="Größere Batches = schneller, aber mehr Tokens")
        parallel_processing = st.checkbox("Parallele Verarbeitung", value=True, help="Mehrere Batches gleichzeitig verarbeiten (schneller)")
        max_workers = st.slider("Max. parallele Requests", min_value=1, max_value=5, value=3, help="Mehr = schneller, aber mehr API-Calls gleichzeitig")
    
    # Debug: Zeige verfügbare Spalten
    with st.expander("🔍 Debug: Verfügbare Spalten"):
        st.write("Spalten im DataFrame:", list(df.columns))
        st.write("Hat 'Search Query':", 'Search Query' in df.columns)
        st.write("Hat 'Search Term':", 'Search Term' in df.columns)
        if 'Search Query' in df.columns:
            st.write("Beispiel Search Query:", df['Search Query'].iloc[0] if len(df) > 0 else "Keine Daten")
    
    if st.button("🚀 Starte AI-Kategorisierung", type="primary"):
        # Aktualisiere Modell falls geändert
        if model_choice != st.session_state.categorizer.model:
            st.session_state.categorizer.model = model_choice
            if reasoning_effort:
                st.session_state.categorizer.reasoning_effort = reasoning_effort
        
        # Finde die richtige Search Query Spalte
        search_col = None
        if 'Search Query' in df.columns:
            search_col = 'Search Query'
            st.info(f"✅ Verwende Spalte: 'Search Query'")
        elif 'Search Term' in df.columns:
            search_col = 'Search Term'
            st.info(f"✅ Verwende Spalte: 'Search Term'")
        else:
            st.error("❌ 'Search Query' oder 'Search Term' Spalte nicht gefunden in den Daten.")
            st.write("Verfügbare Spalten:", list(df.columns))
            st.stop()
        
        st.info(f"🤖 Verwende Modell: {model_choice}" + (f" (Reasoning: {reasoning_effort})" if reasoning_effort else ""))
        
        with st.spinner("🤖 KI kategorisiert Search Queries... Das kann einen Moment dauern."):
            try:
                search_terms = df[search_col].unique().tolist()
                st.info(f"📊 Gefunden: {len(search_terms)} einzigartige Search Queries")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Prüfe ob bereits Kategorien vorhanden sind (Caching)
                existing_categories = {}
                new_search_terms = []
                
                if st.session_state.categories:
                    existing_categories = st.session_state.categories
                    new_search_terms = [term for term in search_terms if term not in existing_categories]
                    cached_count = len(search_terms) - len(new_search_terms)
                    if cached_count > 0:
                        status_text.text(f"📦 {cached_count} bereits kategorisiert, {len(new_search_terms)} neu zu kategorisieren...")
                        progress_bar.progress(cached_count / len(search_terms))
                else:
                    new_search_terms = search_terms
                
                # Kategorisiere nur neue Search Terms
                if new_search_terms:
                    status_text.text(f"🔄 Kategorisiere {len(new_search_terms)} neue Search Queries...")
                    new_categories = st.session_state.categorizer.categorize_search_terms(
                        new_search_terms,
                        batch_size=batch_size,
                        parallel=parallel_processing,
                        max_workers=max_workers
                    )
                    all_categories = {**existing_categories, **new_categories}
                else:
                    all_categories = existing_categories
                    status_text.text("✅ Alle Search Queries bereits kategorisiert!")
                
                # Update Progress
                progress_bar.progress(1.0)
                status_text.text("✅ Kategorisierung abgeschlossen!")
                
                # Debug: Zeige Kategorisierungs-Ergebnisse
                st.write(f"📊 Kategorien erhalten: {len(all_categories)}")
                if len(all_categories) > 0:
                    # Zeige erste 5 Kategorien als Beispiel
                    sample_categories = dict(list(all_categories.items())[:5])
                    st.json(sample_categories)
                
                # Füge Kategorien zu DataFrame hinzu
                df['Category'] = df[search_col].map(all_categories).fillna('Uncategorized')
                
                # Debug: Zeige wie viele Uncategorized sind
                uncategorized_count = (df['Category'] == 'Uncategorized').sum()
                if uncategorized_count > 0:
                    st.warning(f"⚠️ {uncategorized_count} Search Queries wurden als 'Uncategorized' markiert")
                
                st.session_state.categorized_data = df
                st.session_state.categories = all_categories
                
                progress_bar.empty()
                status_text.empty()
                
                st.success(f"✅ {len(search_terms)} Search Queries kategorisiert!")
                st.rerun()  # Aktualisiere die Seite um Kategorien anzuzeigen
                
            except Exception as e:
                st.error(f"❌ Fehler bei der Kategorisierung: {str(e)}")
                st.exception(e)
                # Zeige Debug-Informationen
                with st.expander("🔍 Debug-Informationen"):
                    debug_info = {
                        "Fehler": str(e),
                        "Modell": st.session_state.categorizer.model if hasattr(st.session_state.categorizer, 'model') else 'N/A',
                        "API Key vorhanden": bool(st.session_state.categorizer.client) if hasattr(st.session_state.categorizer, 'client') else False,
                        "Verwendete Spalte": search_col if 'search_col' in locals() else 'N/A',
                        "Anzahl Search Queries": len(search_terms) if 'search_terms' in locals() else 0,
                        "Anzahl Kategorien erhalten": len(all_categories) if 'all_categories' in locals() else 0
                    }
                    st.json(debug_info)
                    
                    if 'all_categories' in locals() and len(all_categories) > 0:
                        st.write("**Erste 10 Kategorien:**")
                        st.json(dict(list(all_categories.items())[:10]))
    
    # Zeige Kategorien-Übersicht
    if st.session_state.categorized_data is not None:
        st.subheader("📊 Kategorien-Übersicht")
        df_cat = st.session_state.categorized_data
        
        if 'Category' in df_cat.columns:
            category_counts = df_cat['Category'].value_counts().reset_index()
            category_counts.columns = ['Category', 'Count']
            category_counts = category_counts.head(20)  # Beschränke auf Top 20 Kategorien
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(category_counts, use_container_width=True)
            
            with col2:
                fig = go.Figure(data=[go.Pie(
                    labels=category_counts['Category'],
                    values=category_counts['Count'],
                    hole=0.3
                )])
                fig.update_layout(title="Kategorien-Verteilung", height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Download kategorisierte Daten
            csv = df_cat.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Kategorisierte Daten herunterladen",
                data=csv,
                file_name="categorized_sqp_data.csv",
                mime="text/csv"
            )

st.divider()

# ============================================================================
# SECTION 3: DASHBOARD
# ============================================================================
st.header("📊 Visual Intelligence Dashboard")

if st.session_state.categorized_data is None:
    st.warning("⚠️ Bitte führe zuerst die AI-Kategorisierung durch.")
else:
    df = st.session_state.categorized_data
    
    # Prüfe ob Category Spalte existiert
    if 'Category' not in df.columns:
        st.error("❌ Keine Kategorien gefunden. Bitte führe zuerst die AI-Kategorisierung durch.")
    else:
        # Opportunity Matrix
        st.subheader("🎯 Opportunity Matrix")
        st.markdown("""
        Diese Grafik kombiniert drei Perspektiven auf einen Blick:
        * **X-Achse (Market Volume)** zeigt, wie viele Impressions bzw. Suchanfragen in einer Kategorie anfallen.
        * **Y-Achse (Market Share)** zeigt deinen Anteil an den Sales in dieser Kategorie.
        * **Bubble-Größe & Farbe** repräsentieren deine absoluten Sales.
        
        Interpretation: Kategorien rechts oben sind bereits stark (hohes Volumen, hoher Marktanteil). Spannend für Wachstum sind vor allem Kategorien weit rechts, aber mit niedrigem Market Share – hier existiert viel Nachfrage, aber dein Anteil ist noch gering.
        """)
        
        try:
            # Bereite Daten für Opportunity Matrix vor
            search_col = 'Search Query' if 'Search Query' in df.columns else 'Search Term'
            category_stats = df.groupby('Category').agg({
                'Impressions': 'sum',
                'Sales': 'sum',
                search_col: 'count'
            }).reset_index()
            category_stats.columns = ['Category', 'Total Impressions', 'Total Sales', 'Query Count']
            
            total_sales = category_stats['Total Sales'].sum()
            if total_sales > 0:
                category_stats['Market Share %'] = (
                    category_stats['Total Sales'] / total_sales * 100
                ).round(2)
            else:
                category_stats['Market Share %'] = 0
            
            fig_opportunity = st.session_state.viz_engine.create_opportunity_matrix(
                category_stats,
                category_col='Category',
                volume_col='Total Impressions',
                share_col='Market Share %',
                sales_col='Total Sales'
            )
            st.plotly_chart(fig_opportunity, use_container_width=True)
            
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Opportunity Matrix: {e}")
            st.exception(e)
        
        st.divider()
        
        # Market Trend Analysis
        st.subheader("📈 Market Trend Analysis")
        st.markdown("""
        Diese Dual-Achsen-Linie zeigt pro Zeitraum oder Kategorie sowohl das **Gesamtvolumen (Impressions)** als auch deine **Sales Velocity**.
        * Die blaue Linie misst, wie sich das Marktvolumen entwickelt – wächst die Kategorie oder schrumpft sie?
        * Die orange Linie zeigt, ob deine eigenen Sales Schritt halten, schneller wachsen oder zurückfallen.
        
        Ein Auseinanderlaufen der Linien bedeutet: Das Marktvolumen entwickelt sich anders als dein Sales-Anteil. So erkennst du frühzeitig, wo du Marktanteile verlierst oder gewinnst.
        """)
        
        try:
            fig_trend = st.session_state.viz_engine.create_trend_analysis(df)
            st.plotly_chart(fig_trend, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Trend-Analyse: {e}")
        
        st.divider()
        
        # Share of Voice
        st.subheader("🎤 Share of Voice Tracking")
        st.markdown("""
        Der Share-of-Voice-Chart vergleicht pro Kategorie zwei Kennzahlen:
        * **Impression Share %** – wie häufig wirst du angezeigt im Vergleich zum gesamten Markt?
        * **Sales Share %** – wie viel Umsatz generierst du relativ zum Gesamtumsatz der Kategorie?
        
        Wenn der Impression Share deutlich höher ist als der Sales Share, gewinnst du zwar Sichtbarkeit, konvertierst aber nicht entsprechend. Umgekehrt deutet ein höherer Sales Share darauf hin, dass deine Listings sehr effizient verkaufen. Ideal ist ein ausgewogenes Verhältnis.
        """)
        
        try:
            fig_sov = st.session_state.viz_engine.create_share_of_voice(df)
            st.plotly_chart(fig_sov, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Share of Voice Analyse: {e}")
        
        st.divider()
        
        # Performance Heatmap
        st.subheader("🔥 Performance Heatmap")
        st.markdown("""
        Die Heatmap zeigt für jede Kategorie den Durchschnittswert der ausgewählten Metrik (z. B. CTR, Conversion Rate, Sales). 
        * **Warme Farben** (rot/gelb) stehen für überdurchschnittliche Performance.
        * **Kühle Farben** (grün/blau) weisen auf Potenzial oder Problembereiche hin.
        
        So erkennst du sofort, welche Kategorien bei der gewählten Kennzahl herausragen und welche optimiert werden sollten.
        """)
        
        metric_option = st.selectbox(
            "Wähle Metrik",
            ['CTR', 'Conversion Rate', 'Sales', 'Impressions'],
            key='heatmap_metric'
        )
        
        try:
            fig_heatmap = st.session_state.viz_engine.create_performance_heatmap(
                df,
                category_col='Category',
                metric_col=metric_option
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Heatmap: {e}")

st.divider()

# ============================================================================
# SECTION 4: DEEP DIVE ANALYTICS
# ============================================================================
st.header("🔍 Deep Dive Analytics")

if st.session_state.categorized_data is None:
    st.warning("⚠️ Bitte führe zuerst die AI-Kategorisierung durch.")
else:
    df = st.session_state.categorized_data
    
    if 'Category' not in df.columns:
        st.error("❌ Keine Kategorien gefunden. Bitte führe zuerst die AI-Kategorisierung durch.")
    else:
        # Filter-Optionen
        st.subheader("🔎 Filter & Suche")
        st.markdown("""
        In der Deep-Dive-Section kannst du jede Kategorie oder einen einzelnen Suchbegriff detailliert analysieren. 
        * Nutze die Filter (Kategorie, Suchtext, minimale Impressions), um den Datensatz einzugrenzen.
        * Sortiere nach der gewünschten Kennzahl, um Top-Performer oder Ausreißer zu finden.
        * Die Kennzahlen am Kopf zeigen die aggregierten Werte für deine aktuelle Auswahl.
        
        Ideal für Ad-hoc-Analysen, wenn du konkrete Optimierungsmöglichkeiten pro Suchbegriff identifizieren willst.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categories = ['Alle'] + df['Category'].unique().tolist()
            selected_category = st.selectbox("Kategorie", categories)
        
        with col2:
            search_term_filter = st.text_input("Search Query suchen", "")
        
        with col3:
            min_impressions = st.number_input("Min. Impressions", min_value=0, value=0, step=100)
        
        # Filter anwenden
        df_filtered = df.copy()
        
        if selected_category != 'Alle':
            df_filtered = df_filtered[df_filtered['Category'] == selected_category]
        
        if search_term_filter:
            search_col = 'Search Query' if 'Search Query' in df_filtered.columns else 'Search Term'
            if search_col in df_filtered.columns:
                df_filtered = df_filtered[
                    df_filtered[search_col].str.contains(search_term_filter, case=False, na=False)
                ]
        
        if min_impressions > 0:
            df_filtered = df_filtered[df_filtered['Impressions'] >= min_impressions]
        
        st.info(f"📊 {len(df_filtered)} Search Queries gefunden")
        
        # Sortierung
        sort_by = st.selectbox(
            "Sortiere nach",
            ['Impressions', 'Sales', 'Orders', 'CTR', 'Conversion Rate'],
            index=0
        )
        sort_order = st.radio("Reihenfolge", ["Absteigend", "Aufsteigend"], horizontal=True)
        
        ascending = sort_order == "Aufsteigend"
        df_filtered = df_filtered.sort_values(sort_by, ascending=ascending)
        
        # Zeige Ergebnisse
        st.subheader("📋 Search Query Details")
        
        # Wichtige Metriken
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Volume", f"{df_filtered['Impressions'].sum():,.0f}")
        with col2:
            st.metric("Total Sales", f"€{df_filtered['Sales'].sum():,.2f}")
        with col3:
            st.metric("Total Orders", f"{df_filtered['Orders'].sum():,.0f}")
        with col4:
            st.metric("Avg CTR", f"{df_filtered['CTR'].mean():.2f}%")
        with col5:
            st.metric("Avg CVR", f"{df_filtered['Conversion Rate'].mean():.2f}%")
        
        # Daten-Tabelle
        search_col = 'Search Query' if 'Search Query' in df_filtered.columns else 'Search Term'
        display_cols = [search_col, 'Category', 'Impressions', 'Clicks', 'CTR', 
                       'Orders', 'Sales', 'Conversion Rate']
        available_cols = [col for col in display_cols if col in df_filtered.columns]
        
        st.dataframe(
            df_filtered[available_cols],
            use_container_width=True,
            height=400
        )
        
        # Download
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Gefilterte Daten herunterladen",
            data=csv,
            file_name="filtered_sqp_data.csv",
            mime="text/csv"
        )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Amazon Search Query Performance Analyzer | Privacy First | Powered by ChatGPT</p>
</div>
""", unsafe_allow_html=True)
