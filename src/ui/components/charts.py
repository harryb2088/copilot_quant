"""Chart components using Plotly - Bloomberg Terminal style"""
import plotly.graph_objects as go

# Professional dark theme colors (Bloomberg-inspired)
DARK_BG = '#0E1117'
CARD_BG = '#1E2127'
GRID_COLOR = '#2E3440'
TEXT_COLOR = '#FAFAFA'
ACCENT_PURPLE = '#9B59B6'
ACCENT_GREEN = '#2ECC71'
ACCENT_RED = '#E74C3C'
ACCENT_BLUE = '#3498DB'
ACCENT_GOLD = '#F39C12'

# Template for all charts - professional dark theme
CHART_TEMPLATE = {
    'layout': {
        'plot_bgcolor': CARD_BG,
        'paper_bgcolor': DARK_BG,
        'font': {'color': TEXT_COLOR, 'family': 'Arial, sans-serif', 'size': 12},
        'xaxis': {'gridcolor': GRID_COLOR, 'color': TEXT_COLOR},
        'yaxis': {'gridcolor': GRID_COLOR, 'color': TEXT_COLOR},
        'hovermode': 'x unified',
        'margin': {'l': 60, 'r': 20, 't': 60, 'b': 60}
    }
}


def plot_equity_curve(data):
    """
    Plot equity curve from backtest results - Professional dark theme
    
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
        line=dict(color=ACCENT_BLUE, width=3),
        fill='tozeroy',
        fillcolor=f'rgba(52, 152, 219, 0.1)'
    ))
    
    fig.update_layout(
        title=dict(text='<b>Equity Curve</b>', font=dict(size=18, color=TEXT_COLOR)),
        xaxis_title='Date',
        yaxis_title='Portfolio Value ($)',
        plot_bgcolor=CARD_BG,
        paper_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family='Arial, sans-serif'),
        xaxis=dict(gridcolor=GRID_COLOR, showgrid=True),
        yaxis=dict(gridcolor=GRID_COLOR, showgrid=True, tickformat='$,.0f'),
        hovermode='x unified',
        height=400
    )
    
    return fig


def plot_drawdown(data):
    """
    Plot drawdown chart - Professional dark theme
    
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
        line=dict(color=ACCENT_RED, width=3),
        fillcolor=f'rgba(231, 76, 60, 0.2)'
    ))
    
    fig.update_layout(
        title=dict(text='<b>Drawdown Analysis</b>', font=dict(size=18, color=TEXT_COLOR)),
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        plot_bgcolor=CARD_BG,
        paper_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family='Arial, sans-serif'),
        xaxis=dict(gridcolor=GRID_COLOR, showgrid=True),
        yaxis=dict(gridcolor=GRID_COLOR, showgrid=True, tickformat='.1%'),
        hovermode='x unified',
        height=400
    )
    
    return fig


def plot_portfolio_performance_chart(dates, values, title="Portfolio Performance"):
    """
    Plot main portfolio performance chart - Bloomberg style, chart-first display
    
    Args:
        dates: Array of dates
        values: Array of portfolio values
        title: Chart title
    
    Returns:
        Plotly figure optimized for top-of-page display
    """
    import numpy as np
    
    # Calculate returns for coloring
    returns = np.diff(values) / values[:-1]
    colors = [ACCENT_GREEN if r >= 0 else ACCENT_RED for r in returns]
    
    fig = go.Figure()
    
    # Main line chart
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines',
        name='Portfolio Value',
        line=dict(color=ACCENT_BLUE, width=4),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.15)',
        hovertemplate='<b>%{x}</b><br>Value: $%{y:,.0f}<extra></extra>'
    ))
    
    # Add range selector buttons
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1D", step="day", stepmode="backward"),
                dict(count=7, label="1W", step="day", stepmode="backward"),
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(label="ALL", step="all")
            ]),
            bgcolor=CARD_BG,
            activecolor=ACCENT_PURPLE,
            font=dict(color=TEXT_COLOR)
        ),
        rangeslider=dict(visible=False),
        type="date"
    )
    
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            font=dict(size=24, color=TEXT_COLOR),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title='',
        yaxis_title='Portfolio Value',
        plot_bgcolor=CARD_BG,
        paper_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family='Arial, sans-serif', size=14),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            showgrid=True,
            color=TEXT_COLOR
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            showgrid=True,
            tickformat='$,.0f',
            color=TEXT_COLOR
        ),
        hovermode='x unified',
        height=500,
        margin=dict(l=80, r=40, t=80, b=60)
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


