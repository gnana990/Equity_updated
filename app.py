import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pymongo")

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz
import json
import os
from config import Config

# Import KiteConnect configuration and API functions
try:
    from kiteconnect_config import (
        get_lot_size_from_api, 
        get_expiry_dates_from_api, 
        get_current_price_from_api,
        get_options_data_from_api
    )
except ImportError:
    # Fallback functions if config file doesn't exist
    def get_lot_size_from_api(symbol):
        fallback_sizes = {"NIFTY": 50, "BANKNIFTY": 25, "FINNIFTY": 40, "MIDCPNIFTY": 75}
        return fallback_sizes.get(symbol, 50)
    
    def get_expiry_dates_from_api(symbol):
        return []
    
    def get_current_price_from_api(symbol):
        return None
    
    def get_options_data_from_api(symbol, expiry_date):
        return None

def calculate_volume_in_lots(volume_contracts, symbol):
    """
    Convert volume from contracts to lots
    Volume in lots = Volume in contracts / Lot size
    
    Example:
    If NIFTY volume = 25,000 contracts and lot size = 50
    Then traded quantity in lots = 25,000 ÷ 50 = 500 lots
    """
    lot_size = get_lot_size_from_api(symbol)
    return round(volume_contracts / lot_size, 2) if lot_size > 0 else 0

def calculate_oi_in_lots(oi_contracts, symbol):
    """
    Convert OI from contracts to lots
    OI in lots = OI in contracts / Lot size
    
    Example:
    If NIFTY OI = 50,000 contracts and lot size = 50
    Then OI in lots = 50,000 ÷ 50 = 1,000 lots
    """
    lot_size = get_lot_size_from_api(symbol)
    return round(oi_contracts / lot_size, 2) if lot_size > 0 else 0

def format_volume_display(volume_contracts, symbol, show_lots=True):
    """
    Format volume for display
    Args:
        volume_contracts: Volume in number of contracts (from API)
        symbol: Symbol name
        show_lots: If True, show volume in lots; if False, show in contracts
    Returns:
        Formatted volume string
    """
    if show_lots:
        volume_lots = calculate_volume_in_lots(volume_contracts, symbol)
        return f"{volume_lots:,.2f} lots"
    else:
        return f"{volume_contracts:,} contracts"

def format_oi_display(oi_contracts, symbol, show_lots=True):
    """
    Format OI for display
    Args:
        oi_contracts: OI in number of contracts (from API)
        symbol: Symbol name
        show_lots: If True, show OI in lots; if False, show in contracts
    Returns:
        Formatted OI string
    """
    if show_lots:
        oi_lots = calculate_oi_in_lots(oi_contracts, symbol)
        return f"{oi_lots:,.2f} lots"
    else:
        return f"{oi_contracts:,} contracts"

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# MongoDB Connection
client = MongoClient(Config.MONGODB_URI)
db = client['equity_project']
users_collection = db['users']

# SMTP Configuration
SMTP_SERVER = Config.SMTP_SERVER
SMTP_PORT = Config.SMTP_PORT
SMTP_USER = Config.SMTP_USER
SMTP_PASSWORD = Config.SMTP_PASSWORD

# Email alert cooldown (in seconds) to prevent spam
EMAIL_COOLDOWN = 300  # 5 minutes
last_email_sent = {}  # Track last email sent time for each user
last_special_alert_sent = {}  # Track last special alert sent time for each user

# User alert settings storage
user_alert_settings = {}  # Store user alert preferences

# Store previous OI values for detecting sudden jumps
previous_oi_values = {}  # Format: {user_email: {symbol: {strike_type: {strike: previous_oi}}}}

# Historical data collection
historical_data_collection = db['historical_data']

# Alerts collection
alerts_collection = db['alerts']

# Background alert system for all users
background_alert_settings = {}  # Store alert settings for all users
background_previous_oi_values = {}  # Store previous OI for background alerts

# Scheduled data collection for historical data
import threading
import time
from datetime import time as datetime_time

# Comprehensive NSE symbols list - Major indices first, then alphabetical order
# Organization:
# 1. First 5: Major Indices (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX)
# 2. Rest: All other symbols in alphabetical order (A-Z)
# Complete NSE F&O symbols list as of 2025
NSE_SYMBOLS = [
    # Major Indices (First 5 - Always at top)
    "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX",
    
    # All other symbols in alphabetical order (Complete NSE F&O list)
    "ABB", "ABBOTINDIA", "ACC", "ADANIENT", "ADANIPORTS", "ADANIPOWER", "ADANITRANS", "ADANIGREEN",
    "ALKEM", "AMARAJABAT", "AMBUJACEM", "APOLLOHOSP", "APOLLOTYRE", "ASIANPAINT", "AUROPHARMA",
    "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BAJAJHLDNG", "BALKRISIND", "BANDHANBNK",
    "BANKBARODA", "BEL", "BERGEPAINT", "BHARTIARTL", "BHEL", "BIOCON", "BPCL", "BRITANNIA",
    "CADILAHC", "CANBK", "CENTURYTEX", "CESC", "CHOLAFIN", "CIPLA", "COALINDIA", "COLPAL",
    "CUMMINSIND", "DABUR", "DEEPAKNTR", "DIVISLAB", "DLF", "DRREDDY", "EICHERMOT", "ESCORTS",
    "EXIDEIND", "FEDERALBNK", "GAIL", "GLENMARK", "GODREJCP", "GODREJIND", "GRASIM", "HAVELLS",
    "HCLTECH", "HDFC", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDCOPPER",
    "HINDPETRO", "HINDUNILVR", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDEA", "INDIGO", "INDUSINDBK",
    "INFY", "IOC", "ITC", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KARNATKA",
    "KOTAKBANK", "LT", "LUPIN", "M&M", "MARICO", "MARUTI", "MAXHEALTH", "MCDOWELL-N",
    "MINDTREE", "MPHASIS", "MUTHOOTFIN", "NATCOPHARM", "NESTLEIND", "NMDC", "NTPC", "ONGC",
    "PEL", "PERSISTENT", "PIDILITIND", "PFC", "PNB", "POWERGRID", "RECLTD", "RELIANCE",
    "RBLBANK", "SAIL", "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SIEMENS", "SUNPHARMA",
    "TATACOMM", "TATACONSUM", "TATAELXSI", "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM",
    "TITAN", "TORNTPHARM", "TVSMOTOR", "UBL", "ULTRACEMCO", "UPL", "VEDL", "VEYERMOTOR",
    "VOLTAS", "WIPRO", "YESBANK", "ZEEL", "ZYDUSLIFE"
]

