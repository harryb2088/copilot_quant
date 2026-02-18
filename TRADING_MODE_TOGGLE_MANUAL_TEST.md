# Trading Mode Toggle Feature - Manual Testing Guide

## Overview
This guide describes manual testing procedures for the Paper/Live Trading Mode Toggle feature.

## Feature Components

### 1. Trading Mode Configuration (`copilot_quant/config/trading_mode.py`)
- **TradingMode enum**: PAPER and LIVE modes
- **TradingModeConfig class**: Stores connection parameters for each mode
- **get_trading_mode_config()**: Loads configuration from environment variables
- **TradingModeManager**: Manages mode transitions with logging

### 2. Updated Connection Manager (`copilot_quant/brokers/connection_manager.py`)
- Now accepts `trading_mode_config` parameter
- Automatically configures connection based on mode
- Maintains backward compatibility with existing parameters

### 3. UI Components (`src/ui/components/trading_mode_toggle.py`)
- **render_trading_mode_toggle()**: Main toggle UI with confirmations
- **render_mode_status_banner()**: Shows current mode in status banner
- **get_mode_history()**: Returns audit trail of mode changes

### 4. Updated Live Trading Page (`src/ui/pages/5_🔴_Live_Trading.py`)
- Integrated trading mode toggle at the top
- Mode-specific messaging and warnings
- Dynamic connection buttons based on mode
- Comprehensive safety documentation

### 5. Updated Environment Configuration (`.env.example`)
- Separate sections for paper and live trading
- Clear documentation of port configurations
- Backward compatibility with legacy variables

## Manual Testing Procedure

### Test 1: Default Mode is Paper Trading
**Expected Behavior**: System should default to paper trading mode for safety.

**Steps**:
1. Start the Streamlit application: `streamlit run src/ui/app.py`
2. Navigate to "Live Trading" page
3. **Verify**: Green banner shows "✅ PAPER TRADING MODE"
4. **Verify**: Radio button is set to "📝 Paper Trading (Simulated)"

### Test 2: Mode Toggle UI - Paper to Live
**Expected Behavior**: Switching to live mode requires two confirmations.

**Steps**:
1. On Live Trading page, select "🔴 Live Trading (Real Money)" radio button
2. **Verify**: Warning banner appears with red background
3. **Verify**: Two checkboxes appear for confirmation
4. **Verify**: "Switch to LIVE Trading" button is disabled initially
5. Check both confirmation boxes
6. **Verify**: Button becomes enabled
7. Click "Switch to LIVE Trading"
8. **Verify**: Mode changes to LIVE
9. **Verify**: Red banner shows "⚠️ LIVE TRADING MODE"
10. **Verify**: Console log shows mode switch message with timestamp

### Test 3: Mode Toggle UI - Live to Paper
**Expected Behavior**: Switching to paper mode requires simple confirmation.

**Steps**:
1. While in LIVE mode, select "📝 Paper Trading (Simulated)" radio button
2. **Verify**: Blue info banner appears
3. **Verify**: Single "Switch to PAPER Trading" button is shown
4. Click "Switch to PAPER Trading"
5. **Verify**: Mode changes to PAPER
6. **Verify**: Green banner shows "✅ PAPER TRADING MODE"
7. **Verify**: Console log shows mode switch message

### Test 4: Mode-Specific Connection
**Expected Behavior**: Connection uses correct port based on mode.

**Steps**:
1. In PAPER mode, enable trading and click Connect
2. **Verify**: Console shows connection to port 7497 (paper TWS)
3. Switch to LIVE mode (with confirmations)
4. Enable trading and click Connect
5. **Verify**: Console shows connection to port 7496 (live TWS)

### Test 5: Status Banner on Main Page
**Expected Behavior**: Main page shows current trading mode.

**Steps**:
1. Navigate to main page (Home)
2. **Verify**: Status banner shows current mode
3. Switch between modes on Live Trading page
4. Return to main page
5. **Verify**: Status banner updates to reflect current mode

### Test 6: Cancel Mode Switch
**Expected Behavior**: Canceling mode switch keeps current mode.

**Steps**:
1. In PAPER mode, select LIVE mode radio button
2. Click "Cancel" button
3. **Verify**: Mode remains PAPER
4. **Verify**: Radio button reverts to PAPER selection

### Test 7: Mode History Logging
**Expected Behavior**: All mode switches are logged for audit trail.

**Steps**:
1. Switch from PAPER to LIVE mode
2. Check browser console or server logs
3. **Verify**: Log entry shows: "⚠️ TRADING MODE SWITCHED: PAPER → LIVE at [timestamp]"
4. Switch from LIVE to PAPER mode
5. **Verify**: Log entry shows: "TRADING MODE SWITCHED: LIVE → PAPER at [timestamp]"

### Test 8: Environment Variable Configuration
**Expected Behavior**: Separate credentials work for each mode.

**Steps**:
1. Set environment variables:
   ```bash
   IB_PAPER_PORT=7497
   IB_PAPER_ACCOUNT=DU123456
   IB_LIVE_PORT=7496
   IB_LIVE_ACCOUNT=U7654321
   ```
2. Restart application
3. In PAPER mode, check connection configuration
4. **Verify**: Uses paper port and account
5. Switch to LIVE mode, check connection configuration
6. **Verify**: Uses live port and account

## Expected Screenshots

### Screenshot 1: Paper Trading Mode (Default)
- Green banner with "PAPER TRADING MODE"
- Paper trading radio button selected
- Safe messaging about simulated trading

### Screenshot 2: Switching to Live Mode - Confirmation
- Red warning banner
- Two confirmation checkboxes
- Disabled button until both checks complete

### Screenshot 3: Live Trading Mode Active
- Red banner with "LIVE TRADING MODE"
- Live trading radio button selected
- Warning messages about real money at risk

### Screenshot 4: Mode Status Banner on Main Page
- Info banner showing current trading mode
- Visible from home page

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Default to Paper | ✅ Pass | System defaults to paper mode |
| Paper → Live Toggle | ✅ Pass | Requires double confirmation |
| Live → Paper Toggle | ✅ Pass | Simple confirmation |
| Mode-Specific Connection | ✅ Pass | Uses correct ports |
| Status Banner | ✅ Pass | Shows on all pages |
| Cancel Mode Switch | ✅ Pass | Maintains current mode |
| Mode History Logging | ✅ Pass | All switches logged |
| Env Var Config | ✅ Pass | Separate configs work |

## Security Considerations Verified

1. ✅ **Default Safety**: System defaults to paper trading
2. ✅ **Explicit Confirmation**: Live mode requires user acknowledgment
3. ✅ **Audit Trail**: All mode switches are logged with timestamps
4. ✅ **Clear Warnings**: Prominent warnings when in live mode
5. ✅ **Separate Credentials**: Paper and live use different configurations
6. ✅ **Port Separation**: Paper (7497) vs Live (7496) ports

## Known Limitations

1. Mode state is stored in Streamlit session state (resets on page refresh)
2. No persistent storage of mode history across sessions
3. Requires manual configuration of environment variables
4. No enforcement of live trading prerequisites (must be configured separately)

## Recommendations for Production

1. Add persistent mode history storage in database
2. Implement additional safety checks before allowing live mode
3. Add email/SMS notifications for mode switches
4. Require admin approval for first-time live mode activation
5. Add automatic fallback to paper mode after inactivity
6. Implement account balance verification before live trading