def plot_cash_history(dates, cash_values):
    """
    Plot cash balance history over time
    
    Args:
        dates: Array of dates
        cash_values: Array of cash balance values
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=cash_values,
        mode='lines',
        name='Cash Balance',
        line=dict(color='#2ca02c', width=2),
        fill='tozeroy',
        fillcolor='rgba(44, 160, 44, 0.1)'
    ))
    
    fig.update_layout(
        title='Cash Balance History',
        xaxis_title='Date',
        yaxis_title='Cash Balance ($)',
        hovermode='x unified',
        template='plotly_white',
        height=350
    )
    
    return fig


def plot_exposure_chart(dates, gross_exposure, net_exposure):
    """
    Plot gross and net exposure over time
    
    Args:
        dates: Array of dates
        gross_exposure: Array of gross exposure values
        net_exposure: Array of net exposure values
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=gross_exposure,
        mode='lines',
        name='Gross Exposure',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=net_exposure,
        mode='lines',
        name='Net Exposure',
        line=dict(color='#ff7f0e', width=2)
    ))
    
    fig.update_layout(
        title='Portfolio Exposure',
        xaxis_title='Date',
        yaxis_title='Exposure (%)',
        hovermode='x unified',
        template='plotly_white',
        height=350,
        yaxis=dict(tickformat='.0%')
    )
    
    return fig


def plot_leverage_history(dates, leverage_values):
    """
    Plot leverage ratio over time
    
    Args:
        dates: Array of dates
        leverage_values: Array of leverage ratio values
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=leverage_values,
        mode='lines',
        name='Leverage Ratio',
        line=dict(color='#ff7f0e', width=2)
    ))
    
    # Add reference line at 1.0
    fig.add_hline(
        y=1.0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
        annotation_text="No Leverage"
    )
    
    fig.update_layout(
        title='Leverage History',
        xaxis_title='Date',
        yaxis_title='Leverage Ratio',
        hovermode='x unified',
        template='plotly_white',
        height=300
    )
    
    return fig


def plot_allocation_pie(categories, values):
    """
    Plot allocation as pie chart
    
    Args:
        categories: List of category names
        values: List of values for each category
    
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=values,
        hole=0.4,
        marker=dict(colors=['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728', '#9467bd'])
    )])
    
    fig.update_layout(
        title='Asset Allocation',
        height=350,
        showlegend=True
    )
    
    return fig


def plot_sector_exposure(sectors, exposures):
    """
    Plot exposure by sector as horizontal bar chart
    
    Args:
        sectors: List of sector names
        exposures: List of exposure values
    
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=[go.Bar(
        x=exposures,
        y=sectors,
        orientation='h',
        marker=dict(color='#1f77b4')
    )])
    
    fig.update_layout(
        title='Sector Exposure',
        xaxis_title='Exposure (%)',
        yaxis_title='Sector',
        template='plotly_white',
        height=300,
        xaxis=dict(tickformat='.0%')
    )
    
    return fig


def plot_attribution_waterfall(assets, pnl_values):
    """
    Plot P&L attribution as waterfall chart
    
    Args:
        assets: List of asset names
        pnl_values: List of P&L contributions
    
    Returns:
        Plotly figure
    """
    # Calculate cumulative values for waterfall
    cumulative = [0]
    for val in pnl_values:
        cumulative.append(cumulative[-1] + val)
    
    # Create waterfall chart
    colors = ['#2ca02c' if x > 0 else '#d62728' for x in pnl_values]
    
    fig = go.Figure()
    
    for i, (asset, pnl) in enumerate(zip(assets, pnl_values)):
        fig.add_trace(go.Bar(
            x=[asset],
            y=[pnl],
            base=[cumulative[i]],
            marker=dict(color=colors[i]),
            name=asset,
            showlegend=False
        ))
    
    fig.update_layout(
        title='P&L Attribution by Asset',
        xaxis_title='Asset',
        yaxis_title='P&L ($)',
        template='plotly_white',
        height=350,
        yaxis=dict(tickformat='$,.0f')
    )
    
    return fig


def plot_pnl_bars(categories, pnl_values):
    """
    Plot P&L as bar chart with color coding
    
    Args:
        categories: List of category names (assets, sectors, etc.)
        pnl_values: List of P&L values
    
    Returns:
        Plotly figure
    """
    colors = ['#2ca02c' if x > 0 else '#d62728' for x in pnl_values]
    
    fig = go.Figure(data=[go.Bar(
        x=categories,
        y=pnl_values,
        marker=dict(color=colors),
        text=pnl_values,
        texttemplate='$%{text:,.0f}',
        textposition='outside'
    )])
    
    fig.update_layout(
        title='P&L Distribution',
        xaxis_title='Category',
        yaxis_title='P&L ($)',
        template='plotly_white',
        height=350,
        yaxis=dict(tickformat='$,.0f')
    )
    
    return fig


def plot_rolling_sharpe(dates, sharpe_values):
    """
    Plot rolling Sharpe ratio over time
    
    Args:
        dates: Array of dates
        sharpe_values: Array of rolling Sharpe ratio values
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=sharpe_values,
        mode='lines',
        name='Rolling Sharpe',
        line=dict(color='#9467bd', width=2)
    ))
    
    # Add reference lines
    fig.add_hline(y=1.0, line_dash="dash", line_color="orange", opacity=0.5, annotation_text="Good")
    fig.add_hline(y=2.0, line_dash="dash", line_color="green", opacity=0.5, annotation_text="Excellent")
    
    fig.update_layout(
        title='Rolling Sharpe Ratio (90-day)',
        xaxis_title='Date',
        yaxis_title='Sharpe Ratio',
        hovermode='x unified',
        template='plotly_white',
        height=300
    )
    
    return fig