def verify_symbols_order():
    """Verify that symbols are properly organized (major indices first, then alphabetical)"""
    major_indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
    
    # Check first 5 are major indices
    first_five = NSE_SYMBOLS[:5]
    if first_five != major_indices:
        print(f"First 5 symbols don't match major indices: {first_five}")
        return False
    
    # Check rest are in alphabetical order
    rest_symbols = NSE_SYMBOLS[5:]
    if rest_symbols != sorted(rest_symbols):
        print("Rest of symbols are not in alphabetical order")
        return False
    
    print("Symbols are properly organized!")
    print(f"   Major indices (first 5): {first_five}")
    print(f"   Total symbols: {len(NSE_SYMBOLS)}")
    print(f"   First 10 alphabetical: {rest_symbols[:10]}")
    return True

# Get available expiry dates for a symbol
def get_expiry_dates(symbol):
    """
    Get available expiry dates for a symbol from KiteConnect API
    """
    try:
        # Get expiry dates from API
        expiry_dates = get_expiry_dates_from_api(symbol)
        
        if expiry_dates:
            return expiry_dates
        
        # Fallback: generate mock expiry dates if API fails
        current_date = datetime.now()
        fallback_dates = []
        temp_date = current_date
        
        for i in range(3):
            # Get next month
            if temp_date.month == 12:
                next_month = temp_date.replace(year=temp_date.year + 1, month=1)
            else:
                next_month = temp_date.replace(month=temp_date.month + 1)
            
            # Find last Thursday of the month
            if next_month.month == 12:
                last_day_of_month = next_month.replace(year=next_month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day_of_month = next_month.replace(month=next_month.month + 1, day=1) - timedelta(days=1)
            
            last_thursday = last_day_of_month
            while last_thursday.weekday() != 3:  # Thursday is 3
                last_thursday = last_thursday - timedelta(days=1)
            
            fallback_dates.append(last_thursday.strftime("%d%b%y").upper())
            temp_date = next_month
        
        return fallback_dates
        
    except Exception as e:
        print(f"Error getting expiry dates for {symbol}: {e}")
        return []

# KiteConnect API data integration
def get_kiteconnect_data(symbol, expiry_date=None):
    """
    Get real options chain data from KiteConnect API
    """
    try:
        # Get current price from API
        current_price = get_current_price_from_api(symbol)
        if current_price is None:
            print(f"⚠️ Failed to get live price for {symbol}, using fallback")
            current_price = 24700.00  # Updated fallback to current market level
        
        # Use provided expiry date or get first available
        if expiry_date is None:
            expiry_dates = get_expiry_dates(symbol)
            expiry_date = expiry_dates[0] if expiry_dates else "28AUG25"
        
        # Get lot size from API
        lot_size = get_lot_size_from_api(symbol)
        
        # Try to get real options data from API
        api_data = get_options_data_from_api(symbol, expiry_date)
        
        if api_data and api_data.get('calls') and api_data.get('puts'):
            # Process real API data with NSE-compatible formatting
            calls = []
            puts = []
            
            print(f"✅ Processing live API data for {symbol} - {len(api_data['calls'])} calls, {len(api_data['puts'])} puts")
            
            for call in api_data['calls']:
                # Calculate values in lots for display
                call_oi_lots = calculate_oi_in_lots(call['oi'], symbol)
                call_oi_chg_lots = calculate_oi_in_lots(abs(call['oi_chg']), symbol)
                call_volume_lots = calculate_volume_in_lots(call['volume'], symbol)
                
                calls.append({
                    "strike": call['strike'],
                    "oi": call['oi'],  # OI in contracts (raw NSE data)
                    "oi_chg": call['oi_chg'],  # OI change in contracts (raw NSE data)
                    "oi_lots": call_oi_lots,  # OI in lots
                    "oi_chg_lots": call_oi_chg_lots,  # OI change in lots
                    "volume": call['volume'],  # Volume in contracts (raw NSE data)
                    "volume_lots": call_volume_lots,  # Volume in lots
                    "ltp": call.get('ltp', 0),
                    "bid": call.get('bid', 0),
                    "ask": call.get('ask', 0),
                    "change": call.get('change', 0),
                    "pchange": call.get('pchange', 0),
                    "volume_display": format_volume_display(call['volume'], symbol, show_lots=True),
                    "oi_display": format_oi_display(call['oi'], symbol, show_lots=True),
                    "oi_chg_display": format_oi_display(abs(call['oi_chg']), symbol, show_lots=True)
                })
            
            for put in api_data['puts']:
                # Calculate values in lots for display
                put_oi_lots = calculate_oi_in_lots(put['oi'], symbol)
                put_oi_chg_lots = calculate_oi_in_lots(abs(put['oi_chg']), symbol)
                put_volume_lots = calculate_volume_in_lots(put['volume'], symbol)
                
                puts.append({
                    "strike": put['strike'],
                    "oi": put['oi'],  # OI in contracts (raw NSE data)
                    "oi_chg": put['oi_chg'],  # OI change in contracts (raw NSE data)
                    "oi_lots": put_oi_lots,  # OI in lots
                    "oi_chg_lots": put_oi_chg_lots,  # OI change in lots
                    "volume": put['volume'],  # Volume in contracts (raw NSE data)
                    "volume_lots": put_volume_lots,  # Volume in lots
                    "ltp": put.get('ltp', 0),
                    "bid": put.get('bid', 0),
                    "ask": put.get('ask', 0),
                    "change": put.get('change', 0),
                    "pchange": put.get('pchange', 0),
                    "volume_display": format_volume_display(put['volume'], symbol, show_lots=True),
                    "oi_display": format_oi_display(put['oi'], symbol, show_lots=True),
                    "oi_chg_display": format_oi_display(abs(put['oi_chg']), symbol, show_lots=True)
                })
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "lot_size": lot_size,
                "expiry_date": expiry_date,
                "calls": calls,
                "puts": puts
            }
        
        else:
            # Fallback to mock data if API fails
            print(f"API data not available for {symbol}, using fallback data")
            
            # Generate strikes around current price (±10 strikes)
            base_strike = int(current_price / 50) * 50  # Round to nearest 50
            strikes = []
            for i in range(-10, 11):
                strikes.append(base_strike + (i * 50))
            
            calls = []
            puts = []
            
            # Generate fallback data for calls and puts
            for strike in strikes:
                # Calls data
                call_oi = max(0, int((current_price - strike + 1000) * 1000))
                call_oi_chg = 0 if strike == current_price else int((call_oi * 0.1) * (1 if strike < current_price else -1))
                call_volume = max(0, int(call_oi * 0.3))  # Volume is typically 30% of OI
                
                # Calculate values in lots for display
                call_oi_lots = calculate_oi_in_lots(call_oi, symbol)
                call_oi_chg_lots = calculate_oi_in_lots(call_oi_chg, symbol)
                call_volume_lots = calculate_volume_in_lots(call_volume, symbol)
                
                calls.append({
                    "strike": strike,
                    "oi": call_oi,
                    "oi_chg": call_oi_chg,
                    "oi_lots": call_oi_lots,
                    "oi_chg_lots": call_oi_chg_lots,
                    "volume": call_volume,
                    "volume_lots": call_volume_lots,
                    "ltp": 0,
                    "bid": 0,
                    "ask": 0,
                    "volume_display": format_volume_display(call_volume, symbol, show_lots=True),
                    "oi_display": format_oi_display(call_oi, symbol, show_lots=True),
                    "oi_chg_display": format_oi_display(call_oi_chg, symbol, show_lots=True)
                })
                
                # Puts data
                put_oi = max(0, int((strike - current_price + 1000) * 1000))
                put_oi_chg = 0 if strike == current_price else int((put_oi * 0.1) * (1 if strike > current_price else -1))
                put_volume = max(0, int(put_oi * 0.3))
                
                # Calculate values in lots for display
                put_oi_lots = calculate_oi_in_lots(put_oi, symbol)
                put_oi_chg_lots = calculate_oi_in_lots(put_oi_chg, symbol)
                put_volume_lots = calculate_volume_in_lots(put_volume, symbol)
                
                puts.append({
                    "strike": strike,
                    "oi": put_oi,
                    "oi_chg": put_oi_chg,
                    "oi_lots": put_oi_lots,
                    "oi_chg_lots": put_oi_chg_lots,
                    "volume": put_volume,
                    "volume_lots": put_volume_lots,
                    "ltp": 0,
                    "bid": 0,
                    "ask": 0,
                    "volume_display": format_volume_display(put_volume, symbol, show_lots=True),
                    "oi_display": format_oi_display(put_oi, symbol, show_lots=True),
                    "oi_chg_display": format_oi_display(put_oi_chg, symbol, show_lots=True)
                })
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "lot_size": lot_size,
                "expiry_date": expiry_date,
                "calls": calls,
                "puts": puts
            }
    
    except Exception as e:
        print(f"Error in get_kiteconnect_data for {symbol}: {e}")
        return None

