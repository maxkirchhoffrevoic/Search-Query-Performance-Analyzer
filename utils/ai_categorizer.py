"""
AI-Powered Categorization Engine mit ChatGPT API
"""
import openai
from typing import List, Dict, Optional
import pandas as pd
from config import OPENAI_API_KEY, OPENAI_MODEL, REASONING_EFFORT
import json
import time


class AICategorizer:
    """Kategorisiert Search Terms mit Hilfe von ChatGPT"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    
    def categorize_search_terms(
        self, 
        search_terms: List[str], 
        batch_size: int = 50
    ) -> Dict[str, str]:
        """
        Kategorisiert eine Liste von Search Terms
        
        Args:
            search_terms: Liste von Search Terms
            batch_size: Anzahl der Terms pro Batch
            
        Returns:
            Dict: Mapping von Search Term zu Kategorie
        """
        if not self.client:
            raise ValueError("OpenAI API Key nicht konfiguriert. Bitte in .env Datei setzen.")
        
        categorization = {}
        
        # Verarbeite in Batches
        for i in range(0, len(search_terms), batch_size):
            batch = search_terms[i:i+batch_size]
            batch_categories = self._categorize_batch(batch)
            categorization.update(batch_categories)
            time.sleep(0.5)  # Rate limiting
        
        return categorization
    
    def _categorize_batch(self, search_terms: List[str]) -> Dict[str, str]:
        """
        Kategorisiert einen Batch von Search Terms
        
        Args:
            search_terms: Liste von Search Terms (max batch_size)
            
        Returns:
            Dict: Mapping von Search Term zu Kategorie
        """
        prompt = f"""Du bist ein Experte für Amazon-Produktkategorisierung. 
Kategorisiere die folgenden Amazon-Suchbegriffe in logische Produktkategorien.

Wichtige Regeln:
1. Gruppiere ähnliche Begriffe in die gleiche Kategorie (z.B. "Bento Box", "Bento Lunchbox" → "Bento")
2. Unterscheide zwischen "Generic" (allgemeine Suchbegriffe) und "Branded" (Marken-spezifische Begriffe)
3. Verwende präzise, beschreibende Kategorienamen (z.B. "Isothermal Bags", "Lunchbox", "Food Container")
4. Wenn ein Begriff zu einer Marke gehört, kategorisiere ihn als "Branded: [Markenname]"

Suchbegriffe:
{json.dumps(search_terms, ensure_ascii=False, indent=2)}

Antworte mit einem JSON-Objekt, das jeden Suchbegriff als Key und die entsprechende Kategorie als Value enthält.
Format: {{"Suchbegriff 1": "Kategorie 1", "Suchbegriff 2": "Kategorie 2", ...}}"""

        try:
            # API-Parameter für GPT-5.1 Thinking
            api_params = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "Du bist ein Experte für Produktkategorisierung. Antworte immer nur mit gültigem JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"}
            }
            
            # Füge reasoning_effort hinzu, wenn GPT-5.1 verwendet wird
            if "gpt-5" in OPENAI_MODEL.lower():
                api_params["reasoning_effort"] = REASONING_EFFORT
            
            response = self.client.chat.completions.create(**api_params)
            
            result_text = response.choices[0].message.content.strip()
            
            # Mit response_format={"type": "json_object"} sollte die Antwort bereits valides JSON sein
            # Aber für Sicherheit entfernen wir trotzdem mögliche Markdown-Code-Blöcke
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # Parse JSON
            categories = json.loads(result_text)
            
            return categories
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response was: {result_text}")
            # Fallback: Einfache Kategorisierung
            return {term: "Uncategorized" for term in search_terms}
        except Exception as e:
            print(f"Error in AI categorization: {e}")
            return {term: "Uncategorized" for term in search_terms}
    
    def identify_niche_opportunities(
        self, 
        df: pd.DataFrame, 
        category_col: str = 'Category'
    ) -> pd.DataFrame:
        """
        Identifiziert Nische-Opportunities basierend auf Volume und Market Share
        
        Args:
            df: DataFrame mit kategorisierten Daten
            category_col: Name der Kategoriespalte
            
        Returns:
            pd.DataFrame: DataFrame mit Opportunity-Score
        """
        if category_col not in df.columns:
            return df
        
        # Gruppiere nach Kategorie
        category_stats = df.groupby(category_col).agg({
            'Impressions': 'sum',
            'Sales': 'sum',
            'Search Term': 'count'
        }).reset_index()
        
        category_stats.columns = [category_col, 'Total Impressions', 'Total Sales', 'Query Count']
        
        # Berechne Market Share pro Kategorie
        total_sales = category_stats['Total Sales'].sum()
        if total_sales > 0:
            category_stats['Market Share %'] = (
                category_stats['Total Sales'] / total_sales * 100
            ).round(2)
        else:
            category_stats['Market Share %'] = 0
        
        # Berechne Opportunity Score (High Volume, Low Market Share = High Opportunity)
        max_impressions = category_stats['Total Impressions'].max()
        max_share = category_stats['Market Share %'].max()
        
        if max_impressions > 0 and max_share > 0:
            category_stats['Volume Score'] = (
                category_stats['Total Impressions'] / max_impressions * 100
            )
            category_stats['Opportunity Score'] = (
                category_stats['Volume Score'] * (100 - category_stats['Market Share %']) / 100
            )
        else:
            category_stats['Opportunity Score'] = 0
        
        return category_stats.sort_values('Opportunity Score', ascending=False)