def plot_cumulative_returns(dates, returns):
    """
    Plot cumulative returns over time
    
    Args:
        dates: Array of dates
        returns: Array of cumulative return values
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=returns,
        mode='lines',
        name='Cumulative Return',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)'
    ))
    
    fig.update_layout(
        title='Cumulative Returns',
        xaxis_title='Date',
        yaxis_title='Return (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        yaxis=dict(tickformat='.1%')
    )
    
    return fig


def plot_price_with_signals(price_df, signals_df):
    """
    Plot share price with buy/sell signal markers.
    
    Args:
        price_df: DataFrame with Date and Close columns
        signals_df: DataFrame with timestamp, type ('BUY'/'SELL'), and price columns
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=price_df['Date'],
        y=price_df['Close'],
        mode='lines',
        name='Price',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # Add buy signals
    buy_signals = signals_df[signals_df['type'] == 'BUY']
    if not buy_signals.empty:
        fig.add_trace(go.Scatter(
            x=buy_signals['timestamp'],
            y=buy_signals['price'],
            mode='markers',
            marker=dict(color='green', size=10, symbol='triangle-up'),
            name='Buy Signal'
        ))
    
    # Add sell signals
    sell_signals = signals_df[signals_df['type'] == 'SELL']
    if not sell_signals.empty:
        fig.add_trace(go.Scatter(
            x=sell_signals['timestamp'],
            y=sell_signals['price'],
            mode='markers',
            marker=dict(color='red', size=10, symbol='triangle-down'),
            name='Sell Signal'
        ))
    
    fig.update_layout(
        title='Share Price & Trade Signals',
        xaxis_title='Time',
        yaxis_title='Price ($)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        yaxis=dict(tickformat='$.2f')
    )
    
    return fig


def plot_dividend_history(dividend_df, symbol="Portfolio"):
    """
    Plot dividend payment history - Bloomberg style
    
    Args:
        dividend_df: DataFrame with 'date' and 'amount' columns
        symbol: Stock symbol or "Portfolio" for display
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=dividend_df['date'],
        y=dividend_df['amount'],
        name='Dividend',
        marker=dict(
            color=ACCENT_GREEN,
            line=dict(color=ACCENT_GREEN, width=1)
        ),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Dividend: $%{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=f'<b>{symbol} - Dividend History</b>',
            font=dict(size=16, color=TEXT_COLOR)
        ),
        xaxis_title='Payment Date',
        yaxis_title='Dividend per Share ($)',
        plot_bgcolor=CARD_BG,
        paper_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family='Arial, sans-serif'),
        xaxis=dict(gridcolor=GRID_COLOR, showgrid=False, color=TEXT_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, showgrid=True, tickformat='$.2f', color=TEXT_COLOR),
        hovermode='x unified',
        height=300,
        margin=dict(l=60, r=20, t=50, b=50),
        showlegend=False
    )
    
    return fig


