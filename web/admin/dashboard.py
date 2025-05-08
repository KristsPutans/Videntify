#!/usr/bin/env python3
"""
Admin Dashboard for Videntify

Provides monitoring tools for content ingestion and system performance metrics.
"""

import os
import sys
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from flask import Flask
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Videntify modules
from src.config.config import ConfigManager
from src.db.vector_db import get_vector_db_client

# Initialize Flask server
server = Flask(__name__)

# Initialize Dash app
app = dash.Dash(
    __name__,
    server=server,
    title="Videntify Admin Dashboard",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

# Load configuration
config_manager = ConfigManager()

# Create layout
app.layout = html.Div(
    [
        # Header
        html.Div(
            [
                html.H1("Videntify Admin Dashboard", className="dashboard-title"),
                html.Div(
                    [
                        html.Button("Refresh", id="refresh-button", className="refresh-button"),
                        dcc.Interval(id="interval-component", interval=30*1000, n_intervals=0),
                    ],
                    className="header-actions",
                ),
            ],
            className="dashboard-header",
        ),
        
        # Summary stats
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Total Videos"),
                        html.H2(id="total-videos", children="0"),
                    ],
                    className="stat-card",
                ),
                html.Div(
                    [
                        html.H3("Today's Ingestion"),
                        html.H2(id="today-ingestion", children="0"),
                    ],
                    className="stat-card",
                ),
                html.Div(
                    [
                        html.H3("Vector Database Size"),
                        html.H2(id="vector-db-size", children="0"),
                    ],
                    className="stat-card",
                ),
                html.Div(
                    [
                        html.H3("API Requests (24h)"),
                        html.H2(id="api-requests", children="0"),
                    ],
                    className="stat-card",
                ),
            ],
            className="summary-stats",
        ),
        
        # Content ingestion chart
        html.Div(
            [
                html.H2("Content Ingestion"),
                dcc.Tabs(
                    [
                        dcc.Tab(
                            label="Daily",
                            children=[
                                dcc.Graph(id="daily-ingestion-chart"),
                            ],
                        ),
                        dcc.Tab(
                            label="By Source",
                            children=[
                                dcc.Graph(id="source-ingestion-chart"),
                            ],
                        ),
                    ]
                ),
            ],
            className="chart-container",
        ),
        
        # System performance
        html.Div(
            [
                html.H2("System Performance"),
                dcc.Tabs(
                    [
                        dcc.Tab(
                            label="API Response Time",
                            children=[
                                dcc.Graph(id="api-response-chart"),
                            ],
                        ),
                        dcc.Tab(
                            label="Resource Usage",
                            children=[
                                dcc.Graph(id="resource-usage-chart"),
                            ],
                        ),
                    ]
                ),
            ],
            className="chart-container",
        ),
        
        # Vector database stats
        html.Div(
            [
                html.H2("Vector Database Statistics"),
                html.Div(
                    [
                        dcc.Graph(id="vector-db-stats-chart"),
                    ]
                ),
            ],
            className="chart-container",
        ),
        
        # Identification accuracy metrics
        html.Div(
            [
                html.H2("Identification Performance"),
                dcc.Tabs([
                    dcc.Tab(
                        label="Accuracy Metrics",
                        children=[
                            html.Div([
                                html.Div([
                                    html.H3("Overall Accuracy"),
                                    html.Div(id="accuracy-gauge", className="gauge-container"),
                                ], className="metric-card"),
                                html.Div([
                                    html.H3("Feature Performance"),
                                    html.Div(id="feature-performance-chart"),
                                ], className="metric-card wide"),
                            ], className="metrics-row"),
                        ],
                    ),
                    dcc.Tab(
                        label="Recent Matches",
                        children=[
                            html.Div(id="recent-matches-table"),
                        ],
                    ),
                ]),
            ],
            className="chart-container",
        ),
        
        # System health monitoring
        html.Div(
            [
                html.H2("System Health"),
                dcc.Tabs([
                    dcc.Tab(
                        label="Component Status",
                        children=[
                            html.Div(id="system-health-status"),
                        ],
                    ),
                    dcc.Tab(
                        label="Error Rates",
                        children=[
                            dcc.Graph(id="error-rates-chart"),
                        ],
                    ),
                ]),
            ],
            className="chart-container",
        ),
        
        # Recent content table
        html.Div(
            [
                html.H2("Recently Ingested Content"),
                html.Div(id="recent-content-table"),
            ],
            className="table-container",
        ),
    ],
    className="dashboard-container",
)

