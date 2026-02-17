"""Chart components using Plotly"""
import plotly.graph_objects as go


def plot_equity_curve(data):
    """
    Plot equity curve from backtest results
    
    Args:
        data: DataFrame with 'Date' and 'Equity' columns
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['Date'],
        y=data['Equity'],
        mode='lines',
        name='Equity',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.update_layout(
        title='Equity Curve',
        xaxis_title='Date',
        yaxis_title='Portfolio Value ($)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


def plot_drawdown(data):
    """
    Plot drawdown chart
    
    Args:
        data: DataFrame with 'Date' and 'Drawdown' columns
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['Date'],
        y=data['Drawdown'],
        mode='lines',
        name='Drawdown',
        fill='tozeroy',
        line=dict(color='#d62728', width=2)
    ))
    
    fig.update_layout(
        title='Drawdown',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


def plot_returns_distribution(returns):
    """
    Plot distribution of returns
    
    Args:
        returns: Series or array of returns
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=returns,
        nbinsx=50,
        name='Returns',
        marker_color='#2ca02c'
    ))
    
    fig.update_layout(
        title='Returns Distribution',
        xaxis_title='Return (%)',
        yaxis_title='Frequency',
        template='plotly_white',
        height=400
    )
    
    return fig


def plot_monthly_returns_heatmap(data):
    """
    Plot monthly returns heatmap
    
    Args:
        data: DataFrame with returns data
    
    Returns:
        Plotly figure
    """
    # Mock implementation - create sample heatmap data
    import numpy as np
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    years = ['2023', '2024']
    
    # Generate random returns for demo
    np.random.seed(42)
    returns_data = np.random.uniform(-5, 8, (len(years), len(months)))
    
    fig = go.Figure(data=go.Heatmap(
        z=returns_data,
        x=months,
        y=years,
        colorscale='RdYlGn',
        zmid=0
    ))
    
    fig.update_layout(
        title='Monthly Returns Heatmap',
        xaxis_title='Month',
        yaxis_title='Year',
        template='plotly_white',
        height=300
    )
    
    return fig
