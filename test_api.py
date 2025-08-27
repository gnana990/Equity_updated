#!/usr/bin/env python3
"""
Test KiteConnect API Integration
Run this script to verify your API connection and data fetching
"""

from kiteconnect_config import test_api_connection, get_options_data_from_api, get_expiry_dates_from_api

def main():
    print("Testing KiteConnect API Integration")
    print("=" * 60)
    
    # Test basic connection
    if not test_api_connection():
        print("\nBasic API connection failed. Please check your credentials.")
        return
    
    print("\n" + "="*60)
    print("Testing Options Data Fetching...")
    
    # Test options data
    symbol = "NIFTY"
    expiry_dates = get_expiry_dates_from_api(symbol)
    
    if not expiry_dates:
        print(f"No expiry dates found for {symbol}")
        return
    
    expiry = expiry_dates[0]
    print(f"Testing with {symbol} expiry: {expiry}")
    
    options_data = get_options_data_from_api(symbol, expiry)
    
    if options_data:
        calls = options_data.get('calls', [])
        puts = options_data.get('puts', [])
        
        print(f"Options data fetched successfully!")
        print(f"Calls: {len(calls)} strikes")
        print(f"Puts: {len(puts)} strikes")
        
        if calls:
            sample_call = calls[len(calls)//2]  # Middle strike
            print(f"\nSample Call Data (Strike {sample_call['strike']}):")
            print(f"   OI: {sample_call['oi']:,} contracts")
            print(f"   OI Change: {sample_call['oi_chg']:,} contracts")
            print(f"   Volume: {sample_call['volume']:,} contracts")
            print(f"   LTP: Rs.{sample_call['ltp']}")
            print(f"   Bid: Rs.{sample_call['bid']}")
            print(f"   Ask: Rs.{sample_call['ask']}")
        
        if puts:
            sample_put = puts[len(puts)//2]  # Middle strike
            print(f"\nSample Put Data (Strike {sample_put['strike']}):")
            print(f"   OI: {sample_put['oi']:,} contracts")
            print(f"   OI Change: {sample_put['oi_chg']:,} contracts")
            print(f"   Volume: {sample_put['volume']:,} contracts")
            print(f"   LTP: Rs.{sample_put['ltp']}")
            print(f"   Bid: Rs.{sample_put['bid']}")
            print(f"   Ask: Rs.{sample_put['ask']}")
        
        print(f"\nAPI Integration Test: PASSED")
        print(f"Your application is ready to fetch live NSE data!")
        
    else:
        print(f"Failed to fetch options data for {symbol} {expiry}")
        print(f"This might be due to:")
        print(f"   • Market is closed")
        print(f"   • Invalid expiry date")
        print(f"   • API rate limits")

if __name__ == "__main__":
    main()