# Callbacks
@app.callback(
    [
        Output("total-videos", "children"),
        Output("today-ingestion", "children"),
        Output("vector-db-size", "children"),
        Output("api-requests", "children"),
    ],
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_summary_stats(n_intervals, n_clicks):
    """Update the summary statistics."""
    # In a real app, these would be fetched from the database
    # Mock data for now
    total_videos = 12845
    today_ingestion = 432
    
    # Get actual vector database size if possible
    try:
        vector_db_client = get_vector_db_client()
        vector_db_client.connect()
        collections = vector_db_client.list_collections()
        
        total_vectors = 0
        for collection in collections:
            try:
                count = vector_db_client.get_collection_stats(collection)
                total_vectors += count
            except:
                pass
        
        vector_db_size = f"{total_vectors:,}"
    except:
        vector_db_size = "N/A"
    
    api_requests = 25843
    
    return total_videos, today_ingestion, vector_db_size, api_requests

@app.callback(
    Output("daily-ingestion-chart", "figure"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_daily_ingestion_chart(n_intervals, n_clicks):
    """Update the daily ingestion chart."""
    # Mock data
    dates = pd.date_range(start="2025-05-01", periods=8, freq="D")
    counts = [320, 450, 380, 520, 410, 380, 432, 150]
    
    df = pd.DataFrame({"Date": dates, "Videos Ingested": counts})
    
    fig = px.bar(
        df,
        x="Date",
        y="Videos Ingested",
        title="Daily Content Ingestion",
        height=350,
    )
    
    return fig

@app.callback(
    Output("source-ingestion-chart", "figure"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_source_ingestion_chart(n_intervals, n_clicks):
    """Update the source ingestion chart."""
    # Mock data
    sources = ["Netflix", "Disney+", "Prime", "YouTube", "Network TV", "Other"]
    counts = [3560, 2840, 2650, 1845, 1250, 700]
    
    df = pd.DataFrame({"Source": sources, "Count": counts})
    
    fig = px.pie(
        df,
        names="Source",
        values="Count",
        title="Content Distribution by Source",
        height=350,
    )
    
    return fig

@app.callback(
    Output("api-response-chart", "figure"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_api_response_chart(n_intervals, n_clicks):
    """Update the API response time chart."""
    # Mock data
    hours = list(range(24))
    response_times = [120, 115, 105, 100, 95, 110, 150, 200, 280, 320, 340, 310, 
                    290, 320, 350, 370, 340, 300, 260, 210, 180, 160, 140, 130]
    
    df = pd.DataFrame({"Hour": hours, "Response Time (ms)": response_times})
    
    fig = px.line(
        df,
        x="Hour",
        y="Response Time (ms)",
        title="API Response Time (24h)",
        height=350,
    )
    
    return fig

@app.callback(
    Output("resource-usage-chart", "figure"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_resource_usage_chart(n_intervals, n_clicks):
    """Update the resource usage chart."""
    # Mock data
    time_points = list(range(24))
    cpu_usage = [30, 32, 28, 25, 22, 20, 25, 35, 60, 75, 80, 78, 
                72, 75, 82, 85, 80, 75, 65, 55, 45, 40, 35, 32]
    memory_usage = [45, 46, 44, 42, 40, 40, 42, 50, 65, 80, 85, 82, 
                  80, 82, 85, 88, 84, 80, 75, 70, 60, 55, 50, 48]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=time_points,
        y=cpu_usage,
        mode="lines",
        name="CPU (%)",
    ))
    
    fig.add_trace(go.Scatter(
        x=time_points,
        y=memory_usage,
        mode="lines",
        name="Memory (%)",
    ))
    
    fig.update_layout(
        title="Resource Usage (24h)",
        xaxis_title="Hour",
        yaxis_title="Usage (%)",
        height=350,
    )
    
    return fig

@app.callback(
    Output("vector-db-stats-chart", "figure"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_vector_db_stats_chart(n_intervals, n_clicks):
    """Update the vector database statistics chart."""
    # Try to get actual data from vector database
    try:
        vector_db_client = get_vector_db_client()
        vector_db_client.connect()
        collections = vector_db_client.list_collections()
        
        collection_data = []
        for collection in collections:
            try:
                count = vector_db_client.get_collection_stats(collection)
                collection_data.append((collection, count))
            except:
                pass
        
        if collection_data:
            df = pd.DataFrame(collection_data, columns=["Collection", "Count"])
            
            fig = px.bar(
                df,
                x="Collection",
                y="Count",
                title="Vector Database Collections",
                height=350,
            )
            
            return fig
    except:
        pass
    
    # Mock data if we couldn't get real data
    collections = ["vidid_cnn_features", "vidid_perceptual_hash", "vidid_motion_pattern", "vidid_audio_spectrogram"]
    counts = [25000, 12000, 8000, 5000]
    
    df = pd.DataFrame({"Collection": collections, "Count": counts})
    
    fig = px.bar(
        df,
        x="Collection",
        y="Count",
        title="Vector Database Collections",
        height=350,
    )
    
    return fig

@app.callback(
    Output("recent-content-table", "children"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_recent_content_table(n_intervals, n_clicks):
    """Update the recent content table."""
    # Mock data
    data = [
        {"id": "V12345", "title": "Stranger Things S04E08", "source": "Netflix", "timestamp": "2025-05-08 11:20:15", "status": "Complete"},
        {"id": "V12344", "title": "The Mandalorian S03E05", "source": "Disney+", "timestamp": "2025-05-08 11:05:32", "status": "Complete"},
        {"id": "V12343", "title": "The Boys S04E02", "source": "Prime", "timestamp": "2025-05-08 10:45:18", "status": "Complete"},
        {"id": "V12342", "title": "Top 10 Movie Scenes", "source": "YouTube", "timestamp": "2025-05-08 10:30:45", "status": "Complete"},
        {"id": "V12341", "title": "Breaking News May 8", "source": "CNN", "timestamp": "2025-05-08 10:15:20", "status": "Processing"},
    ]
    
    table = html.Table(
        # Header
        [html.Tr([html.Th(col) for col in ["ID", "Title", "Source", "Timestamp", "Status"]])]
        # Body
        + [html.Tr([html.Td(item[col]) for col in ["id", "title", "source", "timestamp", "status"]]) for item in data],
        className="content-table",
    )
    
    return table

# CSS for the dashboard
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .dashboard-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                font-family: Arial, sans-serif;
            }
            .dashboard-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                background-color: #2c3e50;
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
            }
            .dashboard-title {
                margin: 0;
                font-size: 24px;
            }
            .refresh-button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
            }
            .refresh-button:hover {
                background-color: #2980b9;
            }
            .summary-stats {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }
            .stat-card {
                flex: 1;
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin: 0 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }
            .stat-card h3 {
                margin: 0 0 10px 0;
                font-size: 14px;
                color: #7f8c8d;
            }
            .stat-card h2 {
                margin: 0;
                font-size: 28px;
                color: #2c3e50;
            }
            .chart-container, .table-container {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .chart-container h2, .table-container h2 {
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 18px;
                color: #2c3e50;
            }
            .content-table {
                width: 100%;
                border-collapse: collapse;
            }
            .content-table th, .content-table td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            .content-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .content-table tr:hover {
                background-color: #f5f5f5;
            }
            body {
                background-color: #ecf0f1;
                margin: 0;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Main function
def main():
    app.run_server(debug=True, host="0.0.0.0", port=8050)

# New callback for accuracy metrics
@app.callback(
    Output("accuracy-gauge", "children"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_accuracy_gauge(n_intervals, n_clicks):
    """Update the accuracy gauge."""
    # In a real app, this would be calculated from actual identification results
    accuracy = 92.7  # percentage
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=accuracy,
        title={"text": "Identification Accuracy"},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#4CAF50"},
            "steps": [
                {"range": [0, 60], "color": "#FF5252"},
                {"range": [60, 80], "color": "#FFC107"},
                {"range": [80, 100], "color": "#4CAF50"},
            ],
            "threshold": {
                "line": {"color": "#673AB7", "width": 4},
                "thickness": 0.75,
                "value": 90
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    
    return dcc.Graph(figure=fig)

@app.callback(
    Output("feature-performance-chart", "children"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_feature_performance_chart(n_intervals, n_clicks):
    """Update the feature performance chart."""
    # In a real app, this would show actual feature extraction performance
    # Mock data for now
    features = [
        "CNN Features", "Perceptual Hash", "Motion Pattern", 
        "Audio Spectrogram", "Scene Transition"
    ]
    precision = [0.94, 0.91, 0.86, 0.88, 0.82]
    recall = [0.92, 0.89, 0.84, 0.85, 0.80]
    speed = [0.95, 0.98, 0.90, 0.87, 0.93]  # normalized processing speed
    
    # Create a grouped bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=features,
        y=precision,
        name='Precision',
        marker_color='#4CAF50'
    ))
    
    fig.add_trace(go.Bar(
        x=features,
        y=recall,
        name='Recall',
        marker_color='#2196F3'
    ))
    
    fig.add_trace(go.Bar(
        x=features,
        y=speed,
        name='Processing Speed',
        marker_color='#FF9800'
    ))
    
    fig.update_layout(
        barmode='group',
        height=300,
        margin=dict(l=20, r=20, t=10, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return dcc.Graph(figure=fig)

@app.callback(
    Output("recent-matches-table", "children"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_recent_matches_table(n_intervals, n_clicks):
    """Update the recent matches table."""
    # In a real app, this would show actual recent matches
    # Mock data for now
    matches = [
        {"id": 1, "query": "User Video 1", "match": "Commercial A", "confidence": 98.2, "timestamp": "2025-05-08 12:45:34"},
        {"id": 2, "query": "User Image 3", "match": "Movie Scene B", "confidence": 94.7, "timestamp": "2025-05-08 12:30:21"},
        {"id": 3, "query": "User Video 2", "match": "TV Show C", "confidence": 89.5, "timestamp": "2025-05-08 12:15:45"},
        {"id": 4, "query": "User Image 1", "match": "Music Video D", "confidence": 92.3, "timestamp": "2025-05-08 11:50:17"},
        {"id": 5, "query": "User Video 5", "match": "Documentary E", "confidence": 97.1, "timestamp": "2025-05-08 11:32:09"},
    ]
    
    # Create the table
    table = html.Table(
        # Header
        [html.Tr([html.Th(col) for col in ["ID", "Query Type", "Match Content", "Confidence", "Timestamp"]])] +
        # Body
        [html.Tr([
            html.Td(match["id"]),
            html.Td(match["query"]),
            html.Td(match["match"]),
            html.Td(f"{match['confidence']}%"),
            html.Td(match["timestamp"]),
        ]) for match in matches],
        className="matches-table"
    )
    
    return table

@app.callback(
    Output("system-health-status", "children"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_system_health_status(n_intervals, n_clicks):
    """Update the system health status."""
    # In a real app, this would show actual system component statuses
    # Mock data for now
    components = [
        {"name": "API Server", "status": "Healthy", "latency": "45ms", "load": "32%"},
        {"name": "Feature Extraction Service", "status": "Healthy", "latency": "125ms", "load": "65%"},
        {"name": "Vector Database", "status": "Healthy", "latency": "18ms", "load": "28%"},
        {"name": "Storage Service", "status": "Healthy", "latency": "32ms", "load": "15%"},
        {"name": "Authentication Service", "status": "Healthy", "latency": "12ms", "load": "10%"},
    ]
    
    # Create status indicators
    status_cards = []
    for component in components:
        status_color = "#4CAF50" if component["status"] == "Healthy" else "#FF5252"
        
        card = html.Div(
            [
                html.Div(
                    html.Div(className="status-indicator", style={"backgroundColor": status_color}),
                    className="status-indicator-container"
                ),
                html.Div(
                    [
                        html.H3(component["name"]),
                        html.Div(
                            [
                                html.Span("Status: "),
                                html.Span(component["status"], style={"color": status_color, "fontWeight": "bold"}),
                            ]
                        ),
                        html.Div(f"Latency: {component['latency']}"),
                        html.Div(f"Load: {component['load']}"),
                    ],
                    className="status-details"
                )
            ],
            className="health-status-card"
        )
        
        status_cards.append(card)
    
    return html.Div(status_cards, className="health-status-container")

@app.callback(
    Output("error-rates-chart", "figure"),
    [Input("interval-component", "n_intervals"), Input("refresh-button", "n_clicks")]
)
def update_error_rates_chart(n_intervals, n_clicks):
    """Update the error rates chart."""
    # In a real app, this would show actual error rates over time
    # Mock data for now
    dates = pd.date_range(end=pd.Timestamp.now(), periods=24, freq='H')
    
    # Create some realistic error rate patterns
    api_errors = [0.2, 0.3, 0.1, 0.2, 0.1, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1, 0.2, 
                  0.3, 0.1, 0.0, 0.1, 0.2, 0.3, 0.5, 0.3, 0.2, 0.1, 0.0, 0.1]
    extraction_errors = [0.5, 0.4, 0.3, 0.2, 0.3, 0.1, 0.2, 0.3, 0.4, 0.3, 0.2, 0.1, 
                         0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0.2, 0.3, 0.2, 0.1]
    db_errors = [0.1, 0.0, 0.1, 0.2, 0.1, 0.0, 0.0, 0.1, 0.2, 0.1, 0.0, 0.1, 
                 0.0, 0.1, 0.2, 0.1, 0.0, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0, 0.0]
    
    # Create the figure
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=api_errors,
        mode='lines',
        name='API Errors',
        line=dict(color='#F44336', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=extraction_errors,
        mode='lines',
        name='Extraction Errors',
        line=dict(color='#FFC107', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=db_errors,
        mode='lines',
        name='Database Errors',
        line=dict(color='#9C27B0', width=2)
    ))
    
    fig.update_layout(
        title='System Error Rates (Last 24 Hours)',
        xaxis_title='Time',
        yaxis_title='Error Rate (%)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=20, t=40, b=40),
        height=350,
        yaxis=dict(
            tickformat='.1%',
            range=[0, 0.6]
        )
    )
    
    return fig

def main():
    """Run the application."""
    app.run(debug=True, host='0.0.0.0', port=8050)

if __name__ == "__main__":
    main()
