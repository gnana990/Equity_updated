# KiteConnect API Configuration
# Replace these values with your actual KiteConnect API credentials

# Your KiteConnect API Key
KITE_API_KEY = "tmp23p1tsmywqb5s"

# Your KiteConnect API Secret
KITE_API_SECRET = "d1lkd7orpowxrdm4ff6l4fnctp0cjmh9"

# Access Token (you'll get this after login)
KITE_ACCESS_TOKEN = "pgn2d2uNCDgt1nweUUhCkG7VAC44kmxM"

# Login URL for KiteConnect
KITE_LOGIN_URL = "https://kite.trade/connect/login"

# Redirect URL after login (updated for production)
KITE_REDIRECT_URL = "https://equity-updated.onrender.com/kite/callback"

# Request Token (you'll get this from the redirect URL)
KITE_REQUEST_TOKEN = "your_request_token_here"

# Example usage:
# from kiteconnect import KiteConnect
# kite = KiteConnect(api_key=KITE_API_KEY)
# kite.set_access_token(KITE_ACCESS_TOKEN)

# Import KiteConnect for API integration
from kiteconnect import KiteConnect
from datetime import datetime
import logging

# Cache for lot sizes and expiry dates to avoid repeated API calls
_lot_sizes_cache = {}
_expiry_dates_cache = {}
_instruments_cache = None
_cache_timestamp = None

# Cache duration in seconds (5 minutes)
CACHE_DURATION = 300

def get_kite_instance():
    """Get KiteConnect instance with access token"""
    try:
        kite = KiteConnect(api_key=KITE_API_KEY)
        kite.set_access_token(KITE_ACCESS_TOKEN)
        return kite
    except Exception as e:
        logging.error(f"Error creating KiteConnect instance: {e}")
        return None

def get_instruments_from_api():
    """Get all NFO instruments from KiteConnect API with caching"""
    global _instruments_cache, _cache_timestamp
    
    current_time = datetime.now().timestamp()
    
    # Check if cache is valid
    if (_instruments_cache is not None and 
        _cache_timestamp is not None and 
        (current_time - _cache_timestamp) < CACHE_DURATION):
        return _instruments_cache
    
    try:
        kite = get_kite_instance()
        if kite is None:
            return None
            
        # Get NFO instruments
        instruments = kite.instruments("NFO")
        
        # Update cache
        _instruments_cache = instruments
        _cache_timestamp = current_time
        
        logging.info(f"Fetched {len(instruments)} NFO instruments from API")
        return instruments
        
    except Exception as e:
        logging.error(f"Error fetching instruments from API: {e}")
        return None

def get_lot_size_from_api(symbol):
    """Get lot size for a symbol from KiteConnect API"""
    global _lot_sizes_cache
    
    # Check cache first
    if symbol in _lot_sizes_cache:
        return _lot_sizes_cache[symbol]
    
    try:
        instruments = get_instruments_from_api()
        if instruments is None:
            return 50  # Fallback default
        
        # Find the symbol in instruments
        for instrument in instruments:
            if instrument['name'] == symbol and instrument['instrument_type'] in ['CE', 'PE']:
                lot_size = instrument['lot_size']
                _lot_sizes_cache[symbol] = lot_size
                return lot_size
        
        # If symbol not found, return default based on symbol type
        default_lot_sizes = {
            "NIFTY": 50,
            "BANKNIFTY": 25,
            "FINNIFTY": 40,
            "MIDCPNIFTY": 75,
            "SENSEX": 10
        }
        
        lot_size = default_lot_sizes.get(symbol, 50)
        _lot_sizes_cache[symbol] = lot_size
        return lot_size
        
    except Exception as e:
        logging.error(f"Error getting lot size for {symbol}: {e}")
        # Return reasonable defaults
        if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]:
            return {"NIFTY": 50, "BANKNIFTY": 25, "FINNIFTY": 40, "MIDCPNIFTY": 75, "SENSEX": 10}.get(symbol, 50)
        return 50

def get_expiry_dates_from_api(symbol):
    """Get expiry dates for a symbol from KiteConnect API"""
    global _expiry_dates_cache
    
    # Check cache first
    cache_key = symbol
    if cache_key in _expiry_dates_cache:
        return _expiry_dates_cache[cache_key]
    
    try:
        instruments = get_instruments_from_api()
        if instruments is None:
            return []
        
        # Filter instruments for the specific symbol
        symbol_instruments = [inst for inst in instruments 
                            if inst['name'] == symbol and 
                            inst['instrument_type'] in ['CE', 'PE'] and
                            inst['expiry'] is not None]
        
        if not symbol_instruments:
            return []
        
        # Extract unique expiry dates
        expiry_dates = list(set([inst['expiry'] for inst in symbol_instruments]))
        expiry_dates.sort()  # Sort by date
        
        # Format dates as DDMMMYY (e.g., 28AUG25)
        formatted_dates = []
        for date in expiry_dates:
            if date:
                formatted_date = date.strftime("%d%b%y").upper()
                formatted_dates.append(formatted_date)
        
        # Cache the result
        _expiry_dates_cache[cache_key] = formatted_dates
        
        logging.info(f"Found {len(formatted_dates)} expiry dates for {symbol}")
        return formatted_dates
        
    except Exception as e:
        logging.error(f"Error getting expiry dates for {symbol}: {e}")
        return []

