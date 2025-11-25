"""
AI-Powered Categorization Engine mit ChatGPT API
"""
import openai
from typing import List, Dict, Optional
import pandas as pd
from config import OPENAI_API_KEY, OPENAI_MODEL, REASONING_EFFORT
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import ThreadPoolExecutor, as_completed


class AICategorizer:
    """Kategorisiert Search Terms mit Hilfe von ChatGPT"""
    
    def __init__(self, model=None):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.model = model if model else OPENAI_MODEL
        self.reasoning_effort = REASONING_EFFORT
        self.fallback_model = "gpt-4-turbo-preview"  # Fallback falls GPT-5.1 nicht verfügbar
    
    def categorize_search_terms(
        self, 
        search_terms: List[str], 
        batch_size: int = 50,
        parallel: bool = True,
        max_workers: int = 3
    ) -> Dict[str, str]:
        """
        Kategorisiert eine Liste von Search Terms
        
        Args:
            search_terms: Liste von Search Terms
            batch_size: Anzahl der Terms pro Batch
            parallel: Ob parallele Verarbeitung verwendet werden soll
            max_workers: Anzahl paralleler Worker (nur wenn parallel=True)
            
        Returns:
            Dict: Mapping von Search Term zu Kategorie
        """
        if not self.client:
            raise ValueError("OpenAI API Key nicht konfiguriert. Bitte in .env Datei setzen.")
        
        categorization = {}
        
        # Erstelle Batches
        batches = [search_terms[i:i+batch_size] for i in range(0, len(search_terms), batch_size)]
        
        if parallel and len(batches) > 1:
            # Parallele Verarbeitung
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_batch = {
                    executor.submit(self._categorize_batch, batch): batch 
                    for batch in batches
                }
                
                for future in as_completed(future_to_batch):
                    try:
                        batch_categories = future.result()
                        categorization.update(batch_categories)
                    except Exception as e:
                        batch = future_to_batch[future]
                        import sys
                        print(f"ERROR: Batch failed: {e}", file=sys.stderr)
                        # Fallback: Alle als Uncategorized
                        for term in batch:
                            categorization[term] = "Uncategorized"
        else:
            # Sequenzielle Verarbeitung (für kleine Batches oder wenn parallel=False)
            for batch in batches:
                batch_categories = self._categorize_batch(batch)
                categorization.update(batch_categories)
                if len(batches) > 1:
                    time.sleep(0.2)  # Reduziertes Rate limiting
        
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
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Du bist ein Experte für Produktkategorisierung. Antworte immer nur mit gültigem JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"}
            }
            
            # Füge reasoning_effort hinzu, wenn GPT-5.1 verwendet wird
            if "gpt-5" in self.model.lower():
                api_params["reasoning_effort"] = self.reasoning_effort
            
            response = self.client.chat.completions.create(**api_params)
            
            result_text = response.choices[0].message.content.strip()
            
            # Debug: Zeige erste 200 Zeichen der Antwort
            import sys
            print(f"DEBUG: API Response (first 200 chars): {result_text[:200]}", file=sys.stderr)
            print(f"DEBUG: Number of search terms sent: {len(search_terms)}", file=sys.stderr)
            
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
            
            # Prüfe ob alle Search Terms im Ergebnis sind
            missing_terms = [term for term in search_terms if term not in categories]
            if missing_terms:
                import sys
                print(f"DEBUG: Missing terms in response: {missing_terms[:5]}...", file=sys.stderr)
                # Füge fehlende Terms als Uncategorized hinzu
                for term in missing_terms:
                    categories[term] = "Uncategorized"
            
            import sys
            print(f"DEBUG: Successfully categorized {len(categories)} terms", file=sys.stderr)
            print(f"DEBUG: Sample categories: {dict(list(categories.items())[:3])}", file=sys.stderr)
            return categories
            
        except openai.APIError as e:
            error_msg = f"OpenAI API Error: {str(e)}"
            print(f"ERROR: {error_msg}")
            # Versuche Fallback auf gpt-4-turbo wenn gpt-5.1 fehlschlägt
            if "gpt-5" in OPENAI_MODEL.lower():
                print("DEBUG: Trying fallback to gpt-4-turbo-preview")
                try:
                    api_params_fallback = {
                        "model": "gpt-4-turbo-preview",
                        "messages": [
                            {"role": "system", "content": "Du bist ein Experte für Produktkategorisierung. Antworte immer nur mit gültigem JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 4096,
                        "response_format": {"type": "json_object"}
                    }
                    response = self.client.chat.completions.create(**api_params_fallback)
                    result_text = response.choices[0].message.content.strip()
                    categories = json.loads(result_text)
                    return categories
                except Exception as e2:
                    print(f"ERROR: Fallback also failed: {e2}")
            
            return {term: "Uncategorized" for term in search_terms}
        except json.JSONDecodeError as e:
            error_msg = f"JSON Parse Error: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(f"DEBUG: Response was: {result_text[:500] if 'result_text' in locals() else 'No response'}")
            # Fallback: Einfache Kategorisierung
            return {term: "Uncategorized" for term in search_terms}
        except Exception as e:
            error_msg = f"Unexpected Error in AI categorization: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
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
        # Finde die richtige Search Query Spalte
        search_col = 'Search Query' if 'Search Query' in df.columns else 'Search Term'
        agg_dict = {
            'Impressions': 'sum',
            'Sales': 'sum',
            search_col: 'count'
        }
        category_stats = df.groupby(category_col).agg(agg_dict).reset_index()
        
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