# Historical data functions
def store_historical_data(symbol, expiry_date, options_data):
    """Store historical data in MongoDB"""
    try:
        # Create historical data record
        historical_record = {
            "symbol": symbol,
            "expiry_date": expiry_date,
            "timestamp": datetime.now(),
            "current_price": options_data['current_price'],
            "lot_size": options_data['lot_size'],
            "calls_data": options_data['calls'],
            "puts_data": options_data['puts'],
            "total_ce_oi": sum(call['oi'] for call in options_data['calls']),  # OI in contracts
            "total_pe_oi": sum(put['oi'] for put in options_data['puts']),  # OI in contracts
            "total_ce_oi_lots": sum(call.get('oi_lots', 0) for call in options_data['calls']),  # OI in lots
            "total_pe_oi_lots": sum(put.get('oi_lots', 0) for put in options_data['puts']),  # OI in lots
            "total_ce_volume": sum(call['volume'] for call in options_data['calls']),  # Volume in contracts
            "total_pe_volume": sum(put['volume'] for put in options_data['puts']),  # Volume in contracts
            "total_ce_volume_lots": sum(call.get('volume_lots', 0) for call in options_data['calls']),  # Volume in lots
            "total_pe_volume_lots": sum(put.get('volume_lots', 0) for put in options_data['puts']),  # Volume in lots
            "pcr": sum(put['oi'] for put in options_data['puts']) / max(sum(call['oi'] for call in options_data['calls']), 1)
        }
        
        # Insert into MongoDB
        historical_data_collection.insert_one(historical_record)
        
        # Auto-cleanup: Delete data older than 2 hours
        cleanup_old_historical_data()
        
    except Exception as e:
        print(f"Error storing historical data: {e}")