def get_current_price_from_api(symbol):
    """Get current market price for a symbol from KiteConnect API"""
    try:
        kite = get_kite_instance()
        if kite is None:
            logging.error("KiteConnect instance not available")
            return None
            
        # Get quote for NSE symbol - try different formats
        quote_keys = [f"NSE:{symbol}", symbol]
        quotes = None
        
        for key in quote_keys:
            try:
                quotes = kite.quote([key])
                if quotes and key in quotes:
                    quote_key = key
                    break
            except:
                continue
        
        if quotes and quote_key in quotes:
            quote_data = quotes[quote_key]
            # Return the last traded price (LTP)
            ltp = quote_data.get('last_price', 0)
            logging.info(f"{symbol} LTP: Rs.{ltp}")
            return ltp
        else:
            logging.warning(f"No quote data found for {symbol}")
            return None
        
    except Exception as e:
        logging.error(f"Error getting current price for {symbol}: {e}")
        return None

def get_options_data_from_api(symbol, expiry_date):
    """Get options chain data from KiteConnect API with proper NSE data mapping"""
    try:
        kite = get_kite_instance()
        if kite is None:
            logging.error("KiteConnect instance not available")
            return None
            
        instruments = get_instruments_from_api()
        if instruments is None:
            logging.error("Instruments data not available")
            return None
        
        # Convert expiry_date string to datetime object for comparison
        try:
            expiry_dt = datetime.strptime(expiry_date, "%d%b%y")
        except ValueError:
            logging.error(f"Invalid expiry date format: {expiry_date}")
            return None
        
        # Filter instruments for the specific symbol and expiry
        symbol_instruments = [inst for inst in instruments 
                            if inst['name'] == symbol and 
                            inst['expiry'] is not None and
                            inst['expiry'] == expiry_dt and
                            inst['instrument_type'] in ['CE', 'PE']]
        
        if not symbol_instruments:
            logging.warning(f"No instruments found for {symbol} expiry {expiry_date}")
            return None
        
        logging.info(f"Found {len(symbol_instruments)} instruments for {symbol} {expiry_date}")
        
        # Get instrument tokens
        instrument_tokens = [inst['instrument_token'] for inst in symbol_instruments]
        
        # Get quotes for all instruments
        quotes = kite.quote(instrument_tokens)
        
        calls = []
        puts = []
        
        # Process the quotes and map to NSE format
        for inst in symbol_instruments:
            token = inst['instrument_token']
            if token not in quotes:
                continue
                
            quote = quotes[token]
            strike = inst['strike']
            
            # Extract NSE-compatible data
            option_data = {
                'strike': strike,
                'ltp': quote.get('last_price', 0),
                'bid': quote.get('depth', {}).get('buy', [{}])[0].get('price', 0) if quote.get('depth', {}).get('buy') else 0,
                'ask': quote.get('depth', {}).get('sell', [{}])[0].get('price', 0) if quote.get('depth', {}).get('sell') else 0,
                'volume': quote.get('volume', 0),
                'oi': quote.get('oi', 0),
                'oi_chg': quote.get('oi_day_high', 0) - quote.get('oi_day_low', 0),  # Approximation
                'change': quote.get('net_change', 0),
                'pchange': quote.get('percentage_change', 0)
            }
            
            if inst['instrument_type'] == 'CE':
                calls.append(option_data)
            else:
                puts.append(option_data)
        
        # Sort by strike price
        calls.sort(key=lambda x: x['strike'])
        puts.sort(key=lambda x: x['strike'])
        return {
            'calls': calls,
            'puts': puts
        }
        
    except Exception as e:
        logging.error(f"Error getting options data for {symbol}: {e}")
        return None

def test_api_connection():
    """Test KiteConnect API connection and display sample data"""
    try:
        kite = get_kite_instance()
        if kite is None:
            print("Failed to create KiteConnect instance")
            return False
        
        # Test profile
        profile = kite.profile()
        print("API Connection successful!")
        print(f"User: {profile['user_name']} ({profile['email']})")
        print(f"Available margin: Rs.{profile.get('net', 'N/A')}")
        
        # Test instruments
        instruments = get_instruments_from_api()
        if instruments:
            print(f"Instruments loaded: {len(instruments)} NFO instruments")
        
        # Test lot size
        nifty_lot_size = get_lot_size_from_api("NIFTY")
        print(f"NIFTY lot size: {nifty_lot_size}")
        
        # Test expiry dates
        nifty_expiries = get_expiry_dates_from_api("NIFTY")
        if nifty_expiries:
            print(f"NIFTY expiry dates: {nifty_expiries[:3]}")
        
        # Test current price
        nifty_price = get_current_price_from_api("NIFTY")
        if nifty_price:
            print(f"NIFTY current price: Rs.{nifty_price}")
        
        return True
        
    except Exception as e:
        print(f"API connection test failed: {e}")
        return False 