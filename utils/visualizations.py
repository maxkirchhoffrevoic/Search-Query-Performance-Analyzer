"""
Visualization Engine für Dashboards
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional


class VisualizationEngine:
    """Erstellt interaktive Visualisierungen für das Dashboard"""
    
    @staticmethod
    def create_opportunity_matrix(
        df: pd.DataFrame,
        category_col: str = 'Category',
        volume_col: str = 'Total Impressions',
        share_col: str = 'Market Share %',
        sales_col: str = 'Total Sales'
    ) -> go.Figure:
        """
        Erstellt Opportunity Matrix Bubble Chart
        
        Args:
            df: DataFrame mit Kategorie-Daten
            category_col: Spalte mit Kategorienamen
            volume_col: Spalte mit Volume (Impressions)
            share_col: Spalte mit Market Share
            sales_col: Spalte mit Sales (für Bubble-Größe)
            
        Returns:
            go.Figure: Plotly Figure
        """
        fig = go.Figure()
        
        # Berechne Bubble-Größe basierend auf Sales
        max_sales = df[sales_col].max()
        if max_sales > 0:
            bubble_sizes = (df[sales_col] / max_sales * 50) + 10
        else:
            bubble_sizes = [20] * len(df)
        
        # Erstelle Scatter Plot
        fig.add_trace(go.Scatter(
            x=df[volume_col],
            y=df[share_col],
            mode='markers+text',
            marker=dict(
                size=bubble_sizes,
                color=df[sales_col],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Sales"),
                sizemode='diameter',
                sizeref=max_sales/50,
                sizemin=10,
                line=dict(width=2, color='white')
            ),
            text=df[category_col],
            textposition="middle center",
            textfont=dict(size=10, color='white'),
            hovertemplate=(
                '<b>%{text}</b><br>' +
                f'Volume: %{{x:,.0f}}<br>' +
                f'Market Share: %{{y:.2f}}%<br>' +
                f'Sales: %{{marker.color:,.0f}}<br>' +
                '<extra></extra>'
            )
        ))
        
        fig.update_layout(
            title={
                'text': 'Opportunity Matrix: High Volume vs. Low Market Share',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Market Volume (Impressions)',
            yaxis_title='Market Share (%)',
            hovermode='closest',
            template='plotly_white',
            height=600
        )
        
        # Füge Quadranten-Linien hinzu
        if len(df) > 0:
            median_volume = df[volume_col].median()
            median_share = df[share_col].median()
            
            fig.add_hline(
                y=median_share,
                line_dash="dash",
                line_color="gray",
                annotation_text="Median Share",
                annotation_position="right"
            )
            fig.add_vline(
                x=median_volume,
                line_dash="dash",
                line_color="gray",
                annotation_text="Median Volume",
                annotation_position="top"
            )
        
        return fig
    
    @staticmethod
    def create_trend_analysis(
        df: pd.DataFrame,
        date_col: Optional[str] = None,
        impressions_col: str = 'Impressions',
        sales_col: str = 'Sales'
    ) -> go.Figure:
        """
        Erstellt Dual-Axis Trend Analysis Chart
        
        Args:
            df: DataFrame mit Zeitreihen-Daten
            date_col: Spalte mit Datum (optional)
            impressions_col: Spalte mit Impressions
            sales_col: Spalte mit Sales
            
        Returns:
            go.Figure: Plotly Figure
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Wenn kein Datum vorhanden, aggregiere nach Kategorie
        if date_col and date_col in df.columns:
            df_sorted = df.sort_values(date_col)
            x_axis = df_sorted[date_col]
        else:
            # Fallback: Verwende Index oder Kategorie
            if 'Category' in df.columns:
                df_sorted = df.groupby('Category').agg({
                    impressions_col: 'sum',
                    sales_col: 'sum'
                }).reset_index()
                x_axis = df_sorted['Category']
            else:
                x_axis = df.index
        
        # Impressions (Primary Y-Axis)
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df_sorted[impressions_col] if 'df_sorted' in locals() else df[impressions_col],
                name="Market Volume (Impressions)",
                line=dict(color='#1f77b4', width=3),
                mode='lines+markers'
            ),
            secondary_y=False,
        )
        
        # Sales (Secondary Y-Axis)
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df_sorted[sales_col] if 'df_sorted' in locals() else df[sales_col],
                name="Sales Velocity",
                line=dict(color='#ff7f0e', width=3),
                mode='lines+markers'
            ),
            secondary_y=True,
        )
        
        fig.update_xaxes(title_text="Zeit / Kategorie")
        fig.update_yaxes(title_text="Market Volume (Impressions)", secondary_y=False)
        fig.update_yaxes(title_text="Sales Velocity", secondary_y=True)
        
        fig.update_layout(
            title={
                'text': 'Market Trend Analysis: Volume vs. Sales Velocity',
                'x': 0.5,
                'xanchor': 'center'
            },
            template='plotly_white',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_share_of_voice(
        df: pd.DataFrame,
        category_col: str = 'Category',
        impressions_col: str = 'Impressions',
        sales_col: str = 'Sales'
    ) -> go.Figure:
        """
        Erstellt Share of Voice Tracking Chart
        
        Args:
            df: DataFrame mit Kategorie-Daten
            category_col: Spalte mit Kategorienamen
            impressions_col: Spalte mit Impressions
            sales_col: Spalte mit Sales
            
        Returns:
            go.Figure: Plotly Figure
        """
        # Berechne Share of Voice Metriken
        category_stats = df.groupby(category_col).agg({
            impressions_col: 'sum',
            sales_col: 'sum'
        }).reset_index()
        
        total_impressions = category_stats[impressions_col].sum()
        total_sales = category_stats[sales_col].sum()
        
        if total_impressions > 0:
            category_stats['Impression Share %'] = (
                category_stats[impressions_col] / total_impressions * 100
            )
        else:
            category_stats['Impression Share %'] = 0
        
        if total_sales > 0:
            category_stats['Sales Share %'] = (
                category_stats[sales_col] / total_sales * 100
            )
        else:
            category_stats['Sales Share %'] = 0
        
        # Erstelle grouped bar chart
        fig = go.Figure()
        
        categories = category_stats[category_col].tolist()
        
        fig.add_trace(go.Bar(
            name='Impression Share %',
            x=categories,
            y=category_stats['Impression Share %'],
            marker_color='#1f77b4'
        ))
        
        fig.add_trace(go.Bar(
            name='Sales Share %',
            x=categories,
            y=category_stats['Sales Share %'],
            marker_color='#ff7f0e'
        ))
        
        fig.update_layout(
            title={
                'text': 'Share of Voice: Brand Share by Category',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Category',
            yaxis_title='Share (%)',
            barmode='group',
            template='plotly_white',
            height=500,
            xaxis={'tickangle': -45}
        )
        
        return fig
    
    @staticmethod
    def create_performance_heatmap(
        df: pd.DataFrame,
        category_col: str = 'Category',
        metric_col: str = 'CTR'
    ) -> go.Figure:
        """
        Erstellt Heatmap für Performance-Metriken
        
        Args:
            df: DataFrame mit Daten
            category_col: Spalte mit Kategorienamen
            metric_col: Spalte mit Metrik
            
        Returns:
            go.Figure: Plotly Figure
        """
        if category_col not in df.columns or metric_col not in df.columns:
            # Fallback: Einfaches Bar Chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df.index[:20],  # Top 20
                y=df[metric_col][:20] if metric_col in df.columns else [0] * 20
            ))
            return fig
        
        # Gruppiere nach Kategorie
        category_metrics = df.groupby(category_col)[metric_col].mean().reset_index()
        category_metrics = category_metrics.sort_values(metric_col, ascending=False)
        
        fig = go.Figure(data=go.Bar(
            x=category_metrics[category_col],
            y=category_metrics[metric_col],
            marker=dict(
                color=category_metrics[metric_col],
                colorscale='RdYlGn',
                showscale=True
            )
        ))
        
        fig.update_layout(
            title={
                'text': f'Performance Heatmap: {metric_col} by Category',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Category',
            yaxis_title=metric_col,
            template='plotly_white',
            height=500,
            xaxis={'tickangle': -45}
        )
        
        return fig