def cleanup_old_historical_data():
    """Delete historical data older than 2 days"""
    try:
        cutoff_time = datetime.now() - timedelta(days=2)
        result = historical_data_collection.delete_many({"timestamp": {"$lt": cutoff_time}})
        if result.deleted_count > 0:
            print(f"Cleaned up {result.deleted_count} old historical records (older than 2 days)")
    except Exception as e:
        print(f"Error cleaning up historical data: {e}")

def get_historical_data(symbol, expiry_date, date_filter=None, time_range="all", start_time="09:00", end_time="16:00"):
    """Get historical data for the specified filters"""
    try:
        # Set IST timezone
        ist_timezone = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist_timezone)
        
        # Calculate date range (last 2 days)
        if date_filter:
            # Specific date filter
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").replace(tzinfo=ist_timezone)
                start_date = filter_date.replace(hour=9, minute=0, second=0, microsecond=0)
                end_date = filter_date.replace(hour=16, minute=0, second=0, microsecond=0)
            except ValueError:
                # If date parsing fails, use last 2 days
                end_date = now.replace(hour=16, minute=0, second=0, microsecond=0)
                start_date = end_date - timedelta(days=2)
        else:
            # Last 2 days
            end_date = now.replace(hour=16, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=2)
        
        # Apply time range filter
        if time_range == "morning":
            start_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=12, minute=0, second=0, microsecond=0)
        elif time_range == "afternoon":
            start_date = start_date.replace(hour=12, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
        elif time_range == "custom":
            try:
                start_hour, start_minute = map(int, start_time.split(':'))
                end_hour, end_minute = map(int, end_time.split(':'))
                
                # Apply custom time to each day in the range
                start_date = start_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                end_date = end_date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            except ValueError:
                # If time parsing fails, use default 9 AM to 4 PM
                start_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
                end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
        else:  # "all" - 9 AM to 4 PM for each day
            start_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Query MongoDB for historical data
        cursor = historical_data_collection.find({
            "symbol": symbol,
            "expiry_date": expiry_date,
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("timestamp", 1)  # Sort by timestamp ascending
        
        historical_data = list(cursor)
        
        # Format data for frontend
        formatted_data = []
        for record in historical_data:
            # Calculate values in lots if not already stored
            lot_size = get_lot_size_from_api(record["symbol"])
            ce_oi_lots = record.get("total_ce_oi_lots", 
                                  round(record["total_ce_oi"] / lot_size, 2) if lot_size > 0 else 0)
            pe_oi_lots = record.get("total_pe_oi_lots", 
                                  round(record["total_pe_oi"] / lot_size, 2) if lot_size > 0 else 0)
            ce_volume_lots = record.get("total_ce_volume_lots", 
                                      round(record["total_ce_volume"] / lot_size, 2) if lot_size > 0 else 0)
            pe_volume_lots = record.get("total_pe_volume_lots", 
                                      round(record["total_pe_volume"] / lot_size, 2) if lot_size > 0 else 0)
            
            formatted_data.append({
                "timestamp": record["timestamp"].isoformat(),  # Full ISO timestamp for frontend parsing
                "current_price": record["current_price"],
                "total_ce_oi": record["total_ce_oi"],  # OI in contracts
                "total_pe_oi": record["total_pe_oi"],  # OI in contracts
                "total_ce_oi_lots": ce_oi_lots,  # OI in lots
                "total_pe_oi_lots": pe_oi_lots,  # OI in lots
                "total_ce_volume": record["total_ce_volume"],  # Volume in contracts
                "total_pe_volume": record["total_pe_volume"],  # Volume in contracts
                "total_ce_volume_lots": ce_volume_lots,  # Volume in lots
                "total_pe_volume_lots": pe_volume_lots,  # Volume in lots
                "pcr": round(record["pcr"], 2)
            })
        
        return formatted_data
        
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return []

def send_negative_oi_alert(user_email, symbol, strike, option_type, oi_change, threshold, time_ist):
    """Send email alert for negative OI changes"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = user_email
        msg['Subject'] = f"🔴 Alert: Negative OI Change for {symbol} {strike} {option_type}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
            <div style="background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #dc2626;">
                <h2 style="color: #dc2626; margin-top: 0;">🔴 Negative OI Change Alert</h2>
                
                <div style="background-color: #fef2f2; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="margin-top: 0; color: #dc2626;">Options Chain Alert</h3>
                    <p><strong>Symbol:</strong> {symbol}</p>
                    <p><strong>Strike Price:</strong> {strike}</p>
                    <p><strong>Option Type:</strong> {option_type}</p>
                    <p><strong>OI Change:</strong> <span style="color: #dc2626; font-weight: bold;">{oi_change:,} lots</span></p>
                    <p><strong>Threshold:</strong> {threshold:,} lots</p>
                    <p><strong>Time (IST):</strong> {time_ist}</p>
                </div>
                
                <p style="margin-top: 20px; font-size: 14px; color: #6c757d;">
                    This alert was triggered because the OI change exceeded the negative threshold within 10 strikes of the current market price.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USER, user_email, text)
        server.quit()
        
        print(f"Negative OI alert sent to {user_email} for {symbol} {strike} {option_type}")
        return True
    except Exception as e:
        print(f"Failed to send negative OI alert: {e}")
        return False

def send_total_oi_alert(user_email, symbol, total_oi_change, threshold, time_ist):
    """Send email alert for total OI changes"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = user_email
        msg['Subject'] = f"🟡 Alert: Total OI Change for {symbol}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
            <div style="background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #f59e0b;">
                <h2 style="color: #f59e0b; margin-top: 0;">🟡 Total OI Change Alert</h2>
                
                <div style="background-color: #fffbeb; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="margin-top: 0; color: #f59e0b;">Options Chain Alert</h3>
                    <p><strong>Symbol:</strong> {symbol}</p>
                    <p><strong>Total OI Change:</strong> <span style="color: #f59e0b; font-weight: bold;">{total_oi_change:,} lots</span></p>
                    <p><strong>Threshold:</strong> {threshold:,} lots</p>
                    <p><strong>Time (IST):</strong> {time_ist}</p>
                </div>
                
                <p style="margin-top: 20px; font-size: 14px; color: #6c757d;">
                    This alert was triggered because the total OI change exceeded the threshold (either positive or negative).
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USER, user_email, text)
        server.quit()
        
        print(f"Total OI alert sent to {user_email} for {symbol}")
        return True
    except Exception as e:
        print(f"Failed to send total OI alert: {e}")
        return False

def send_volume_comparison_alert(user_email, symbol, today_volume, tomorrow_volume, multiplier, time_ist):
    """Send email alert for volume comparison"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = user_email
        msg['Subject'] = f"🟢 Alert: Volume Comparison for {symbol}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
            <div style="background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #10b981;">
                <h2 style="color: #10b981; margin-top: 0;">🟢 Volume Comparison Alert</h2>
                
                <div style="background-color: #ecfdf5; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="margin-top: 0; color: #10b981;">Options Chain Alert</h3>
                    <p><strong>Symbol:</strong> {symbol}</p>
                    <p><strong>Today's End Volume:</strong> <span style="color: #10b981; font-weight: bold;">{today_volume:,} lots</span></p>
                    <p><strong>Tomorrow's Volume:</strong> {tomorrow_volume:,} lots</p>
                    <p><strong>Multiplier:</strong> {multiplier}x</p>
                    <p><strong>Time (IST):</strong> {time_ist}</p>
                </div>
                
                <p style="margin-top: 20px; font-size: 14px; color: #6c757d;">
                    This alert was triggered because today's end volume is {multiplier}x times tomorrow's volume.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USER, user_email, text)
        server.quit()
        
        print(f"Volume comparison alert sent to {user_email} for {symbol}")
        return True
    except Exception as e:
        print(f"Failed to send volume comparison alert: {e}")
        return False



def store_alert(user_email, alert_data):
    """Store alert in MongoDB"""
    try:
        alert_doc = {
            'user_email': user_email,
            'timestamp': datetime.now(),
            'symbol': alert_data['symbol'],
            'strike': alert_data.get('strike'),
            'option_type': alert_data.get('option_type'),
            'alert_type': alert_data['alert_type'],
            'oi_change': alert_data.get('oi_change'),
            'threshold': alert_data.get('threshold'),
            'total_oi_change': alert_data.get('total_oi_change'),
            'today_volume': alert_data.get('today_volume'),
            'tomorrow_volume': alert_data.get('tomorrow_volume'),
            'multiplier': alert_data.get('multiplier'),
            'status': 'sent'
        }
        
        alerts_collection.insert_one(alert_doc)
        print(f"Alert stored for {user_email}: {alert_data['alert_type']} alert for {alert_data['symbol']}")
        return True
    except Exception as e:
        print(f"Error storing alert: {e}")
        return False

def get_user_alerts(user_email, symbol=None, alert_type=None, from_date=None, to_date=None):
    """Get alerts for a user with optional filters"""
    try:
        # Build query
        query = {'user_email': user_email}
        
        if symbol:
            query['symbol'] = symbol
        
        if alert_type:
            query['alert_type'] = alert_type
        
        if from_date or to_date:
            date_query = {}
            if from_date:
                date_query['$gte'] = datetime.fromisoformat(from_date)
            if to_date:
                # Add one day to include the entire to_date
                to_date_obj = datetime.fromisoformat(to_date) + timedelta(days=1)
                date_query['$lt'] = to_date_obj
            query['timestamp'] = date_query
        
        # Get alerts sorted by timestamp (newest first)
        alerts = list(alerts_collection.find(query).sort('timestamp', -1))
        
        # Convert ObjectId to string for JSON serialization
        for alert in alerts:
            alert['_id'] = str(alert['_id'])
            alert['timestamp'] = alert['timestamp'].isoformat()
        
        return alerts
    except Exception as e:
        print(f"Error getting alerts: {e}")
        return []

def load_all_user_alert_settings():
    """Load alert settings for all users from database"""
    try:
        # Get all users from the database
        all_users = list(users_collection.find({}, {'email': 1}))
        
        for user in all_users:
            user_email = user['email']
            
            # Get user's alert settings from database
            user_settings = user_alert_settings.get(user_email, {
                'enabled': False,
                'negative_oi_threshold': -100,
                'total_oi_threshold': 1500,
                'volume_multiplier': 2,
                'cooldown': 300,
                'alert_calls': True,
                'alert_puts': True
            })
            
            # Store in background settings
            background_alert_settings[user_email] = user_settings
            
            # Initialize previous OI storage for this user
            if user_email not in background_previous_oi_values:
                background_previous_oi_values[user_email] = {}
        
        print(f"✅ Loaded alert settings for {len(all_users)} users")
        return len(all_users)
    except Exception as e:
        print(f"Error loading user alert settings: {e}")
        return 0

def is_market_open():
    """Check if NSE market is currently open (9:15 AM to 3:30 PM IST)"""
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    current_time = now.time()
    
    # Market hours: 9:15 AM to 3:30 PM IST
    market_open = datetime_time(9, 15)
    market_close = datetime_time(15, 30)
    
    # Check if current time is within market hours
    is_open = market_open <= current_time <= market_close
    
    # Also check if it's a weekday (Monday=0, Sunday=6)
    is_weekday = now.weekday() < 5
    
    # Log market status for debugging
    status = "OPEN" if (is_open and is_weekday) else "CLOSED"
    print(f"🕐 Market Status: {status} | Time: {current_time.strftime('%H:%M')} IST | Weekday: {is_weekday}")
    
    return is_open and is_weekday

def is_market_hours():
    """Check if current time is within market hours (9 AM to 4 PM IST)"""
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist_timezone).time()
    market_start = datetime_time(9, 0)  # 9 AM
    market_end = datetime_time(16, 0)   # 4 PM
    return market_start <= current_time <= market_end

def is_weekday():
    """Check if current day is a weekday (Monday to Friday)"""
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_weekday = datetime.now(ist_timezone).weekday()
    return current_weekday < 5  # Monday = 0, Friday = 4

def collect_historical_data():
    """Collect historical data for all major symbols every 2 minutes during market hours"""
    if not is_market_open() or not is_weekday():
        print("Market is closed - skipping data collection")
        return
    
    try:
        # Collect data for major indices only to save storage
        major_symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
        
        for symbol in major_symbols:
            try:
                # Get current expiry date
                expiry_dates = get_expiry_dates(symbol)
                if not expiry_dates:
                    continue
                
                expiry_date = expiry_dates[0]  # Use first expiry
                
                # Get options data
                options_data = get_kiteconnect_data(symbol, expiry_date)
                if options_data:
                    # Store historical data
                    store_historical_data(symbol, expiry_date, options_data)
                    print(f"📊 Collected historical data for {symbol} at {datetime.now().strftime('%H:%M:%S')}")
                
            except Exception as e:
                print(f"Error collecting data for {symbol}: {e}")
        
    except Exception as e:
        print(f"Error in historical data collection: {e}")

def scheduled_data_collection():
    """Background thread for scheduled data collection"""
    while True:
        try:
            collect_historical_data()
            # Wait for 2 minutes (120 seconds)
            time.sleep(120)
        except Exception as e:
            print(f"Error in scheduled data collection: {e}")
            time.sleep(60)  # Wait 1 minute on error

def process_background_alerts_for_all_users(symbol, options_data):
    """Process alerts for all users automatically"""
    if not options_data or not background_alert_settings:
        return
    
    # Define major indices that should not trigger alerts
    major_indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
    
    # Skip alerts for major indices
    if symbol in major_indices:
        return
    
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist_timezone).strftime("%Y-%m-%d %H:%M:%S IST")
    current_timestamp = datetime.now().timestamp()
    
    # Process alerts for each user
    for user_email, user_settings in background_alert_settings.items():
        if not user_settings.get('enabled', False):
            continue
        
        # Check cooldown for all alert types
        if user_email in last_email_sent and (current_timestamp - last_email_sent[user_email]) < user_settings.get('cooldown', 300):
            continue
        
        # 1. NEGATIVE OI CHANGE ALERT (within 10 strikes of current price)
        negative_oi_alerts = []
        current_price = options_data['current_price']
        
        # Find strikes within 10 strikes of current price
        strikes_to_check = []
        for i, call in enumerate(options_data['calls']):
            if abs(call['strike'] - current_price) <= 500:  # 10 strikes * 50 = 500 points
                strikes_to_check.append(i)
        
        # Check calls if enabled
        if user_settings.get('alert_calls', True):
            for i in strikes_to_check:
                call = options_data['calls'][i]
                strike = call['strike']
                oi_change = call['oi_chg']  # OI change in contracts
                oi_change_lots = call.get('oi_chg_lots', calculate_oi_in_lots(oi_change, symbol))
                
                # Check negative OI threshold
                threshold_contracts = user_settings.get('negative_oi_threshold', -100) * get_lot_size_from_api(symbol)
                if oi_change < threshold_contracts:
                    negative_oi_alerts.append({
                        'type': 'CE',
                        'strike': strike,
                        'oi_change': oi_change_lots
                    })
        
        # Check puts if enabled
        if user_settings.get('alert_puts', True):
            for i in strikes_to_check:
                put = options_data['puts'][i]
                strike = put['strike']
                oi_change = put['oi_chg']  # OI change in contracts
                oi_change_lots = put.get('oi_chg_lots', calculate_oi_in_lots(oi_change, symbol))
                
                # Check negative OI threshold
                threshold_contracts = user_settings.get('negative_oi_threshold', -100) * get_lot_size_from_api(symbol)
                if oi_change < threshold_contracts:
                    negative_oi_alerts.append({
                        'type': 'PE',
                        'strike': strike,
                        'oi_change': oi_change_lots
                    })
        
        # Send negative OI alerts
        for alert in negative_oi_alerts:
            if send_negative_oi_alert(
                user_email,
                symbol,
                alert['strike'],
                alert['type'],
                alert['oi_change'],
                user_settings.get('negative_oi_threshold', -100),
                current_time
            ):
                store_alert(user_email, {
                    'symbol': symbol,
                    'strike': alert['strike'],
                    'option_type': alert['type'],
                    'alert_type': 'negative_oi',
                    'oi_change': alert['oi_change'],
                    'threshold': user_settings.get('negative_oi_threshold', -100)
                })
                last_email_sent[user_email] = current_timestamp
                break
        
        # 2. TOTAL OI CHANGE ALERT
        total_ce_oi_change = sum(call['oi_chg'] for call in options_data['calls'])
        total_pe_oi_change = sum(put['oi_chg'] for put in options_data['puts'])
        total_oi_change = total_ce_oi_change + total_pe_oi_change
        total_oi_change_lots = calculate_oi_in_lots(total_oi_change, symbol)
        
        threshold_contracts = user_settings.get('total_oi_threshold', 1500) * get_lot_size_from_api(symbol)
        if abs(total_oi_change) > threshold_contracts:
            if send_total_oi_alert(
                user_email,
                symbol,
                total_oi_change_lots,
                user_settings.get('total_oi_threshold', 1500),
                current_time
            ):
                store_alert(user_email, {
                    'symbol': symbol,
                    'alert_type': 'total_oi',
                    'total_oi_change': total_oi_change_lots,
                    'threshold': user_settings.get('total_oi_threshold', 1500)
                })
                last_email_sent[user_email] = current_timestamp
        
        # 3. VOLUME COMPARISON ALERT (end of day comparison)
        # This will be implemented when we have historical data for comparison
        # For now, we'll skip this as it requires end-of-day data collection
        
        # Note: Volume comparison alert requires:
        # - Today's end volume (around 3:30 PM)
        # - Tomorrow's volume data
        # - Comparison logic
        # This will be implemented in a separate function that runs at end of day

@app.route('/')
def index():
    """Homepage with intro and navigation buttons"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login form and authentication"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        user = users_collection.find_one({'email': email, 'password': password})
        
        if user is not None:
            session['user_id'] = str(user['_id'])
            session['email'] = email
            return redirect(url_for('options_chain'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup form and user registration"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user is not None:
            return render_template('signup.html', error="User already exists")
        
        # Create new user (no password hashing as specified)
        user_data = {
            'email': email,
            'password': password
        }
        users_collection.insert_one(user_data)
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/options-chain')
def options_chain():
    """Main dashboard - protected route"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('options_chain.html', symbols=NSE_SYMBOLS)

@app.route('/get-expiry-dates')
def get_expiry_dates_route():
    """JSON endpoint to get available expiry dates for a symbol"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    symbol = request.args.get('symbol', 'NIFTY')
    expiry_dates = get_expiry_dates(symbol)
    
    print(f"Expiry dates for {symbol}: {expiry_dates}")  # Debug print
    
    return jsonify({
        'symbol': symbol,
        'expiry_dates': expiry_dates
    })

@app.route('/save-alert-settings', methods=['POST'])
def save_alert_settings():
    """Save user alert settings"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        user_email = session['email']
        
        # Update user alert settings
        user_alert_settings[user_email] = {
            'enabled': data.get('enabled', False),
            'negative_oi_threshold': data.get('negativeOIThreshold', -100),
            'total_oi_threshold': data.get('totalOIThreshold', 1500),
            'volume_multiplier': data.get('volumeMultiplier', 2),
            'cooldown': data.get('cooldown', 300),
            'alert_calls': data.get('alertCalls', True),
            'alert_puts': data.get('alertPuts', True)
        }
        
        # Also update background alert settings
        background_alert_settings[user_email] = user_alert_settings[user_email]
        
        print(f"Alert settings saved for {user_email}: {user_alert_settings[user_email]}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error saving alert settings: {e}")
        return jsonify({'error': 'Failed to save settings'}), 500

@app.route('/get-alert-settings')
def get_alert_settings():
    """Get user alert settings"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_email = session['email']
    settings = user_alert_settings.get(user_email, {
        'enabled': False,
        'negative_oi_threshold': -100,
        'total_oi_threshold': 1500,
        'volume_multiplier': 2,
        'cooldown': 300,
        'alert_calls': True,
        'alert_puts': True
    })
    
    return jsonify(settings)

@app.route('/reload-alert-settings')
def reload_alert_settings():
    """Reload alert settings for all users (admin function)"""
    try:
        count = load_all_user_alert_settings()
        return jsonify({
            'success': True,
            'message': f'Reloaded alert settings for {count} users',
            'users_with_alerts': len([u for u in background_alert_settings.values() if u.get('enabled', False)])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-option-data')
def get_option_data():
    """JSON endpoint for frontend to fetch updated option chain"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    symbol = request.args.get('symbol', 'NIFTY')
    
    # Get expiry date from request
    expiry_date = request.args.get('expiry', None)
    
    # Get volume display preference (contracts or lots)
    show_volume_in_lots = request.args.get('volume_mode', 'lots').lower() == 'lots'
    
    # Get options data
    options_data = get_kiteconnect_data(symbol, expiry_date)
    
    # Store historical data
    if options_data:
        store_historical_data(symbol, expiry_date, options_data)
    
    # Process background alerts for all users (regardless of login status)
    process_background_alerts_for_all_users(symbol, options_data)
    
    # Check for alerts based on user settings (new alert system)
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist_timezone).strftime("%Y-%m-%d %H:%M:%S IST")
    
    user_email = session['email']
    user_settings = user_alert_settings.get(user_email, {
        'enabled': False,
        'negative_oi_threshold': -100,
        'total_oi_threshold': 1500,
        'volume_multiplier': 2,
        'cooldown': 300,
        'alert_calls': True,
        'alert_puts': True
    })
    
    # Define major indices that should not trigger alerts
    major_indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
    
    # Only check for alerts if user has enabled them and symbol is not a major index
    if user_settings['enabled'] and symbol not in major_indices:
        current_timestamp = datetime.now().timestamp()
        
        # Check cooldown for all alert types
        if user_email in last_email_sent and (current_timestamp - last_email_sent[user_email]) < user_settings.get('cooldown', 300):
            pass  # Skip alerts due to cooldown
        else:
            # 1. NEGATIVE OI CHANGE ALERT (within 10 strikes of current price)
            negative_oi_alerts = []
            current_price = options_data['current_price']
            
            # Find strikes within 10 strikes of current price
            strikes_to_check = []
            for i, call in enumerate(options_data['calls']):
                if abs(call['strike'] - current_price) <= 500:  # 10 strikes * 50 = 500 points
                    strikes_to_check.append(i)
            
            # Check calls if enabled
            if user_settings.get('alert_calls', True):
                for i in strikes_to_check:
                    call = options_data['calls'][i]
                    strike = call['strike']
                    oi_change = call['oi_chg']  # OI change in contracts
                    oi_change_lots = call.get('oi_chg_lots', calculate_oi_in_lots(oi_change, symbol))
                    
                    # Check negative OI threshold
                    threshold_contracts = user_settings.get('negative_oi_threshold', -100) * get_lot_size_from_api(symbol)
                    if oi_change < threshold_contracts:
                        negative_oi_alerts.append({
                            'type': 'CE',
                            'strike': strike,
                            'oi_change': oi_change_lots
                        })
            
            # Check puts if enabled
            if user_settings.get('alert_puts', True):
                for i in strikes_to_check:
                    put = options_data['puts'][i]
                    strike = put['strike']
                    oi_change = put['oi_chg']  # OI change in contracts
                    oi_change_lots = put.get('oi_chg_lots', calculate_oi_in_lots(oi_change, symbol))
                    
                    # Check negative OI threshold
                    threshold_contracts = user_settings.get('negative_oi_threshold', -100) * get_lot_size_from_api(symbol)
                    if oi_change < threshold_contracts:
                        negative_oi_alerts.append({
                            'type': 'PE',
                            'strike': strike,
                            'oi_change': oi_change_lots
                        })
            
            # Send negative OI alerts
            for alert in negative_oi_alerts:
                if send_negative_oi_alert(
                    user_email,
                    symbol,
                    alert['strike'],
                    alert['type'],
                    alert['oi_change'],
                    user_settings.get('negative_oi_threshold', -100),
                    current_time
                ):
                    store_alert(user_email, {
                        'symbol': symbol,
                        'strike': alert['strike'],
                        'option_type': alert['type'],
                        'alert_type': 'negative_oi',
                        'oi_change': alert['oi_change'],
                        'threshold': user_settings.get('negative_oi_threshold', -100)
                    })
                    last_email_sent[user_email] = current_timestamp
                    break
            
            # 2. TOTAL OI CHANGE ALERT
            total_ce_oi_change = sum(call['oi_chg'] for call in options_data['calls'])
            total_pe_oi_change = sum(put['oi_chg'] for put in options_data['puts'])
            total_oi_change = total_ce_oi_change + total_pe_oi_change
            total_oi_change_lots = calculate_oi_in_lots(total_oi_change, symbol)
            
            threshold_contracts = user_settings.get('total_oi_threshold', 1500) * get_lot_size_from_api(symbol)
            if abs(total_oi_change) > threshold_contracts:
                if send_total_oi_alert(
                    user_email,
                    symbol,
                    total_oi_change_lots,
                    user_settings.get('total_oi_threshold', 1500),
                    current_time
                ):
                    store_alert(user_email, {
                        'symbol': symbol,
                        'alert_type': 'total_oi',
                        'total_oi_change': total_oi_change_lots,
                        'threshold': user_settings.get('total_oi_threshold', 1500)
                    })
                    last_email_sent[user_email] = current_timestamp
            
            # 3. VOLUME COMPARISON ALERT (end of day comparison)
            # This will be implemented when we have historical data for comparison
            # For now, we'll skip this as it requires end-of-day data collection
            
            # Note: Volume comparison alert requires:
            # - Today's end volume (around 3:30 PM)
            # - Tomorrow's volume data
            # - Comparison logic
            # This will be implemented in a separate function that runs at end of day
    elif symbol in major_indices:
        print(f"⚠️ Alerts skipped for major index: {symbol}")
    
    return jsonify(options_data)

@app.route('/historical-data')
def historical_data_page():
    """Historical data page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('historical_data.html', symbols=NSE_SYMBOLS)

@app.route('/alerts')
def alerts_page():
    """Alerts history page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('alerts.html', symbols=NSE_SYMBOLS)

@app.route('/get-alerts-history')
def get_alerts_history():
    """Get alerts history for the current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_email = session['email']
        
        # Get query parameters
        symbol = request.args.get('symbol')
        alert_type = request.args.get('alert_type')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Get alerts
        alerts = get_user_alerts(user_email, symbol, alert_type, from_date, to_date)
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total_count': len(alerts)
        })
        
    except Exception as e:
        print(f"Error getting alerts history: {e}")
        return jsonify({'error': 'Failed to get alerts'}), 500

@app.route('/get-historical-data')
def get_historical_data_route():
    """Get historical data for specified filters"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    symbol = request.args.get('symbol', 'NIFTY')
    expiry_date = request.args.get('expiry', '29AUG25')
    date_filter = request.args.get('date', None)
    time_range = request.args.get('time_range', 'all')
    start_time = request.args.get('start_time', '09:00')
    end_time = request.args.get('end_time', '16:00')
    
    historical_data = get_historical_data(symbol, expiry_date, date_filter, time_range, start_time, end_time)
    
    return jsonify({
        'symbol': symbol,
        'expiry_date': expiry_date,
        'date_filter': date_filter,
        'time_range': time_range,
        'start_time': start_time,
        'end_time': end_time,
        'data': historical_data
    })

if __name__ == '__main__':
    # Verify symbols are properly organized
    verify_symbols_order()
    
    # Load all user alert settings
    load_all_user_alert_settings()
    
    # Start background data collection thread
    data_collection_thread = threading.Thread(target=scheduled_data_collection, daemon=True)
    data_collection_thread.start()
    print("Started background data collection thread")
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=Config.PORT) 