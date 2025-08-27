# NSE Equity Project - Professional Options Trading Platform

A comprehensive options trading platform with real-time NSE options chain analysis, live data updates, and intelligent alerting system.

## Features

### Real-time Data
- Live options chain updates every 1 minute
- Comprehensive OI, volume, and price change tracking
- Support for 200+ NSE symbols including NIFTY, BANKNIFTY, and individual stocks
- **Organized dropdown**: Major indices (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX) appear first, followed by all other symbols in alphabetical order

### Advanced Analytics
- Interactive charts and historical data analysis
- Put-Call Ratio calculations
- Professional-grade visualization tools

### Smart Alert System
- **Regular Alerts**: Email notifications when OI change goes below a user-defined threshold
- **🚨 Special Alerts**: Critical email alerts for sudden major OI drops (e.g., -1500 to -3000, -4500 to -7000)
- **Alerts History Page**: Comprehensive table view of all alerts with filtering and search capabilities
- **Major Indices Excluded**: Alerts are disabled for NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX to reduce noise
- **Background Alert System**: Alerts are sent to all signed-up users automatically, even when not logged in
- Customizable alert thresholds and cooldown periods
- Separate alerts for CALLS (CE) and PUTS (PE)
- Intelligent cooldown system to prevent spam

### Historical Data
- Comprehensive historical data storage
- Interactive charts with time-range analysis
- Strategic decision-making tools

### Professional UI
- Modern glassmorphism design (configurable)
- Responsive layout with real-time updates
- Intuitive navigation for seamless trading experience

## Special Alert System

The platform includes a sophisticated alert system with two types of notifications:

### Regular Alerts
- Triggers when OI change goes below a user-defined threshold (default: -100)
- Standard email notification with basic information

### Special Alerts 🚨
- **Purpose**: Detects sudden major OI changes that indicate significant market movements
- **Trigger**: When OI drops by more than the special threshold in one update (default: -1500)
- **Examples**: 
  - OI changes from 5000 to 2000 (drop of 3000)
  - OI changes from 8000 to 1000 (drop of 7000)
- **Features**:
  - Priority alerts with enhanced email formatting
  - Separate cooldown system from regular alerts
  - Detailed information including previous and current OI values
  - Visual indicators in the alert settings

### Alert Configuration
Users can configure:
- Enable/disable alerts
- Regular alert threshold (default: -100)
- Special alert threshold (default: -1500)
- Alert cooldown period (1-60 minutes)
- Alert types (CALLS, PUTS, or both)

**Note**: Alerts are automatically disabled for major indices (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX) to reduce noise and focus on individual stock movements.

### Background Alert System
The platform includes an advanced background alert system that ensures all signed-up users receive alerts automatically:

#### **How It Works**
- **Automatic Processing**: Alerts are processed for all users every time data is fetched
- **No Login Required**: Users receive alerts even when not logged into the web interface
- **Settings Persistence**: Alert settings are stored in the database and loaded on startup
- **Real-time Monitoring**: Continuous monitoring of all symbols for all users

#### **Benefits**
- **Always Active**: Alerts work 24/7 regardless of user login status
- **Comprehensive Coverage**: All users with enabled alerts receive notifications
- **Efficient Processing**: Single data fetch serves all users simultaneously
- **Reliable Delivery**: Background system ensures no alerts are missed

#### **Technical Implementation**
- Background alert settings loaded on application startup
- Separate processing for each user's alert preferences
- Automatic cooldown management per user
- Database storage of all alert activities

### Alerts History Page
The platform includes a comprehensive alerts history page with the following features:

#### **Table View**
- **Date & Time**: When the alert was triggered (IST)
- **Symbol**: NSE symbol that triggered the alert
- **Strike**: Strike price of the option
- **Type**: Option type (CE/PE)
- **Alert Type**: Regular (-100) or Special (-1500) alert
- **OI Change**: The actual OI change value
- **Previous OI**: OI value before the change (for special alerts)
- **Current OI**: OI value after the change (for special alerts)
- **OI Drop**: Magnitude of the drop (for special alerts)
- **Status**: Alert delivery status

#### **Filtering Options**
- **Symbol Filter**: Filter by specific NSE symbols
- **Alert Type Filter**: Filter by regular or special alerts
- **Date Range**: Filter by from/to dates
- **Real-time Updates**: Auto-refresh every 30 seconds

#### **Statistics Dashboard**
- Total alerts count
- Regular alerts count
- Special alerts count
- Filtered results count

#### **Visual Indicators**
- **Regular Alerts**: Yellow background with warning icon
- **Special Alerts**: Red background with critical alert icon
- **Color-coded OI Changes**: Red for negative, green for positive

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure MongoDB connection
4. Set up SMTP settings for email alerts
5. Run the application: `python app.py`

## Usage

1. **Sign up/Login**: Create an account or login with existing credentials
2. **Configure Alerts**: Set up your alert preferences in the dashboard
3. **Monitor Data**: View real-time options chain data
4. **Receive Alerts**: Get email notifications for significant market movements
5. **Analyze History**: Review historical data for strategic insights

## Technical Details

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript with Tailwind CSS
- **Data Source**: KiteConnect API
- **Email**: SMTP with HTML formatting
- **Real-time Updates**: 1-minute intervals

## Alert Email Examples

### Regular Alert
```
Subject: Alert: Negative OI Change for NIFTY 19000 CE
Body: Basic information about the OI change
```

### Special Alert 🚨
```
Subject: 🚨 SPECIAL ALERT: Major OI Drop for NIFTY 19000 CE
Body: Enhanced HTML email with detailed information including:
- Previous OI value
- Current OI value
- OI change amount
- Strike price and option type
- Time of detection
- Market sentiment analysis
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License.