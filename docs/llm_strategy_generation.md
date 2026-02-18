# LLM-Based Signal Strategy Generation

**⚠️ INTERNAL USE ONLY - DO NOT EXPOSE TO EXTERNAL USERS**

## Overview

This feature allows internal users to generate trading signal strategies using a Large Language Model (LLM). Instead of selecting from a predefined list of strategies, users can describe their desired strategy in plain English, and the LLM will generate the signal logic, parameters, and risk management rules.

## Features

### 🤖 Natural Language Strategy Generation
- Describe trading strategies in plain English
- Automatic signal logic generation based on description
- Parameter extraction from natural language
- Risk management rule generation

### 🔒 Security Safeguards
- **Input Sanitization**: Prevents code injection attacks
- **Rate Limiting**: Maximum 20 requests per hour per user
- **API Key Validation**: Ensures proper authentication
- **Pattern Blocking**: Blocks dangerous code execution patterns
- **Length Limits**: Prevents abuse through oversized inputs

### 📊 Strategy Components Generated
- Strategy name and type classification
- Signal indicators (RSI, SMA, MACD, etc.)
- Entry/exit conditions
- Risk management parameters
- Initial capital and position sizing

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root with your OpenAI API key:

```bash
# .env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Important**: 
- Never commit the `.env` file to version control
- Keep API keys secure and rotate them regularly
- Use a dedicated API key for this project with usage limits

### 2. Load Environment Variables

The application automatically loads environment variables when starting. Ensure your `.env` file is in the project root:

```bash
/home/runner/work/copilot_quant/copilot_quant/
├── .env                    # Your environment configuration
├── src/
│   └── ui/
│       ├── app.py         # Main Streamlit app
│       └── utils/
│           └── llm_strategy_generator.py
```

### 3. Install Dependencies

All required dependencies are already in `requirements.txt`. If you need to update:

```bash
pip install -r requirements.txt
```

### 4. Verify Configuration

Run the Streamlit app to verify LLM integration is working:

```bash
streamlit run src/ui/app.py
```

Navigate to the Backtests page. You should see:
- ✅ "LLM Integration Active" if API key is configured correctly
- ⚠️ "LLM Integration Not Configured" if API key is missing

## Usage Guide

### Basic Strategy Generation

1. **Navigate to Backtests Page**
   - Go to 🔬 Backtests from the sidebar

2. **Select LLM Mode**
   - Choose "Generate with LLM (Beta - Internal Use Only)"

3. **Describe Your Strategy**
   - Enter a plain English description of your trading strategy
   - Be specific about indicators, entry/exit conditions, and timeframes

   Example descriptions:
   ```
   A momentum strategy using 20-day and 50-day moving averages. 
   Buy when short MA crosses above long MA, sell when it crosses below. 
   Use RSI for confirmation.
   ```
   
   ```
   Mean reversion strategy with RSI. Buy when RSI drops below 30, 
   sell when it rises above 70. Include 2% stop loss.
   ```

4. **Generate Strategy**
   - Click "🤖 Generate Strategy"
   - Wait for processing (usually 1-3 seconds)
   - Review the generated strategy details

5. **Review Generated Strategy**
   - Check the strategy name and type
   - Verify signals and indicators
   - Review parameters and risk management
   - Make sure the generated strategy matches your intent

6. **Run Backtest**
   - Configure date range and capital
   - Click "🚀 Run Backtest"
   - View results

### Advanced: Strategy Refinement

After generating a strategy, you can refine it by:

1. Generating an initial strategy
2. Reviewing the output
3. Using the refinement feature (if implemented in UI)
4. Or regenerating with a more detailed description

### Example Workflows

#### Example 1: Momentum Strategy
```
Input: "Create a momentum strategy that buys when the 50-day moving 
average crosses above the 200-day moving average. Use $100k initial capital."

Generated Output:
- Name: "Create A Momentum Strategy..."
- Type: "Momentum"
- Signals: [{"type": "SMA", "short_period": 50, "long_period": 200}]
- Parameters: {"initial_capital": 100000, ...}
```

#### Example 2: Mean Reversion Strategy
```
Input: "Mean reversion using RSI. Buy oversold stocks (RSI < 30), 
sell overbought (RSI > 70). Position size 5%."

Generated Output:
- Name: "Mean Reversion Using Rsi..."
- Type: "Mean Reversion"
- Signals: [{"type": "RSI", "period": 14, "overbought": 70, "oversold": 30}]
- Parameters: {"position_size_pct": 5, ...}
```

## Security Best Practices

### 🔒 Internal Use Only

This feature is designed for **internal use only**. Do not:
- Expose the LLM integration to external users
- Share API keys with unauthorized personnel
- Allow user-submitted strategies without review
- Deploy without proper access controls

### 🛡️ Security Features

1. **Input Sanitization**
   - Blocks dangerous code patterns (`eval`, `exec`, `__import__`, etc.)
   - Prevents file system access attempts
   - Limits input length to 1000 characters

2. **Rate Limiting**
   - Maximum 20 requests per hour per user
   - Prevents API abuse
   - Automatically resets after 1 hour

3. **API Key Protection**
   - API keys stored in environment variables only
   - Never logged or displayed in UI
   - Validation before any API calls

4. **Error Handling**
   - Graceful failure on missing API keys
   - User-friendly error messages
   - No sensitive information in error logs

### ⚠️ What NOT to Do

- ❌ Don't commit API keys to version control
- ❌ Don't expose this feature to public users
- ❌ Don't disable input sanitization
- ❌ Don't remove rate limiting
- ❌ Don't trust LLM output without validation
- ❌ Don't use for production trading without thorough testing

## API Configuration

### OpenAI API

Currently supports OpenAI's GPT models. Default model: `gpt-3.5-turbo`

To change the model:

```python
from src.ui.utils.llm_strategy_generator import LLMStrategyGenerator

