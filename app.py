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
Du kannst auch mehrere Dateien gleichzeitig hochladen für Batch Processing.
""")

uploaded_files = st.file_uploader(
    "Wähle Dateien aus",
    type=['csv', 'xlsx', 'xls'],
    accept_multiple_files=True,
    help="Unterstützt CSV und Excel Dateien"
)

if uploaded_files:
    with st.spinner("Verarbeite Dateien..."):
        try:
            if len(uploaded_files) == 1:
                df = st.session_state.processor.load_file(uploaded_files[0])
                st.success(f"✅ Datei geladen: {uploaded_files[0].name}")
            else:
                df = st.session_state.processor.load_multiple_files(uploaded_files)
                st.success(f"✅ {len(uploaded_files)} Dateien geladen und kombiniert")
            
            # Daten bereinigen
            df_cleaned = st.session_state.processor.clean_data(df)
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
            st.dataframe(df_cleaned.head(20), use_container_width=True)
            
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
        batch_size = st.number_input("Batch Size", min_value=10, max_value=100, value=50, step=10)
    
    if st.button("🚀 Starte AI-Kategorisierung", type="primary"):
        # Finde die richtige Search Query Spalte
        search_col = None
        if 'Search Query' in df.columns:
            search_col = 'Search Query'
        elif 'Search Term' in df.columns:
            search_col = 'Search Term'
        else:
            st.error("❌ 'Search Query' oder 'Search Term' Spalte nicht gefunden in den Daten.")
            st.stop()
        
        with st.spinner("🤖 KI kategorisiert Search Queries... Das kann einen Moment dauern."):
            try:
                search_terms = df[search_col].unique().tolist()
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Kategorisiere in Batches
                all_categories = {}
                total_batches = (len(search_terms) + batch_size - 1) // batch_size
                
                for i in range(0, len(search_terms), batch_size):
                    batch = search_terms[i:i+batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    status_text.text(f"Verarbeite Batch {batch_num}/{total_batches}...")
                    batch_categories = st.session_state.categorizer._categorize_batch(batch)
                    all_categories.update(batch_categories)
                    
                    progress = min((i + batch_size) / len(search_terms), 1.0)
                    progress_bar.progress(progress)
                    
                    time.sleep(0.5)  # Rate limiting
                
                # Füge Kategorien zu DataFrame hinzu
                df['Category'] = df[search_col].map(all_categories).fillna('Uncategorized')
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
                    st.code(f"""
Fehler: {str(e)}
Modell: {st.session_state.categorizer.model if hasattr(st.session_state.categorizer, 'model') else 'N/A'}
API Key vorhanden: {bool(st.session_state.categorizer.client) if hasattr(st.session_state.categorizer, 'client') else False}
                    """)
    
    # Zeige Kategorien-Übersicht
    if st.session_state.categorized_data is not None:
        st.subheader("📊 Kategorien-Übersicht")
        df_cat = st.session_state.categorized_data
        
        if 'Category' in df_cat.columns:
            category_counts = df_cat['Category'].value_counts().reset_index()
            category_counts.columns = ['Category', 'Count']
            
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
        **High Volume vs. Low Market Share**: Identifiziere ungenutzte Revenue-Opportunities.
        Große Bubbles = Hohe Sales, Position zeigt Volume vs. Market Share.
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
        
        try:
            fig_trend = st.session_state.viz_engine.create_trend_analysis(df)
            st.plotly_chart(fig_trend, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Trend-Analyse: {e}")
        
        st.divider()
        
        # Share of Voice
        st.subheader("🎤 Share of Voice Tracking")
        st.markdown("""
        **Brand Share**: Vergleiche deinen Impression Share vs. Sales Share pro Kategorie.
        """)
        
        try:
            fig_sov = st.session_state.viz_engine.create_share_of_voice(df)
            st.plotly_chart(fig_sov, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Share of Voice Analyse: {e}")
        
        st.divider()
        
        # Performance Heatmap
        st.subheader("🔥 Performance Heatmap")
        
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
