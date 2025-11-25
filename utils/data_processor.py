"""
Data Processing Engine für Amazon SQP Reports
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import io


class DataProcessor:
    """Verarbeitet Amazon Search Query Performance Reports"""
    
    def __init__(self):
        self.processed_data = None
        self.raw_data = None
    
    def get_search_query_column(self, df: pd.DataFrame) -> str:
        """
        Gibt den Namen der Search Query/Term Spalte zurück
        
        Args:
            df: DataFrame
            
        Returns:
            str: Name der Search Query Spalte
        """
        if 'Search Query' in df.columns:
            return 'Search Query'
        elif 'Search Term' in df.columns:
            return 'Search Term'
        else:
            # Suche nach ähnlichen Spaltennamen
            for col in df.columns:
                if 'search' in col.lower() and ('query' in col.lower() or 'term' in col.lower()):
                    return col
            raise ValueError("Keine Search Query/Term Spalte gefunden")
    
    def load_file(self, uploaded_file) -> pd.DataFrame:
        """
        Lädt CSV oder XLSX Datei und gibt DataFrame zurück
        
        Args:
            uploaded_file: Streamlit UploadedFile Objekt
            
        Returns:
            pd.DataFrame: Geladene Daten
        """
        try:
            # Dateityp erkennen
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                # CSV mit verschiedenen Encodings versuchen
                # Amazon Reports haben oft eine Metadaten-Zeile am Anfang (z.B. Brand=, Reporting range=)
                # Die zweite Zeile ist dann der Header
                try:
                    # Versuche zuerst UTF-8
                    uploaded_file.seek(0)
                    # Prüfe erste Zeile auf Metadaten
                    first_bytes = uploaded_file.read(200)
                    uploaded_file.seek(0)
                    first_line = first_bytes.decode('utf-8', errors='ignore').split('\n')[0]
                    
                    skip_rows = 1 if ('Brand=' in first_line or 'Reporting range' in first_line) else 0
                    df = pd.read_csv(uploaded_file, encoding='utf-8', skiprows=skip_rows)
                except (UnicodeDecodeError, UnicodeError):
                    # Fallback auf latin-1
                    uploaded_file.seek(0)
                    first_bytes = uploaded_file.read(200)
                    uploaded_file.seek(0)
                    first_line = first_bytes.decode('latin-1', errors='ignore').split('\n')[0]
                    
                    skip_rows = 1 if ('Brand=' in first_line or 'Reporting range' in first_line) else 0
                    df = pd.read_csv(uploaded_file, encoding='latin-1', skiprows=skip_rows)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file, engine='openpyxl', skiprows=1)
            else:
                raise ValueError(f"Nicht unterstützter Dateityp: {file_extension}")
            
            self.raw_data = df
            return df
            
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Datei: {str(e)}")
    
    def load_multiple_files(self, uploaded_files: List) -> pd.DataFrame:
        """
        Lädt mehrere Dateien und kombiniert sie
        
        Args:
            uploaded_files: Liste von Streamlit UploadedFile Objekten
            
        Returns:
            pd.DataFrame: Kombinierte Daten
        """
        dataframes = []
        
        for file in uploaded_files:
            df = self.load_file(file)
            dataframes.append(df)
        
        # Alle DataFrames kombinieren
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        # Duplikate entfernen (basierend auf Search Query + Datum falls vorhanden)
        search_col = 'Search Query' if 'Search Query' in combined_df.columns else 'Search Term'
        if search_col in combined_df.columns:
            combined_df = combined_df.drop_duplicates(
                subset=[search_col], 
                keep='last'
            )
        
        self.raw_data = combined_df
        return combined_df
    
    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardisiert Spaltennamen für Amazon SQP Reports
        
        Args:
            df: DataFrame mit möglicherweise unterschiedlichen Spaltennamen
            
        Returns:
            pd.DataFrame: DataFrame mit standardisierten Spaltennamen
        """
        # Mapping für häufige Spaltennamen-Varianten (Amazon SQP Report Format)
        column_mapping = {
            'Search Query': ['Search Query', 'Search Term', 'search_query', 'search_term', 'Query', 'query'],
            'Impressions': ['Impressions: Total Count', 'Impressions', 'impressions', 'Impr.', 'Impr'],
            'Clicks': ['Clicks: Total Count', 'Clicks', 'clicks', 'Click', 'click'],
            'CTR': ['Clicks: Click Rate %', 'CTR', 'ctr', 'Click-Through Rate', 'Click Rate'],
            'Orders': ['Purchases: Total Count', 'Orders', 'orders', 'Order', 'order', 'Total Orders', 'Purchases'],
            'Sales': ['Sales', 'sales', 'Revenue', 'revenue', 'Total Sales'],
            'Purchase Price': ['Purchases: Price (Median)', 'Purchase Price', 'Price'],
            'Conversion Rate': ['Purchases: Purchase Rate %', 'Conversion Rate', 'conversion_rate', 'CVR', 'cvr', 'Conv. Rate', 'Purchase Rate'],
            # Brand-spezifische Spalten
            'Brand Impressions': ['Impressions: Brand Count'],
            'Brand Clicks': ['Clicks: Brand Count'],
            'Brand Orders': ['Purchases: Brand Count'],
            'Brand Share %': ['Impressions: Brand Share %'],
            'Search Query Volume': ['Search Query Volume'],
            'Search Query Score': ['Search Query Score'],
        }
        
        standardized_df = df.copy()
        
        # Spaltennamen normalisieren
        for standard_name, variants in column_mapping.items():
            for variant in variants:
                if variant in standardized_df.columns and standard_name not in standardized_df.columns:
                    standardized_df.rename(columns={variant: standard_name}, inplace=True)
        
        return standardized_df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Bereinigt und bereitet Daten für die Analyse vor
        
        Args:
            df: DataFrame mit rohen Daten
            
        Returns:
            pd.DataFrame: Bereinigte Daten
        """
        df = self.standardize_columns(df)
        
        # Numerische Spalten bereinigen
        numeric_columns = ['Impressions', 'Clicks', 'Orders', 'Sales', 'CTR', 'Conversion Rate']
        
        for col in numeric_columns:
            if col in df.columns:
                # Entferne nicht-numerische Zeichen und konvertiere
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
        
        # NaN Werte in numerischen Spalten mit 0 ersetzen
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # Berechne zusätzliche Metriken falls nicht vorhanden
        if 'CTR' not in df.columns and 'Clicks' in df.columns and 'Impressions' in df.columns:
            df['CTR'] = (df['Clicks'] / df['Impressions'].replace(0, np.nan) * 100).fillna(0)
        
        # Conversion Rate berechnen (Orders/Purchases zu Clicks)
        if 'Conversion Rate' not in df.columns:
            if 'Orders' in df.columns and 'Clicks' in df.columns:
                df['Conversion Rate'] = (df['Orders'] / df['Clicks'].replace(0, np.nan) * 100).fillna(0)
            elif 'Purchases: Total Count' in df.columns and 'Clicks' in df.columns:
                df['Conversion Rate'] = (df['Purchases: Total Count'] / df['Clicks'].replace(0, np.nan) * 100).fillna(0)
        
        # Standardisiere Orders Spalte (kann Purchases: Total Count sein)
        if 'Orders' not in df.columns and 'Purchases: Total Count' in df.columns:
            df['Orders'] = df['Purchases: Total Count']
        
        # Berechne Sales aus Purchases * Price falls Sales nicht vorhanden
        if 'Sales' not in df.columns or (df['Sales'].sum() == 0 if 'Sales' in df.columns else True):
            sales_calculated = False
            # Versuche verschiedene Kombinationen
            if 'Orders' in df.columns and 'Purchase Price' in df.columns:
                df['Sales'] = (df['Orders'].fillna(0) * df['Purchase Price'].fillna(0)).round(2)
                sales_calculated = True
            elif 'Orders' in df.columns and 'Purchases: Price (Median)' in df.columns:
                df['Sales'] = (df['Orders'].fillna(0) * df['Purchases: Price (Median)'].fillna(0)).round(2)
                sales_calculated = True
            elif 'Purchases: Total Count' in df.columns and 'Purchases: Price (Median)' in df.columns:
                df['Sales'] = (df['Purchases: Total Count'].fillna(0) * df['Purchases: Price (Median)'].fillna(0)).round(2)
                if 'Orders' not in df.columns:
                    df['Orders'] = df['Purchases: Total Count']
                sales_calculated = True
            
            # Falls keine Sales berechnet werden konnten, setze auf 0
            if not sales_calculated:
                df['Sales'] = 0
        
        # Berechne Market Share (falls Sales vorhanden)
        if 'Sales' in df.columns:
            total_sales = df['Sales'].sum()
            if total_sales > 0:
                df['Market Share %'] = (df['Sales'] / total_sales * 100).round(2)
            else:
                df['Market Share %'] = 0
        
        self.processed_data = df
        return df
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """
        Berechnet Zusammenfassungsstatistiken
        
        Args:
            df: DataFrame mit verarbeiteten Daten
            
        Returns:
            Dict: Dictionary mit Statistiken
        """
        stats = {
            'total_queries': len(df),
            'total_impressions': df['Impressions'].sum() if 'Impressions' in df.columns else 0,
            'total_clicks': df['Clicks'].sum() if 'Clicks' in df.columns else 0,
            'total_orders': df['Orders'].sum() if 'Orders' in df.columns else 0,
            'total_sales': df['Sales'].sum() if 'Sales' in df.columns else 0,
            'avg_ctr': df['CTR'].mean() if 'CTR' in df.columns else 0,
            'avg_conversion_rate': df['Conversion Rate'].mean() if 'Conversion Rate' in df.columns else 0,
        }
        
        return stats