# Use a different model
generator = LLMStrategyGenerator(
    api_key="your-key",
    model="gpt-4"  # or other supported models
)
```

### Rate Limits

Default rate limits:
- **20 requests per hour** per user
- Configurable in `LLMStrategyGenerator.__init__`

To adjust:

```python
generator = LLMStrategyGenerator()
generator.max_requests_per_hour = 50  # Increase limit
```

## Architecture

### Components

1. **LLMStrategyGenerator** (`src/ui/utils/llm_strategy_generator.py`)
   - Main class handling LLM integration
   - Input sanitization
   - Rate limiting
   - Strategy generation logic

2. **Backtests Page** (`src/ui/pages/2_🔬_Backtests.py`)
   - UI integration
   - User input handling
   - Strategy display

3. **Tests** (`tests/test_ui/test_llm_strategy_generator.py`)
   - Unit tests for all functionality
   - Security validation tests
   - Integration tests

### Data Flow

```
User Input (Text Description)
    ↓
Input Sanitization
    ↓
Rate Limit Check
    ↓
LLM Processing (Strategy Generation)
    ↓
Strategy Object Creation
    ↓
UI Display & Validation
    ↓
Backtest Execution
```

### Strategy Object Structure

```python
{
    "name": "Strategy Name",
    "type": "Momentum|Mean Reversion|Statistical Arbitrage|Volatility|Custom",
    "description": "User's original description",
    "signals": [
        {
            "type": "RSI|SMA|MACD|...",
            "parameters": {...}
        }
    ],
    "parameters": {
        "initial_capital": 100000,
        "position_size_pct": 10,
        "max_positions": 10
    },
    "risk_management": {
        "stop_loss_pct": 2.0,
        "take_profit_pct": 5.0,
        "max_drawdown_pct": 10.0,
        "position_sizing": "equal_weight"
    },
    "generated_at": "ISO timestamp",
    "llm_model": "gpt-3.5-turbo"
}
```

## Testing

### Running Tests

```bash
# Run all LLM tests
pytest tests/test_ui/test_llm_strategy_generator.py -v

# Run specific test
pytest tests/test_ui/test_llm_strategy_generator.py::TestLLMStrategyGenerator::test_input_sanitization_dangerous -v

# Run with coverage
pytest tests/test_ui/test_llm_strategy_generator.py --cov=src.ui.utils.llm_strategy_generator
```

### Test Coverage

Tests cover:
- ✅ Input sanitization (valid and malicious inputs)
- ✅ Rate limiting (enforcement and reset)
- ✅ Strategy type inference
- ✅ Signal generation
- ✅ Parameter extraction
- ✅ Error handling
- ✅ API configuration validation

## Troubleshooting

### Common Issues

**1. "LLM API not configured" Error**
- **Cause**: Missing or invalid OPENAI_API_KEY
- **Solution**: Set the environment variable correctly
  ```bash
  export OPENAI_API_KEY=sk-your-key-here
  # or add to .env file
  ```

**2. "Rate limit exceeded" Error**
- **Cause**: Too many requests in a short time
- **Solution**: Wait for the rate limit to reset (1 hour) or increase the limit

**3. "Input contains potentially dangerous pattern" Error**
- **Cause**: Input contains blocked code patterns
- **Solution**: Rephrase your strategy description without technical code terms

**4. Strategy generation returns empty signals**
- **Cause**: Description doesn't mention specific indicators
- **Solution**: Be more specific about indicators (RSI, SMA, MACD, etc.)

### Debug Mode

To enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.ui.utils.llm_strategy_generator import LLMStrategyGenerator
generator = LLMStrategyGenerator(api_key="sk-...")
```

## Future Enhancements

Potential improvements for future versions:

1. **Real LLM Integration**
   - Currently uses pattern matching; could integrate actual OpenAI API
   - Support for other LLM providers (Anthropic, Cohere, etc.)

2. **Strategy Validation**
   - Automatic validation of generated strategies
   - Backtesting on sample data before user acceptance

3. **Learning from Feedback**
   - Track which generated strategies perform well
   - Improve generation based on historical success

4. **Multi-turn Conversation**
   - Allow iterative refinement through conversation
   - Context-aware strategy modifications

5. **Code Generation**
   - Generate actual Python code for strategies
   - Export to strategy files

## Support

For internal support:
- Check this documentation first
- Review test cases for examples
- Contact the development team

## License

Internal use only. Not for redistribution.

---

**Last Updated**: 2024-02-17  
**Version**: 1.0.0  
**Status**: Beta - Internal Use Only
