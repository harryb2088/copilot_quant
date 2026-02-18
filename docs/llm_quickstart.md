# LLM Strategy Generation - Quick Start

This document provides a quick overview of the LLM-based strategy generation feature.

## What Changed?

The Backtests page now has two modes for selecting strategies:

1. **Use Predefined Strategy** (Original) - Select from a dropdown list
2. **Generate with LLM** (New) - Describe your strategy in plain text

## Quick Demo

### Step 1: Navigate to Backtests
Open the Streamlit app and go to 🔬 Backtests page.

### Step 2: Select LLM Mode
Choose "Generate with LLM (Beta - Internal Use Only)" radio button.

### Step 3: Describe Your Strategy
Enter a description like:
```
A momentum strategy using 20-day and 50-day moving averages. 
Buy when short MA crosses above long MA with RSI confirmation above 50.
```

### Step 4: Generate
Click "🤖 Generate Strategy" button.

### Step 5: Review & Run
Review the generated strategy details and run backtest.

## Configuration Required

To use this feature, you need an OpenAI API key:

1. Copy `.env.example` to `.env`
2. Add: `OPENAI_API_KEY=sk-your-actual-key-here`
3. Restart the Streamlit app

Without configuration, you'll see a warning message.

## Example Strategies to Try

### Momentum Strategy
```
Create a momentum strategy that buys when the 50-day MA crosses 
above the 200-day MA. Use $100k initial capital.
```

### Mean Reversion Strategy
```
Mean reversion using RSI. Buy oversold stocks (RSI < 30), 
sell overbought (RSI > 70). Position size 5%.
```

### Volatility Strategy
```
Trade volatility breakouts. Buy when volatility expands 
beyond 2 standard deviations. Use 2% stop loss.
```

## Security Features

✅ Input sanitization  
✅ Rate limiting (20 requests/hour)  
✅ API key validation  
✅ Length limits  
✅ Internal use only

## Documentation

For complete documentation, see:
- **Full Guide**: `docs/llm_strategy_generation.md`
- **API Reference**: Code in `src/ui/utils/llm_strategy_generator.py`
- **Tests**: `tests/test_ui/test_llm_strategy_generator.py`

## Troubleshooting

**Problem**: "LLM API not configured" error  
**Solution**: Set `OPENAI_API_KEY` in `.env` file

**Problem**: "Rate limit exceeded" error  
**Solution**: Wait 1 hour or increase limit in code

**Problem**: "Input contains potentially dangerous pattern" error  
**Solution**: Rephrase strategy without code-like terms

## Important Notes

⚠️ **INTERNAL USE ONLY** - This feature is not for external users  
⚠️ Always review generated strategies before using  
⚠️ Validate on historical data before live trading  
⚠️ Keep your API key secure and never commit it

## Support

For questions or issues, refer to the full documentation or check the test suite for examples.

---
**Version**: 1.0.0  
**Last Updated**: 2024-02-17
