import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from PIL import Image
import io
import requests

# Set page config
st.set_page_config(
    page_title="Trading Journal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(45deg, #64ffda, #1de9b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .section-header {
        font-size: 1.5rem;
        color: #64ffda;
        border-bottom: 2px solid #64ffda;
        padding-bottom: 0.5rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: rgba(0, 20, 40, 0.6);
        border: 1px solid #64ffda;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .calendar-day {
        border: 2px solid #333;
        padding: 10px;
        height: 80px;
        margin: 2px;
        border-radius: 5px;
        background: rgba(0,20,40,0.3);
        text-align: center;
        cursor: pointer;
    }
    
    .trade-row {
        background: rgba(0, 20, 40, 0.3);
        border: 1px solid #333;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.2rem 0;
    }
    
    .balance-display {
        background: rgba(0, 20, 40, 0.8);
        border: 2px solid #64ffda;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .balance-amount {
        font-size: 1.8rem;
        font-weight: bold;
        color: #64ffda;
    }
</style>
""", unsafe_allow_html=True)

# GitHub API Configuration
class GitHubStorage:
    def __init__(self):
        self.token = None
        self.repo_owner = None
        self.repo_name = None
        self.connected = False
        self.base_url = "https://api.github.com"
        
    def connect(self, token, repo_owner, repo_name):
        """Connect to GitHub repository"""
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
        # Test connection
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/repos/{repo_owner}/{repo_name}",
                headers=headers
            )
            
            if response.status_code == 200:
                self.connected = True
                return True
            else:
                return False
        except:
            return False
    
    def get_file_content(self, file_path):
        """Get file content from GitHub repo"""
        if not self.connected:
            return None
            
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}",
                headers=headers
            )
            
            if response.status_code == 200:
                content = response.json()
                # Decode base64 content
                file_content = base64.b64decode(content['content']).decode('utf-8')
                return json.loads(file_content), content['sha']
            else:
                return None, None
        except Exception as e:
            return None, None
    
    def save_file_content(self, file_path, content, sha=None):
        """Save file content to GitHub repo"""
        if not self.connected:
            return False
            
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Encode content as base64
        content_encoded = base64.b64encode(json.dumps(content, indent=2, default=str).encode()).decode()
        
        data = {
            'message': f'Update {file_path}',
            'content': content_encoded
        }
        
        if sha:
            data['sha'] = sha
        
        try:
            response = requests.put(
                f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}",
                headers=headers,
                json=data
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            return False
    
    def upload_screenshot(self, image_data, filename, date_key):
        """Upload screenshot to GitHub repo"""
        if not self.connected:
            return None
            
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Create path for screenshot
        file_path = f"screenshots/{date_key}/{filename}"
        
        # Encode image as base64
        content_encoded = base64.b64encode(image_data).decode()
        
        data = {
            'message': f'Add screenshot {filename}',
            'content': content_encoded
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}",
                headers=headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                # Return the raw content URL for direct access
                return f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main/{file_path}"
            else:
                return None
        except Exception as e:
            return None
    
    def load_all_journal_data(self):
        """Load all journal data from GitHub repo"""
        if not self.connected:
            return {}
            
        # Try to get the main data file
        data, _ = self.get_file_content("trading_journal_data.json")
        return data if data else {}
    
    def save_journal_entry(self, date_key, entry_data, all_data):
        """Save journal entry to GitHub repo"""
        if not self.connected:
            return False
            
        # Get current file SHA
        _, sha = self.get_file_content("trading_journal_data.json")
        
        # Save the entire data structure
        return self.save_file_content("trading_journal_data.json", all_data, sha)

# Local fallback functions
def load_local_data():
    """Load data from local JSON file as fallback"""
    if os.path.exists("trading_journal_data.json"):
        try:
            with open("trading_journal_data.json", 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_local_data(data):
    """Save data to local JSON file as fallback"""
    with open("trading_journal_data.json", 'w') as f:
        json.dump(data, f, indent=2, default=str)

def get_date_key(date_obj=None):
    """Get date key in YYYY-MM-DD format"""
    if date_obj is None:
        date_obj = date.today()
    return date_obj.strftime("%Y-%m-%d")

def save_uploaded_file_local(uploaded_file, date_key, file_type):
    """Save uploaded file locally as fallback"""
    if uploaded_file is not None:
        os.makedirs(f"screenshots/{date_key}", exist_ok=True)
        file_extension = uploaded_file.name.split('.')[-1]
        filename = f"{file_type}_{uploaded_file.name}"
        filepath = f"screenshots/{date_key}/{filename}"
        
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return filepath
    return None

def display_image_full_size(image_source, caption="Screenshot"):
    """Display image at full size with option to expand"""
    if image_source:
        if image_source.startswith('http'):
            # For GitHub URLs, display directly
            st.image(image_source, caption=caption, use_container_width=True)
        elif os.path.exists(image_source):
            # For local files, display at full size
            try:
                image = Image.open(image_source)
                st.image(image, caption=caption, use_container_width=True)
            except:
                st.error(f"Could not load image: {image_source}")

def parse_trade_log(file_content):
    """Parse uploaded trade log file"""
    try:
        lines = file_content.strip().split('\n')
        if len(lines) < 2:
            return None, "File appears to be empty or invalid"
        
        # Try to detect delimiter
        header_line = lines[0]
        delimiter = '\t' if '\t' in header_line else ',' if ',' in header_line else None
        
        if not delimiter:
            return None, "Could not detect file format (expected CSV or TSV)"
        
        headers = header_line.split(delimiter)
        trades = []
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip():
                values = line.split(delimiter)
                if len(values) >= len(headers):
                    trade = {}
                    for j, header in enumerate(headers):
                        trade[header] = values[j] if j < len(values) else ''
                    trades.append(trade)
        
        return trades, None
    except Exception as e:
        return None, f"Error parsing file: {str(e)}"

def analyze_trades(trades):
    """Comprehensive trade analysis with winner/loser calculations"""
    if not trades:
        return {}
    
    analysis = {
        'total_fills': len(trades),
        'symbols': set(),
        'order_types': set(),
        'buy_orders': 0,
        'sell_orders': 0,
        'total_volume': 0,
        'prices': [],
        'times': [],
        'positions': [],
        'hourly_activity': {},
        'daily_pnl': 0,
        'win_rate': 0,
        'avg_trade_size': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'avg_winner': 0,
        'avg_loser': 0,
        'trade_pnls': []
    }
    
    # Process all fills first
    for trade in trades:
        # Basic counting
        buy_sell = trade.get('BuySell', '')
        if buy_sell == 'Buy':
            analysis['buy_orders'] += 1
        elif buy_sell == 'Sell':
            analysis['sell_orders'] += 1
        
        # Volume
        quantity = float(trade.get('Quantity', 0)) if trade.get('Quantity') else 0
        analysis['total_volume'] += quantity
        
        # Symbols and order types
        if trade.get('Symbol'):
            analysis['symbols'].add(trade.get('Symbol'))
        if trade.get('OrderType'):
            analysis['order_types'].add(trade.get('OrderType'))
        
        # Prices
        fill_price = float(trade.get('FillPrice', 0)) if trade.get('FillPrice') else 0
        if fill_price > 0:
            analysis['prices'].append(fill_price)
        
        # Time analysis
        datetime_str = trade.get('DateTime', '')
        if datetime_str and ' ' in datetime_str:
            time_part = datetime_str.split(' ')[1]
            if ':' in time_part:
                hour = time_part.split(':')[0]
                analysis['hourly_activity'][hour] = analysis['hourly_activity'].get(hour, 0) + 1
                analysis['times'].append(time_part)
        
        # Position tracking for P&L calculation
        pos_qty = float(trade.get('PositionQuantity', 0)) if trade.get('PositionQuantity') else 0
        analysis['positions'].append({
            'time': datetime_str,
            'symbol': trade.get('Symbol', ''),
            'action': buy_sell,
            'quantity': quantity,
            'price': fill_price,
            'position_qty': pos_qty,
            'open_close': trade.get('OpenClose', ''),
            'order_type': trade.get('OrderType', '')
        })
    
    # Calculate P&L and winner/loser statistics
    def get_point_value(symbol):
        if 'ENQU25' in symbol:
            return 20.0
        elif 'mNQU25' in symbol or 'MNQU25' in symbol:
            return 2.0
        else:
            return 1.0
    
    # Track individual trade P&Ls
    open_positions = {}
    individual_trade_pnls = []
    
    for pos in analysis['positions']:
        if not pos['time'] or pos['price'] <= 0:
            continue
            
        symbol = pos['symbol']
        point_value = get_point_value(symbol)
        
        if symbol not in open_positions:
            open_positions[symbol] = {'qty': 0, 'avg_price': 0, 'total_cost': 0}
        
        pnl_change = 0
        
        if pos['open_close'] == 'Open':
            if pos['action'] == 'Buy':
                new_total_cost = open_positions[symbol]['total_cost'] + (pos['quantity'] * pos['price'])
                new_qty = open_positions[symbol]['qty'] + pos['quantity']
                open_positions[symbol]['total_cost'] = new_total_cost
                open_positions[symbol]['qty'] = new_qty
                if new_qty != 0:
                    open_positions[symbol]['avg_price'] = new_total_cost / new_qty
            else:
                new_total_cost = open_positions[symbol]['total_cost'] - (pos['quantity'] * pos['price'])
                new_qty = open_positions[symbol]['qty'] - pos['quantity']
                open_positions[symbol]['total_cost'] = new_total_cost
                open_positions[symbol]['qty'] = new_qty
                if new_qty != 0:
                    open_positions[symbol]['avg_price'] = abs(new_total_cost / new_qty)
        
        elif pos['open_close'] == 'Close':
            if pos['action'] == 'Sell':
                if open_positions[symbol]['qty'] > 0:
                    avg_price = open_positions[symbol]['avg_price']
                    price_diff = pos['price'] - avg_price
                    pnl_change = pos['quantity'] * price_diff * point_value
                    
                    remaining_qty = open_positions[symbol]['qty'] - pos['quantity']
                    if remaining_qty > 0:
                        open_positions[symbol]['qty'] = remaining_qty
                        open_positions[symbol]['total_cost'] = remaining_qty * avg_price
                    else:
                        open_positions[symbol] = {'qty': 0, 'avg_price': 0, 'total_cost': 0}
            else:
                if open_positions[symbol]['qty'] < 0:
                    avg_price = open_positions[symbol]['avg_price']
                    price_diff = avg_price - pos['price']
                    pnl_change = pos['quantity'] * price_diff * point_value
                    
                    remaining_qty = open_positions[symbol]['qty'] + pos['quantity']
                    if remaining_qty < 0:
                        open_positions[symbol]['qty'] = remaining_qty
                        open_positions[symbol]['total_cost'] = remaining_qty * avg_price
                    else:
                        open_positions[symbol] = {'qty': 0, 'avg_price': 0, 'total_cost': 0}
        
        if pnl_change != 0:
            individual_trade_pnls.append(pnl_change)
    
    # Calculate winner/loser statistics
    if individual_trade_pnls:
        winners = [pnl for pnl in individual_trade_pnls if pnl > 0]
        losers = [pnl for pnl in individual_trade_pnls if pnl < 0]
        
        analysis['winning_trades'] = len(winners)
        analysis['losing_trades'] = len(losers)
        analysis['total_trades'] = len(individual_trade_pnls)
        analysis['trade_pnls'] = individual_trade_pnls
        analysis['daily_pnl'] = sum(individual_trade_pnls)
        
        if winners:
            analysis['avg_winner'] = sum(winners) / len(winners)
        if losers:
            analysis['avg_loser'] = sum(losers) / len(losers)
        
        if analysis['total_trades'] > 0:
            analysis['win_rate'] = (analysis['winning_trades'] / analysis['total_trades']) * 100
    
    # Calculate derived statistics
    if analysis['prices']:
        analysis['high_price'] = max(analysis['prices'])
        analysis['low_price'] = min(analysis['prices'])
        analysis['avg_price'] = sum(analysis['prices']) / len(analysis['prices'])
        analysis['price_range'] = analysis['high_price'] - analysis['low_price']
    
    if analysis['total_volume'] > 0:
        analysis['avg_trade_size'] = analysis['total_volume'] / analysis['total_fills']
    
    # Convert sets to lists for JSON serialization
    analysis['symbols'] = list(analysis['symbols'])
    analysis['order_types'] = list(analysis['order_types'])
    
    return analysis

# NEW: Account Balance Functions
def calculate_running_balance(data, target_date, starting_balance, start_date):
    """Calculate running account balance up to target date"""
    if not starting_balance or not start_date:
        return starting_balance if starting_balance else 0
    
    # Convert string dates to date objects if needed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    
    running_balance = starting_balance
    current_date = start_date
    
    while current_date <= target_date:
        date_key = get_date_key(current_date)
        if date_key in data and 'trading' in data[date_key]:
            pnl = data[date_key]['trading'].get('pnl', 0)
            running_balance += pnl
        current_date += timedelta(days=1)
    
    return running_balance

def get_account_settings(data):
    """Get account balance settings from data"""
    return data.get('account_settings', {
        'starting_balance': 0.0,
        'start_date': None,
        'last_updated': None
    })

def save_account_settings(data, starting_balance, start_date):
    """Save account balance settings to data"""
    if 'account_settings' not in data:
        data['account_settings'] = {}
    
    data['account_settings']['starting_balance'] = starting_balance
    data['account_settings']['start_date'] = start_date.strftime("%Y-%m-%d") if isinstance(start_date, date) else start_date
    data['account_settings']['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return data

# Initialize session state - CALENDAR VIEW FIRST!
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()
if 'page' not in st.session_state:
    st.session_state.page = "📊 Calendar View"  # STARTS ON CALENDAR!
if 'github_connected' not in st.session_state:
    st.session_state.github_connected = False
if 'github_storage' not in st.session_state:
    st.session_state.github_storage = GitHubStorage()
if 'trade_analysis' not in st.session_state:
    st.session_state.trade_analysis = None
if 'trade_data' not in st.session_state:
    st.session_state.trade_data = None
if 'last_analysis_date' not in st.session_state:
    st.session_state.last_analysis_date = None
if 'trade_log_action' not in st.session_state:
    st.session_state.trade_log_action = None

# Main header - UPDATED VERSION TO 7.3
st.markdown('<h1 class="main-header">📊 Trading Journal v7.3</h1>', unsafe_allow_html=True)

# GitHub connection check and auto-setup
if hasattr(st, 'secrets') and 'github' in st.secrets:
    # Auto-connect using secrets
    if not st.session_state.get('github_connected', False):
        if st.session_state.github_storage.connect(st.secrets.github.token, st.secrets.github.owner, st.secrets.github.repo):
            st.session_state.github_connected = True
            st.session_state.github_token = st.secrets.github.token
            st.session_state.repo_owner = st.secrets.github.owner
            st.session_state.repo_name = st.secrets.github.repo

# Load data (GitHub first, then local fallback)
if st.session_state.get('github_connected', False):
    try:
        data = st.session_state.github_storage.load_all_journal_data()
        if not data:  # If GitHub is empty, try to load local data
            data = load_local_data()
    except:
        data = load_local_data()
else:
    data = load_local_data()

# NEW: Account Balance Management in Sidebar
st.sidebar.title("💰 Account Balance")

# Get account settings
account_settings = get_account_settings(data)
current_balance = 0

# Account balance setup
if not account_settings.get('starting_balance') or not account_settings.get('start_date'):
    # Setup required
    with st.sidebar.expander("⚙️ Setup Account Tracking", expanded=True):
        starting_balance = st.number_input(
            "Starting Balance ($)",
            min_value=0.0,
            value=account_settings.get('starting_balance', 10000.0),
            step=100.0,
            format="%.2f"
        )
        
        start_date = st.date_input(
            "Start Date",
            value=datetime.strptime(account_settings.get('start_date', date.today().strftime("%Y-%m-%d")), "%Y-%m-%d").date() if account_settings.get('start_date') else date.today(),
            max_value=date.today()
        )
        
        if st.button("💾 Save Balance Settings", key="save_balance_settings"):
            data = save_account_settings(data, starting_balance, start_date)
            
            # Save to storage
            if st.session_state.get('github_connected', False):
                if st.session_state.github_storage.save_journal_entry("account_setup", {}, data):
                    st.success("✅ Balance settings saved to GitHub!")
                else:
                    save_local_data(data)
                    st.success("💾 Balance settings saved locally!")
            else:
                save_local_data(data)
                st.success("💾 Balance settings saved locally!")
            
            st.rerun()
else:
    # Display current balance
    starting_balance = account_settings['starting_balance']
    start_date_str = account_settings['start_date']
    start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    
    # Calculate current balance
    current_balance = calculate_running_balance(data, st.session_state.current_date, starting_balance, start_date_obj)
    
    # Display balance with styling
    balance_change = current_balance - starting_balance
    balance_color = "#00ff88" if balance_change > 0 else "#ff4444" if balance_change < 0 else "#64ffda"
    change_symbol = "↗" if balance_change > 0 else "↘" if balance_change < 0 else "→"
    
    st.sidebar.markdown(f"""
    <div class="balance-display">
        <div style="font-size: 1rem; color: #aaa;">Current Balance</div>
        <div class="balance-amount" style="color: {balance_color};">
            ${current_balance:,.2f} {change_symbol}
        </div>
        <div style="font-size: 0.9rem; color: #aaa;">
            {change_symbol} ${abs(balance_change):,.2f} from start
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Balance management
    with st.sidebar.expander("⚙️ Manage Balance"):
        st.write(f"**Start Date:** {start_date_str}")
        st.write(f"**Starting Balance:** ${starting_balance:,.2f}")
        
        # Option to reset/update
        new_starting_balance = st.number_input(
            "Update Starting Balance ($)",
            min_value=0.0,
            value=starting_balance,
            step=100.0,
            format="%.2f"
        )
        
        new_start_date = st.date_input(
            "Update Start Date",
            value=start_date_obj,
            max_value=date.today()
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Update", key="update_balance"):
                data = save_account_settings(data, new_starting_balance, new_start_date)
                
                # Save to storage
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry("account_setup", {}, data)
                save_local_data(data)
                st.success("Updated!")
                st.rerun()
        
        with col2:
            if st.button("🗑️ Reset", key="reset_balance"):
                if 'account_settings' in data:
                    del data['account_settings']
                
                # Save to storage
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry("account_setup", {}, data)
                save_local_data(data)
                st.success("Reset!")
                st.rerun()

# Sidebar GitHub status
st.sidebar.title("☁️ Cloud Storage")
if st.session_state.get('github_connected', False):
    st.sidebar.success("✅ Connected to GitHub")
    repo_url = f"https://github.com/{st.session_state.repo_owner}/{st.session_state.repo_name}"
    st.sidebar.markdown(f"🔗 [View Repository]({repo_url})")
    screenshots_url = f"{repo_url}/tree/main/screenshots"
    st.sidebar.markdown(f"📸 [View Screenshots]({screenshots_url})")
else:
    st.sidebar.warning("⚠️ GitHub not connected")

# Sidebar navigation with buttons - CALENDAR FIRST!
st.sidebar.markdown("---")
st.sidebar.title("📋 Navigation")

# Navigation buttons - CALENDAR VIEW FIRST!
if st.sidebar.button("📊 Calendar View", key="nav_calendar", use_container_width=True):
    st.session_state.page = "📊 Calendar View"

if st.sidebar.button("🌅 Morning Prep", key="nav_morning", use_container_width=True):
    st.session_state.page = "🌅 Morning Prep"

if st.sidebar.button("📈 Trading Review", key="nav_trading", use_container_width=True):
    st.session_state.page = "📈 Trading Review"

if st.sidebar.button("🌙 Evening Recap", key="nav_evening", use_container_width=True):
    st.session_state.page = "🌙 Evening Recap"

if st.sidebar.button("📊 Trade Log Analysis", key="nav_tradelog", use_container_width=True):
    st.session_state.page = "📊 Trade Log Analysis"

if st.sidebar.button("📚 Historical Analysis", key="nav_history", use_container_width=True):
    st.session_state.page = "📚 Historical Analysis"

# NEW: Balance History Page
if st.sidebar.button("💰 Balance History", key="nav_balance_history", use_container_width=True):
    st.session_state.page = "💰 Balance History"

page = st.session_state.page

# Date selector - FIXED: Removed max_value restriction to allow future dates
st.sidebar.markdown("---")
selected_date = st.sidebar.date_input(
    "📅 Select Date",
    value=st.session_state.current_date,
    key="date_selector"
)

# Update current date when changed
if selected_date != st.session_state.current_date:
    st.session_state.current_date = selected_date

date_key = get_date_key(selected_date)

# Initialize date entry if doesn't exist
if date_key not in data:
    data[date_key] = {
        'morning': {},
        'trading': {},
        'evening': {},
        'rules': []
    }

current_entry = data[date_key]

# NEW: Balance History Page
if page == "💰 Balance History":
    st.markdown('<div class="section-header">💰 Account Balance History</div>', unsafe_allow_html=True)
    
    account_settings = get_account_settings(data)
    
    if not account_settings.get('starting_balance') or not account_settings.get('start_date'):
        st.warning("⚠️ Please set up your account balance tracking in the sidebar first.")
        st.info("Go to the sidebar and expand '⚙️ Setup Account Tracking' to get started.")
    else:
        starting_balance = account_settings['starting_balance']
        start_date_str = account_settings['start_date']
        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        
        # Date range for analysis
        col1, col2 = st.columns(2)
        with col1:
            analysis_start = st.date_input(
                "Start Date",
                value=start_date_obj,
                min_value=start_date_obj,
                max_value=date.today()
            )
        with col2:
            analysis_end = st.date_input(
                "End Date",
                value=date.today(),
                min_value=start_date_obj,
                max_value=date.today()
            )
        
        # Calculate daily balances
        balance_data = []
        current_date = analysis_start
        running_balance = calculate_running_balance(data, analysis_start, starting_balance, start_date_obj)
        
        while current_date <= analysis_end:
            date_key = get_date_key(current_date)
            daily_pnl = 0
            
            if date_key in data and 'trading' in data[date_key]:
                daily_pnl = data[date_key]['trading'].get('pnl', 0)
            
            balance_data.append({
                'date': current_date,
                'date_str': current_date.strftime("%Y-%m-%d"),
                'balance': running_balance,
                'daily_pnl': daily_pnl,
                'cumulative_pnl': running_balance - starting_balance
            })
            
            running_balance += daily_pnl
            current_date += timedelta(days=1)
        
        # Display summary metrics
        if balance_data:
            latest_balance = balance_data[-1]['balance']
            total_pnl = latest_balance - starting_balance
            best_day = max(balance_data, key=lambda x: x['daily_pnl'])
            worst_day = min(balance_data, key=lambda x: x['daily_pnl'])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Balance", f"${latest_balance:,.2f}")
            with col2:
                st.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{(total_pnl/starting_balance)*100:.2f}%")
            with col3:
                st.metric("Best Day", f"${best_day['daily_pnl']:,.2f}", delta=best_day['date_str'])
            with col4:
                st.metric("Worst Day", f"${worst_day['daily_pnl']:,.2f}", delta=worst_day['date_str'])
            
            # Balance chart
            fig = go.Figure()
            
            # Balance line
            fig.add_trace(go.Scatter(
                x=[d['date'] for d in balance_data],
                y=[d['balance'] for d in balance_data],
                mode='lines+markers',
                name='Account Balance',
                line=dict(color='#64ffda', width=3),
                marker=dict(size=4)
            ))
            
            # Starting balance reference line
            fig.add_hline(
                y=starting_balance,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Starting Balance: ${starting_balance:,.2f}"
            )
            
            fig.update_layout(
                title="Account Balance Over Time",
                xaxis_title="Date",
                yaxis_title="Balance ($)",
                template="plotly_dark",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Daily P&L chart
            fig2 = go.Figure()
            
            colors = ['green' if pnl > 0 else 'red' if pnl < 0 else 'gray' for pnl in [d['daily_pnl'] for d in balance_data]]
            
            fig2.add_trace(go.Bar(
                x=[d['date'] for d in balance_data],
                y=[d['daily_pnl'] for d in balance_data],
                marker_color=colors,
                name="Daily P&L"
            ))
            
            fig2.update_layout(
                title="Daily P&L",
                xaxis_title="Date",
                yaxis_title="P&L ($)",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Data table
            st.subheader("📊 Balance History Table")
            
            df = pd.DataFrame(balance_data)
            df['balance'] = df['balance'].apply(lambda x: f"${x:,.2f}")
            df['daily_pnl'] = df['daily_pnl'].apply(lambda x: f"${x:,.2f}")
            df['cumulative_pnl'] = df['cumulative_pnl'].apply(lambda x: f"${x:,.2f}")
            
            # Rename columns for display
            df_display = df[['date_str', 'balance', 'daily_pnl', 'cumulative_pnl']].copy()
            df_display.columns = ['Date', 'Balance', 'Daily P&L', 'Total P&L']
            
            # Show most recent first
            df_display = df_display.sort_values('Date', ascending=False)
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)

# ======== CALENDAR VIEW PAGE ========
elif page == "📊 Calendar View":
    st.markdown('<div class="section-header">📊 Monthly Calendar</div>', unsafe_allow_html=True)
    
    # Month selector
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        selected_month = st.date_input(
            "Select Month",
            value=selected_date.replace(day=1),
            key="calendar_month"
        )
    
    # Get the first day of the month and number of days
    first_day = selected_month.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Create calendar with Sunday as first day of week
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(first_day.year, first_day.month)
    
    st.subheader(f"{calendar.month_name[first_day.month]} {first_day.year}")
    
    # Calendar with weekly totals - Header
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Weekly P&L']
    header_cols = st.columns(8)
    for i, day in enumerate(days):
        header_cols[i].markdown(f"**{day}**")
    
    # Calendar body with weekly totals - ALL SAME HEIGHT
    for week in cal:
        week_cols = st.columns(8)
        week_pnl = 0
        
        for i, day in enumerate(week):
            if day == 0:
                # Empty day - same height as others
                week_cols[i].markdown(
                    '<div style="border: 2px solid #333; padding: 10px; height: 80px; background: rgba(0,0,0,0.2); border-radius: 5px;">&nbsp;</div>', 
                    unsafe_allow_html=True
                )
            else:
                day_date = date(first_day.year, first_day.month, day)
                day_key = get_date_key(day_date)
                
                # Check if we have data for this day
                if day_key in data:
                    entry = data[day_key]
                    pnl = entry.get('trading', {}).get('pnl', 0)
                    week_pnl += pnl
                    
                    # Check rule compliance
                    rule_compliance = entry.get('trading', {}).get('rule_compliance', {})
                    if rule_compliance:
                        compliance_rate = sum(rule_compliance.values()) / len(rule_compliance)
                        compliance_color = "🟢" if compliance_rate >= 0.8 else "🔴"
                    else:
                        compliance_color = "⚪"
                    
                    # Display day with P&L and compliance - clickable with same height
                    pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "gray"
                    
                    # Create clickable day button with fixed height
                    button_key = f"cal_day_{day_key}"
                    week_cols[i].markdown(f'''
                    <div style="border: 2px solid #333; padding: 10px; height: 80px; background: rgba(0,20,40,0.3); 
                                border-radius: 5px; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                        <strong>{day} {compliance_color}</strong><br>
                        <span style="color: {pnl_color};">${pnl:.2f}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    if week_cols[i].button("View", key=button_key, help=f"Click to view {day_date.strftime('%B %d, %Y')}"):
                        st.session_state.current_date = day_date
                        st.session_state.page = "📈 Trading Review"
                        st.rerun()
                else:
                    # Empty day - still clickable with same height
                    empty_button_key = f"cal_empty_{day}_{first_day.month}_{first_day.year}"
                    week_cols[i].markdown(f'''
                    <div style="border: 2px solid #333; padding: 10px; height: 80px; background: rgba(0,0,0,0.2); 
                                border-radius: 5px; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                        <strong>{day}</strong><br>
                        <span style="color: gray;">---</span>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    if week_cols[i].button("Add", key=empty_button_key, help=f"Click to add entry for {day_date.strftime('%B %d, %Y')}"):
                        st.session_state.current_date = day_date
                        st.session_state.page = "📈 Trading Review"
                        st.rerun()
        
        # Weekly total column - SAME HEIGHT as calendar days
        week_color = "green" if week_pnl > 0 else "red" if week_pnl < 0 else "gray"
        week_cols[7].markdown(f'''
        <div style="border: 2px solid {week_color}; padding: 10px; height: 80px; 
                    background: rgba({'0,255,0' if week_pnl > 0 else '255,0,0' if week_pnl < 0 else '128,128,128'}, 0.1);
                    text-align: center; display: flex; flex-direction: column; justify-content: center; border-radius: 5px;">
            <strong style="color: {week_color};">Week Total</strong><br>
            <span style="color: {week_color}; font-size: 1.2em;">${week_pnl:.2f}</span>
        </div>
        ''', unsafe_allow_html=True)
    
    # Legend
    st.markdown("---")
    st.markdown("**Legend:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🟢 Good Process (80%+ rule compliance)")
    with col2:
        st.markdown("🔴 Poor Process (<80% rule compliance)")
    with col3:
        st.markdown("⚪ No trading data")
    with col4:
        st.markdown("💡 **Click View/Add to edit entries**")

# ======== TRADE LOG ANALYSIS PAGE ========
elif page == "📊 Trade Log Analysis":
    st.markdown('<div class="section-header">📊 Trade Log Analysis</div>', unsafe_allow_html=True)
    
    # Clear session state if date changed
    if st.session_state.last_analysis_date != date_key:
        st.session_state.trade_analysis = None
        st.session_state.trade_data = None
        st.session_state.last_analysis_date = date_key
    
    # Display selected date at the top
    st.markdown(f"### 📅 Analyzing trade log for: {selected_date.strftime('%A, %B %d, %Y')}")
    
    # Check if there's existing trade log data for this date
    existing_trade_log = current_entry.get('trade_log', {})
    has_existing_data = bool(existing_trade_log.get('analysis'))
    
    if has_existing_data:
        st.success(f"✅ Trade log data found for {selected_date.strftime('%B %d, %Y')}!")
        
        # Show option to view existing or upload new
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👁️ View Existing Trade Log", key="view_existing"):
                st.session_state.trade_log_action = "view_existing"
                st.session_state.trade_analysis = existing_trade_log.get('analysis', {})
                st.rerun()
        with col2:
            if st.button("📄 Replace with New Upload", key="replace_upload"):
                st.session_state.trade_log_action = "upload_new"
                st.session_state.trade_analysis = None
                st.session_state.trade_data = None
                st.rerun()
    
    # Determine what to show based on state
    if has_existing_data and st.session_state.trade_log_action == "view_existing":
        # User chose to view existing - load the data
        if not st.session_state.trade_analysis:
            st.session_state.trade_analysis = existing_trade_log.get('analysis', {})
        # Don't show upload interface
        
    elif has_existing_data and st.session_state.trade_log_action == "upload_new":
        # User chose to upload new - show upload interface
        st.subheader("📄 Upload New Trade Log")
        st.info("Upload a new file to replace the existing trade log data.")
        
        uploaded_file = st.file_uploader(
            f"Upload trade log for {selected_date.strftime('%B %d, %Y')} (CSV or TSV format)",
            type=['txt', 'csv', 'tsv'],
            help="Upload trade logs from your broker (e.g., TradeActivityLogExport files)",
            key=f"trade_log_upload_new_{date_key}"
        )
        
        if uploaded_file is not None:
            file_content = uploaded_file.read().decode('utf-8')
            trades, error = parse_trade_log(file_content)
            
            if error:
                st.error(f"Error parsing file: {error}")
            else:
                st.session_state.trade_data = trades
                st.session_state.trade_analysis = analyze_trades(trades)
                st.success(f"✅ Successfully parsed {len(trades)} trade records for {selected_date.strftime('%B %d, %Y')}!")
        
    elif has_existing_data and st.session_state.trade_log_action is None:
        # Default state - auto-load existing data
        if not st.session_state.trade_analysis:
            st.session_state.trade_analysis = existing_trade_log.get('analysis', {})
        
    else:
        # No existing data - show upload interface
        st.subheader("📄 Upload Trade Log")
        
        uploaded_file = st.file_uploader(
            f"Upload trade log for {selected_date.strftime('%B %d, %Y')} (CSV or TSV format)",
            type=['txt', 'csv', 'tsv'],
            help="Upload trade logs from your broker (e.g., TradeActivityLogExport files)",
            key=f"trade_log_upload_{date_key}"
        )
        
        if uploaded_file is not None:
            file_content = uploaded_file.read().decode('utf-8')
            trades, error = parse_trade_log(file_content)
            
            if error:
                st.error(f"Error parsing file: {error}")
            else:
                st.session_state.trade_data = trades
                st.session_state.trade_analysis = analyze_trades(trades)
                st.success(f"✅ Successfully parsed {len(trades)} trade records for {selected_date.strftime('%B %d, %Y')}!")
    
    # Display analysis if available
    if st.session_state.trade_analysis:
        analysis = st.session_state.trade_analysis
        trades = st.session_state.trade_data if st.session_state.trade_data else []
        
        st.markdown("---")
        st.subheader("📈 Trading Statistics")
        
        # Get saved commission from existing data or allow input
        saved_commissions = existing_trade_log.get('commissions', 0.0) if has_existing_data else 0.0
        
        commission_input = st.number_input(
            "Total Commissions for Session ($)",
            min_value=0.0,
            value=saved_commissions,
            step=0.01,
            format="%.2f",
            help="Enter total commission costs for this trading session"
        )
        
        # Calculate net P&L
        gross_pnl = analysis.get('daily_pnl', 0)
        net_pnl = gross_pnl - commission_input
        
        # Key metrics in columns - UPDATED WITH WINNER/LOSER STATS
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Fills", analysis.get('total_fills', 0))
            st.metric("Total Volume", f"{analysis.get('total_volume', 0):.0f} contracts")
        
        with col2:
            st.metric("Completed Trades", analysis.get('total_trades', 0))
            st.metric("Win/Loss Ratio", f"{analysis.get('winning_trades', 0)}/{analysis.get('losing_trades', 0)}")
        
        with col3:
            avg_winner = analysis.get('avg_winner', 0)
            avg_loser = analysis.get('avg_loser', 0)
            st.metric("Average Winner", f"${avg_winner:.2f}" if avg_winner > 0 else "$0.00")
            st.metric("Average Loser", f"${avg_loser:.2f}" if avg_loser < 0 else "$0.00")
        
        with col4:
            st.metric("Win Rate", f"{analysis.get('win_rate', 0):.1f}%")
            st.metric("Net P&L", f"${net_pnl:.2f}", help="P&L after commissions")
        
        # Symbols and Order Types
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Symbols Traded")
            symbols = analysis.get('symbols', [])
            if symbols:
                for symbol in symbols:
                    st.write(f"• {symbol}")
            else:
                st.write("No symbol data available")
        
        with col2:
            st.subheader("📋 Order Types")
            order_types = analysis.get('order_types', [])
            if order_types:
                for order_type in order_types:
                    st.write(f"• {order_type}")
            else:
                st.write("No order type data available")
        
        # Show saved analysis summary
        if has_existing_data and not trades:
            st.subheader("📊 Saved Analysis Summary")
            st.write(f"**Trade Fills:** {existing_trade_log.get('fill_count', existing_trade_log.get('trade_count', 'N/A'))}")
            st.write(f"**Total Volume:** {existing_trade_log.get('total_volume', 'N/A')} contracts")
            st.write(f"**Completed Trades:** {existing_trade_log.get('completed_trades', existing_trade_log.get('total_trades', 'N/A'))}")
            st.write(f"**Win Rate:** {existing_trade_log.get('win_rate', 0):.1f}%")
        
        # Save/Export functionality
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save Analysis to Journal"):
                # Save trade analysis to selected date
                current_entry['trade_log'] = {
                    'analysis': analysis,
                    'fill_count': len(trades) if trades else analysis.get('total_fills', 0),  # Changed from trade_count
                    'symbols': analysis.get('symbols', []),
                    'total_volume': analysis.get('total_volume', 0),
                    'gross_pnl': gross_pnl,
                    'commissions': commission_input,
                    'net_pnl': net_pnl,
                    'win_rate': analysis.get('win_rate', 0),
                    'winning_trades': analysis.get('winning_trades', 0),
                    'losing_trades': analysis.get('losing_trades', 0),
                    'avg_winner': analysis.get('avg_winner', 0),
                    'avg_loser': analysis.get('avg_loser', 0),
                    'completed_trades': analysis.get('total_trades', 0)  # Clearer terminology
                }
                
                if st.session_state.get('github_connected', False):
                    if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                        st.success(f"✅ Trade analysis saved to journal for {selected_date.strftime('%B %d, %Y')}!")
                    else:
                        save_local_data(data)
                        st.success(f"💾 Trade analysis saved locally for {selected_date.strftime('%B %d, %Y')}!")
                else:
                    save_local_data(data)
                    st.success(f"💾 Trade analysis saved locally for {selected_date.strftime('%B %d, %Y')}!")
        
        with col2:
            if st.button("📄 Update Trading Review P&L"):
                # Update the trading review P&L with net P&L from trade log
                if 'trading' not in current_entry:
                    current_entry['trading'] = {}
                
                current_entry['trading']['pnl'] = net_pnl
                current_entry['trading']['trade_log_sync'] = True
                current_entry['trading']['gross_pnl'] = gross_pnl
                current_entry['trading']['commissions'] = commission_input
                
                if st.session_state.get('github_connected', False):
                    if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                        st.success(f"✅ Trading Review P&L updated to ${net_pnl:.2f} for {selected_date.strftime('%B %d, %Y')}!")
                    else:
                        save_local_data(data)
                        st.success(f"💾 Trading Review P&L updated to ${net_pnl:.2f} for {selected_date.strftime('%B %d, %Y')}!")
                else:
                    save_local_data(data)
                    st.success(f"💾 Trading Review P&L updated to ${net_pnl:.2f} for {selected_date.strftime('%B %d, %Y')}!")
        
        with col3:
            if st.button("🗑️ Delete Trade Log"):
                # Remove trade log from current entry
                if 'trade_log' in current_entry:
                    del current_entry['trade_log']
                
                # Clear session state
                st.session_state.trade_analysis = None
                st.session_state.trade_data = None
                st.session_state.trade_log_action = None
                
                # Save the updated data
                if st.session_state.get('github_connected', False):
                    if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                        st.success("✅ Trade log deleted from GitHub!")
                    else:
                        save_local_data(data)
                        st.success("💾 Trade log deleted locally!")
                else:
                    save_local_data(data)
                    st.success("💾 Trade log deleted locally!")
                
                st.rerun()
        
        with col4:
            # Export filtered data as CSV - only if we have trade data
            if trades:
                df = pd.DataFrame(trades)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📤 Export Trades as CSV",
                    data=csv,
                    file_name=f"trades_{selected_date.strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.write("📤 Export not available")
    
    else:
        st.info(f"No trade log data available for {selected_date.strftime('%B %d, %Y')}. Upload a trade log file to see detailed analysis and statistics.")
        
        # Show sample format
        st.subheader("📋 Supported File Formats")
        st.write("Your trade log should be in CSV or TSV format with columns like:")
        st.code("""
DateTime, Symbol, BuySell, Quantity, FillPrice, OrderType, OpenClose, PositionQuantity
2025-09-08 05:49:31, F.US.mNQU25, Buy, 3, 23736.50, Market, Open, 3
2025-09-08 06:06:38, F.US.mNQU25, Sell, 1, 23746.75, Market, Close, 2
        """)

# ======== MORNING PREP PAGE - COMPLETELY FIXED ========
elif page == "🌅 Morning Prep":
    st.markdown('<div class="section-header">🌅 Morning Preparation</div>', unsafe_allow_html=True)
    
    # Show current date and delete option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📅 {selected_date.strftime('%A, %B %d, %Y')}")
    with col2:
        if st.button("🗑️ Delete Entry", key="delete_morning", help="Delete all data for this date"):
            if date_key in data:
                del data[date_key]
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry(date_key, {}, data)
                save_local_data(data)
                st.success("Entry deleted!")
                st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Check-in")
        
        sleep_quality = st.slider(
            "Sleep Quality (1-10)",
            1, 10,
            value=current_entry['morning'].get('sleep_quality', 7),
            key="sleep_quality"
        )
        
        emotional_state = st.selectbox(
            "Emotional State",
            ["Calm & Focused", "Excited", "Anxious", "Stressed", "Tired", "Confident", "Uncertain"],
            index=["Calm & Focused", "Excited", "Anxious", "Stressed", "Tired", "Confident", "Uncertain"].index(
                current_entry['morning'].get('emotional_state', "Calm & Focused")
            )
        )
        
        post_night_shift = st.checkbox(
            "Post Night Shift?",
            value=current_entry['morning'].get('post_night_shift', False)
        )
        
        checked_news = st.checkbox(
            "Checked News & Market Events?",
            value=current_entry['morning'].get('checked_news', False)
        )
        
        # FIXED: Market News text box right below the checkbox
        market_news = st.text_area(
            "Market News & Events for Today",
            value=current_entry['morning'].get('market_news', ""),
            height=100,
            placeholder="Add any relevant news, economic data, or market events..."
        )
        
        triggers_present = st.text_area(
            "Any triggers/reasons why you shouldn't trade today?",
            value=current_entry['morning'].get('triggers_present', ""),
            height=100
        )
        
        grateful_for = st.text_area(
            "What are you grateful for today?",
            value=current_entry['morning'].get('grateful_for', ""),
            height=100
        )
        
        # FIXED: Screenshot upload for morning prep WITH CAPTIONS
        st.subheader("📸 Morning Screenshots")
        
        # Initialize current_entry['morning'] if it doesn't exist
        if 'morning' not in current_entry:
            current_entry['morning'] = {}
        
        # Ensure screenshots array exists
        if 'morning_screenshots' not in current_entry['morning']:
            current_entry['morning']['morning_screenshots'] = []
        
        # Use a unique key based on the number of existing screenshots to avoid conflicts
        existing_morning_count = len(current_entry['morning'].get('morning_screenshots', []))
        morning_upload_key = f"morning_screenshot_{date_key}_{existing_morning_count}"
        
        morning_screenshot = st.file_uploader(
            "Upload market analysis, news, or prep screenshots",
            type=['png', 'jpg', 'jpeg'],
            key=morning_upload_key,
            help="Select an image file to upload"
        )
        
        # Handle immediate upload when file is selected
        if morning_screenshot is not None:
            # Use a unique caption key as well
            morning_caption_key = f"morning_caption_{date_key}_{existing_morning_count}"
            
            # Caption input
            morning_caption = st.text_input(
                "Screenshot Caption",
                placeholder="Describe this screenshot...",
                key=morning_caption_key
            )
            
            # Upload button with unique key
            morning_upload_btn_key = f"upload_morning_btn_{date_key}_{existing_morning_count}"
            
            if st.button("📤 Upload Screenshot", key=morning_upload_btn_key):
                if not morning_caption.strip():
                    st.warning("⚠️ Please add a caption for your screenshot!")
                else:
                    # Get existing screenshots
                    morning_screenshots = current_entry['morning'].get('morning_screenshots', [])
                    
                    success = False
                    if st.session_state.get('github_connected', False):
                        # Upload to GitHub
                        try:
                            file_data = morning_screenshot.getvalue()
                            timestamp = int(datetime.now().timestamp())
                            filename = f"morning_{timestamp}_{morning_screenshot.name}"
                            screenshot_url = st.session_state.github_storage.upload_screenshot(
                                file_data, filename, date_key
                            )
                            if screenshot_url:
                                # Save as dict with URL and caption
                                morning_screenshots.append({
                                    'url': screenshot_url,
                                    'caption': morning_caption
                                })
                                success = True
                                st.success(f"✅ Screenshot '{morning_caption}' uploaded to GitHub!")
                            else:
                                st.error("❌ Failed to upload screenshot to GitHub")
                        except Exception as e:
                            st.error(f"❌ GitHub upload error: {str(e)}")
                    else:
                        # Save locally
                        try:
                            screenshot_path = save_uploaded_file_local(morning_screenshot, date_key, "morning")
                            if screenshot_path:
                                morning_screenshots.append({
                                    'url': screenshot_path,
                                    'caption': morning_caption
                                })
                                success = True
                                st.success(f"✅ Screenshot '{morning_caption}' saved locally!")
                            else:
                                st.error("❌ Failed to save screenshot locally")
                        except Exception as e:
                            st.error(f"❌ Local save error: {str(e)}")
                    
                    if success:
                        # Update the entry
                        current_entry['morning']['morning_screenshots'] = morning_screenshots
                        
                        # Save immediately
                        try:
                            if st.session_state.get('github_connected', False):
                                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                                    st.success("📝 Entry updated successfully!")
                                else:
                                    st.error("❌ Failed to save entry to GitHub")
                            else:
                                save_local_data(data)
                                st.success("📝 Entry updated successfully!")
                        except Exception as e:
                            st.error(f"❌ Save error: {str(e)}")
                        
                        # Force rerun to refresh the page and clear the upload
                        st.rerun()
        
        # Display existing morning screenshots
        existing_morning_screenshots = current_entry['morning'].get('morning_screenshots', [])
        if existing_morning_screenshots:
            st.markdown("**Uploaded Screenshots:**")
            
            for i, screenshot_data in enumerate(existing_morning_screenshots):
                if screenshot_data:
                    # Handle both old format (just URL) and new format (dict with URL and caption)
                    if isinstance(screenshot_data, dict):
                        screenshot_link = screenshot_data.get('url', '')
                        screenshot_caption = screenshot_data.get('caption', f"Morning Screenshot {i+1}")
                    else:
                        screenshot_link = screenshot_data
                        screenshot_caption = f"Morning Screenshot {i+1}"
                    
                    if screenshot_link:
                        col_img, col_delete = st.columns([4, 1])
                        with col_img:
                            st.markdown(f"**{screenshot_caption}:**")
                            display_image_full_size(screenshot_link, screenshot_caption)
                        with col_delete:
                            delete_morning_key = f"delete_morning_img_{date_key}_{i}"
                            if st.button("🗑️", key=delete_morning_key, help="Delete this screenshot"):
                                # Remove screenshot
                                current_entry['morning']['morning_screenshots'].pop(i)
                                
                                # Save immediately
                                try:
                                    if st.session_state.get('github_connected', False):
                                        st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                                    save_local_data(data)
                                    st.success("Screenshot deleted!")
                                except Exception as e:
                                    st.error(f"Error deleting screenshot: {str(e)}")
                                st.rerun()
    
    with col2:
        st.subheader("Trading Goals & Rules")
        
        daily_goal = st.text_area(
            "Daily Trading Goal",
            value=current_entry['morning'].get('daily_goal', ""),
            height=100
        )
        
        trading_process = st.text_area(
            "Trading Process Focus",
            value=current_entry['morning'].get('trading_process', ""),
            height=100
        )
        
        st.subheader("Trading Rules")
        
        # Display existing rules
        if 'rules' not in current_entry:
            current_entry['rules'] = []
        
        # Keep track of rules to delete
        rules_to_delete = []
        
        for i, rule in enumerate(current_entry['rules']):
            col_rule, col_delete = st.columns([4, 1])
            with col_rule:
                new_rule_value = st.text_input(
                    f"Rule {i+1}",
                    value=rule,
                    key=f"rule_{i}",
                    placeholder="Enter your trading rule here..."
                )
                # Update the rule in real-time
                current_entry['rules'][i] = new_rule_value
            with col_delete:
                if st.button("❌", key=f"delete_rule_{i}"):
                    rules_to_delete.append(i)
        
        # Remove deleted rules (in reverse order to maintain indices)
        for i in reversed(rules_to_delete):
            current_entry['rules'].pop(i)
            # Save immediately
            if st.session_state.get('github_connected', False):
                st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
            save_local_data(data)
            st.rerun()
        
        if st.button("➕ Add Rule"):
            current_entry['rules'].append("New rule - click to edit")
            # Save immediately
            if st.session_state.get('github_connected', False):
                st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
            save_local_data(data)
            st.rerun()
    
    # Save morning data - FIXED to include market_news and morning_screenshots
    if st.button("💾 Save Morning Prep", type="primary"):
        current_entry['morning'] = {
            'sleep_quality': sleep_quality,
            'emotional_state': emotional_state,
            'post_night_shift': post_night_shift,
            'checked_news': checked_news,
            'market_news': market_news,  # FIXED: Include market news
            'triggers_present': triggers_present,
            'grateful_for': grateful_for,
            'daily_goal': daily_goal,
            'trading_process': trading_process,
            'morning_screenshots': current_entry['morning'].get('morning_screenshots', [])  # FIXED: Keep existing screenshots
        }
        
        # Save to GitHub and local
        if st.session_state.get('github_connected', False):
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Morning prep saved to GitHub!")
            else:
                save_local_data(data)
                st.success("💾 Morning prep saved locally!")
        else:
            save_local_data(data)
            st.success("💾 Morning prep saved locally!")

# ======== TRADING REVIEW PAGE ========
elif page == "📈 Trading Review":
    st.markdown('<div class="section-header">📈 Post-Trading Review</div>', unsafe_allow_html=True)
    
    # Show current date and delete option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📅 {selected_date.strftime('%A, %B %d, %Y')}")
    with col2:
        if st.button("🗑️ Delete Entry", key="delete_trading", help="Delete all data for this date"):
            if date_key in data:
                del data[date_key]
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry(date_key, {}, data)
                save_local_data(data)
                st.success("Entry deleted!")
                st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance Metrics")
        
        pnl = st.number_input(
            "P&L for the Day ($)",
            value=current_entry['trading'].get('pnl', 0.0),
            format="%.2f",
            help="Manual entry or synced from Trade Log Analysis"
        )
        
        # Show if P&L is synced from trade log
        if current_entry['trading'].get('trade_log_sync', False):
            gross_pnl = current_entry['trading'].get('gross_pnl', 0)
            commissions = current_entry['trading'].get('commissions', 0)
            st.info(f"📄 P&L synced from Trade Log: Gross ${gross_pnl:.2f} - Commissions ${commissions:.2f} = Net ${pnl:.2f}")
        
        process_grade = st.selectbox(
            "Grade Your Process (A-F)",
            ["A", "B", "C", "D", "F"],
            index=["A", "B", "C", "D", "F"].index(
                current_entry['trading'].get('process_grade', "A")
            )
        )
        
        grade_reasoning = st.text_area(
            "Why did you grade yourself this way?",
            value=current_entry['trading'].get('grade_reasoning', ""),
            height=100
        )
        
        general_comments = st.text_area(
            "General comments on the trading day",
            value=current_entry['trading'].get('general_comments', ""),
            height=100
        )
        
        screenshot_notes = st.text_area(
            "Screenshot/Entry Notes",
            value=current_entry['trading'].get('screenshot_notes', ""),
            height=100,
            help="Describe your entries, exits, and any screenshots you took"
        )
        
        # Screenshot upload for trading WITH CAPTIONS
        st.subheader("📸 Trading Screenshots")
        
        # Initialize current_entry['trading'] if it doesn't exist
        if 'trading' not in current_entry:
            current_entry['trading'] = {}
        
        # Ensure screenshots array exists
        if 'trading_screenshots' not in current_entry['trading']:
            current_entry['trading']['trading_screenshots'] = []
        
        # Use a unique key based on the number of existing screenshots to avoid conflicts
        existing_screenshot_count = len(current_entry['trading'].get('trading_screenshots', []))
        upload_key = f"trading_screenshot_{date_key}_{existing_screenshot_count}"
        
        trading_screenshot = st.file_uploader(
            "Upload entry/exit screenshots, charts, or P&L",
            type=['png', 'jpg', 'jpeg'],
            key=upload_key,
            help="Select an image file to upload"
        )
        
        # Handle immediate upload when file is selected
        if trading_screenshot is not None:
            # Use a unique caption key as well
            caption_key = f"trading_caption_{date_key}_{existing_screenshot_count}"
            
            # Caption input
            trading_caption = st.text_input(
                "Screenshot Caption",
                placeholder="Describe this screenshot...",
                key=caption_key
            )
            
            # Upload button with unique key
            upload_btn_key = f"upload_trading_btn_{date_key}_{existing_screenshot_count}"
            
            if st.button("📤 Upload Screenshot", key=upload_btn_key):
                if not trading_caption.strip():
                    st.warning("⚠️ Please add a caption for your screenshot!")
                else:
                    # Get existing screenshots
                    trading_screenshots = current_entry['trading'].get('trading_screenshots', [])
                    
                    success = False
                    if st.session_state.get('github_connected', False):
                        # Upload to GitHub
                        try:
                            file_data = trading_screenshot.getvalue()
                            timestamp = int(datetime.now().timestamp())
                            filename = f"trading_{timestamp}_{trading_screenshot.name}"
                            screenshot_url = st.session_state.github_storage.upload_screenshot(
                                file_data, filename, date_key
                            )
                            if screenshot_url:
                                # Save as dict with URL and caption
                                trading_screenshots.append({
                                    'url': screenshot_url,
                                    'caption': trading_caption
                                })
                                success = True
                                st.success(f"✅ Screenshot '{trading_caption}' uploaded to GitHub!")
                            else:
                                st.error("❌ Failed to upload screenshot to GitHub")
                        except Exception as e:
                            st.error(f"❌ GitHub upload error: {str(e)}")
                    else:
                        # Save locally
                        try:
                            screenshot_path = save_uploaded_file_local(trading_screenshot, date_key, "trading")
                            if screenshot_path:
                                trading_screenshots.append({
                                    'url': screenshot_path,
                                    'caption': trading_caption
                                })
                                success = True
                                st.success(f"✅ Screenshot '{trading_caption}' saved locally!")
                            else:
                                st.error("❌ Failed to save screenshot locally")
                        except Exception as e:
                            st.error(f"❌ Local save error: {str(e)}")
                    
                    if success:
                        # Update the entry
                        current_entry['trading']['trading_screenshots'] = trading_screenshots
                        
                        # Save immediately
                        try:
                            if st.session_state.get('github_connected', False):
                                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                                    st.success("📝 Entry updated successfully!")
                                else:
                                    st.error("❌ Failed to save entry to GitHub")
                            else:
                                save_local_data(data)
                                st.success("📝 Entry updated successfully!")
                        except Exception as e:
                            st.error(f"❌ Save error: {str(e)}")
                        
                        # Force rerun to refresh the page and clear the upload
                        st.rerun()
        
        # Display existing trading screenshots
        existing_screenshots = current_entry['trading'].get('trading_screenshots', [])
        if existing_screenshots:
            st.markdown("**Uploaded Screenshots:**")
            
            for i, screenshot_data in enumerate(existing_screenshots):
                if screenshot_data:
                    # Handle both old format (just URL) and new format (dict with URL and caption)
                    if isinstance(screenshot_data, dict):
                        screenshot_link = screenshot_data.get('url', '')
                        screenshot_caption = screenshot_data.get('caption', f"Trading Screenshot {i+1}")
                    else:
                        screenshot_link = screenshot_data
                        screenshot_caption = f"Trading Screenshot {i+1}"
                    
                    if screenshot_link:
                        col_img, col_delete = st.columns([4, 1])
                        with col_img:
                            st.markdown(f"**{screenshot_caption}:**")
                            display_image_full_size(screenshot_link, screenshot_caption)
                        with col_delete:
                            delete_key = f"delete_trading_img_{date_key}_{i}"
                            if st.button("🗑️", key=delete_key, help="Delete this screenshot"):
                                # Remove screenshot
                                current_entry['trading']['trading_screenshots'].pop(i)
                                
                                # Save immediately
                                try:
                                    if st.session_state.get('github_connected', False):
                                        st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                                    save_local_data(data)
                                    st.success("Screenshot deleted!")
                                except Exception as e:
                                    st.error(f"Error deleting screenshot: {str(e)}")
                                st.rerun()
        
        # Add some spacing
        st.markdown("---")
    
    with col2:
        st.subheader("Rule Compliance")
        
        if current_entry['rules']:
            rule_compliance = {}
            for i, rule in enumerate(current_entry['rules']):
                if rule.strip():  # Only show non-empty rules
                    compliance = st.checkbox(
                        f"✅ {rule}",
                        value=current_entry['trading'].get('rule_compliance', {}).get(f"rule_{i}", False),
                        key=f"compliance_{i}"
                    )
                    rule_compliance[f"rule_{i}"] = compliance
        else:
            st.info("No rules set in morning prep. Go to Morning Prep to add rules.")
            rule_compliance = {}
        
        st.subheader("Reflection")
        
        what_could_improve = st.text_area(
            "What could you have done better?",
            value=current_entry['trading'].get('what_could_improve', ""),
            height=100
        )
        
        tomorrow_focus = st.text_area(
            "What do you want to do better tomorrow?",
            value=current_entry['trading'].get('tomorrow_focus', ""),
            height=100
        )
    
    # Calculate overall compliance
    if rule_compliance:
        compliance_rate = sum(rule_compliance.values()) / len(rule_compliance) * 100
        st.metric("Rule Compliance Rate", f"{compliance_rate:.1f}%")
    
    # Save trading data
    if st.button("💾 Save Trading Review", type="primary"):
        current_entry['trading'] = {
            'pnl': pnl,
            'process_grade': process_grade,
            'grade_reasoning': grade_reasoning,
            'general_comments': general_comments,
            'screenshot_notes': screenshot_notes,
            'rule_compliance': rule_compliance,
            'what_could_improve': what_could_improve,
            'tomorrow_focus': tomorrow_focus,
            'trading_screenshots': current_entry['trading'].get('trading_screenshots', [])  # Keep existing screenshots
        }
        
        # Preserve trade log sync data if it exists
        if current_entry['trading'].get('trade_log_sync', False):
            current_entry['trading']['trade_log_sync'] = True
            current_entry['trading']['gross_pnl'] = current_entry['trading'].get('gross_pnl', 0)
            current_entry['trading']['commissions'] = current_entry['trading'].get('commissions', 0)
        
        # Save to GitHub and local
        if st.session_state.get('github_connected', False):
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Trading review saved to GitHub!")
            else:
                save_local_data(data)
                st.success("💾 Trading review saved locally!")
        else:
            save_local_data(data)
            st.success("💾 Trading review saved locally!")

# ======== EVENING RECAP PAGE ========
elif page == "🌙 Evening Recap":
    st.markdown('<div class="section-header">🌙 Evening Life Recap</div>', unsafe_allow_html=True)
    
    # Show current date and delete option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📅 {selected_date.strftime('%A, %B %d, %Y')}")
    with col2:
        if st.button("🗑️ Delete Entry", key="delete_evening", help="Delete all data for this date"):
            if date_key in data:
                del data[date_key]
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry(date_key, {}, data)
                save_local_data(data)
                st.success("Entry deleted!")
                st.rerun()
    
    st.subheader("Personal Reflection")
    st.write("Reflect on your day as a person, father, and husband")
    
    personal_recap = st.text_area(
        "How was your day outside of trading?",
        value=current_entry['evening'].get('personal_recap', ""),
        height=200,
        help="Reflect on family time, personal goals, relationships, and overall well-being"
    )
    
    family_highlights = st.text_area(
        "Family Highlights",
        value=current_entry['evening'].get('family_highlights', ""),
        height=150,
        help="Special moments with family, conversations with spouse/children"
    )
    
    personal_wins = st.text_area(
        "Personal Wins & Growth",
        value=current_entry['evening'].get('personal_wins', ""),
        height=150,
        help="Non-trading accomplishments, personal development, habits"
    )
    
    tomorrow_intentions = st.text_area(
        "Intentions for Tomorrow",
        value=current_entry['evening'].get('tomorrow_intentions', ""),
        height=150,
        help="How do you want to show up as a person, father, and husband tomorrow?"
    )
    
    # Save evening data
    if st.button("💾 Save Evening Recap", type="primary"):
        current_entry['evening'] = {
            'personal_recap': personal_recap,
            'family_highlights': family_highlights,
            'personal_wins': personal_wins,
            'tomorrow_intentions': tomorrow_intentions
        }
        
        # Save to GitHub and local
        if st.session_state.get('github_connected', False):
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Evening recap saved to GitHub!")
            else:
                save_local_data(data)
                st.success("💾 Evening recap saved locally!")
        else:
            save_local_data(data)
            st.success("💾 Evening recap saved locally!")

# ======== HISTORICAL ANALYSIS PAGE ========
elif page == "📚 Historical Analysis":
    st.markdown('<div class="section-header">📚 Historical Analysis</div>', unsafe_allow_html=True)
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=date.today() - timedelta(days=30),
            max_value=date.today()
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=date.today(),
            max_value=date.today()
        )
    
    if st.button("📊 Analyze Period"):
        # Filter data for date range
        filtered_data = {}
        current_date = start_date
        while current_date <= end_date:
            date_key = get_date_key(current_date)
            if date_key in data:
                filtered_data[date_key] = data[date_key]
            current_date += timedelta(days=1)
        
        if filtered_data:
            # Calculate statistics
            total_pnl = 0
            process_compliance_days = 0
            total_trading_days = 0
            profitable_days = 0
            daily_pnls = []
            
            for date_key, entry in filtered_data.items():
                if 'trading' in entry and 'pnl' in entry['trading']:
                    pnl = entry['trading']['pnl']
                    total_pnl += pnl
                    daily_pnls.append(pnl)
                    total_trading_days += 1
                    
                    if pnl > 0:
                        profitable_days += 1
                    
                    # Check process compliance
                    rule_compliance = entry.get('trading', {}).get('rule_compliance', {})
                    if rule_compliance:
                        compliance_rate = sum(rule_compliance.values()) / len(rule_compliance)
                        if compliance_rate >= 0.8:
                            process_compliance_days += 1
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total P&L", f"${total_pnl:.2f}")
            
            with col2:
                avg_pnl = total_pnl / total_trading_days if total_trading_days > 0 else 0
                st.metric("Average Daily P&L", f"${avg_pnl:.2f}")
            
            with col3:
                process_rate = (process_compliance_days / total_trading_days * 100) if total_trading_days > 0 else 0
                st.metric("Process Success Rate", f"{process_rate:.1f}%")
            
            with col4:
                win_rate = (profitable_days / total_trading_days * 100) if total_trading_days > 0 else 0
                st.metric("Win Rate", f"{win_rate:.1f}%")
            
            # P&L Chart
            if daily_pnls:
                dates = list(filtered_data.keys())
                pnls = [filtered_data[d].get('trading', {}).get('pnl', 0) for d in dates]
                
                fig = go.Figure()
                colors = ['green' if p > 0 else 'red' if p < 0 else 'gray' for p in pnls]
                
                fig.add_trace(go.Bar(
                    x=dates,
                    y=pnls,
                    marker_color=colors,
                    name="Daily P&L"
                ))
                
                fig.update_layout(
                    title="Daily P&L Over Time",
                    xaxis_title="Date",
                    yaxis_title="P&L ($)",
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed entries
            st.subheader("Detailed Entries")
            
            for date_key in sorted(filtered_data.keys(), reverse=True):
                entry = filtered_data[date_key]
                
                with st.expander(f"📅 {date_key}"):
                    # Morning Section
                    if 'morning' in entry and entry['morning']:
                        st.markdown("### 🌅 Morning Preparation")
                        morning = entry['morning']
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if 'sleep_quality' in morning:
                                st.write(f"**Sleep Quality:** {morning['sleep_quality']}/10")
                            if 'emotional_state' in morning:
                                st.write(f"**Emotional State:** {morning['emotional_state']}")
                            if 'market_news' in morning and morning['market_news']:
                                st.write(f"**Market News:** {morning['market_news']}")
                        
                        with col2:
                            if 'daily_goal' in morning and morning['daily_goal']:
                                st.write(f"**Daily Goal:** {morning['daily_goal']}")
                            if 'trading_process' in morning and morning['trading_process']:
                                st.write(f"**Trading Process:** {morning['trading_process']}")
                        
                        # Morning Screenshots
                        morning_screenshots = morning.get('morning_screenshots', [])
                        if morning_screenshots:
                            st.write("**Morning Screenshots:**")
                            for j, screenshot_data in enumerate(morning_screenshots):
                                if screenshot_data:
                                    if isinstance(screenshot_data, dict):
                                        screenshot_link = screenshot_data.get('url', '')
                                        screenshot_caption = screenshot_data.get('caption', f"Morning Screenshot {j+1}")
                                    else:
                                        screenshot_link = screenshot_data
                                        screenshot_caption = f"Morning Screenshot {j+1}"
                                    
                                    if screenshot_link and screenshot_link.strip():
                                        st.write(f"*{screenshot_caption}:*")
                                        display_image_full_size(screenshot_link, screenshot_caption)
                    
                    # Trading Section
                    if 'trading' in entry and entry['trading']:
                        st.markdown("### 📈 Trading Review")
                        trading = entry['trading']
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if 'pnl' in trading:
                                pnl = trading['pnl']
                                pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "gray"
                                st.markdown(f"**P&L:** <span style='color: {pnl_color}'>${pnl:.2f}</span>", unsafe_allow_html=True)
                            if 'process_grade' in trading:
                                st.write(f"**Process Grade:** {trading['process_grade']}")
                        
                        with col2:
                            if 'grade_reasoning' in trading and trading['grade_reasoning']:
                                st.write(f"**Grade Reasoning:** {trading['grade_reasoning']}")
                            if 'general_comments' in trading and trading['general_comments']:
                                st.write(f"**General Comments:** {trading['general_comments']}")
                        
                        # Trading Screenshots
                        trading_screenshots = trading.get('trading_screenshots', [])
                        if trading_screenshots:
                            st.write("**Trading Screenshots:**")
                            for j, screenshot_data in enumerate(trading_screenshots):
                                if screenshot_data:
                                    if isinstance(screenshot_data, dict):
                                        screenshot_link = screenshot_data.get('url', '')
                                        screenshot_caption = screenshot_data.get('caption', f"Trading Screenshot {j+1}")
                                    else:
                                        screenshot_link = screenshot_data
                                        screenshot_caption = f"Trading Screenshot {j+1}"
                                    
                                    if screenshot_link:
                                        st.write(f"*{screenshot_caption}:*")
                                        display_image_full_size(screenshot_link, screenshot_caption)
                    
                    # Trade Log Summary (if available)
                    if 'trade_log' in entry:
                        trade_log = entry['trade_log']
                        st.markdown("### 📊 Trade Log Summary")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Trade Fills:** {trade_log.get('fill_count', trade_log.get('trade_count', 'N/A'))}")
                            st.write(f"**Symbols:** {', '.join(trade_log.get('symbols', []))}")
                            st.write(f"**Total Volume:** {trade_log.get('total_volume', 'N/A')} contracts")
                            if 'win_rate' in trade_log:
                                st.write(f"**Win Rate:** {trade_log['win_rate']:.1f}%")
                        
                        with col2:
                            if 'completed_trades' in trade_log:
                                st.write(f"**Completed Trades:** {trade_log['completed_trades']}")
                            if 'avg_winner' in trade_log:
                                st.write(f"**Average Winner:** ${trade_log['avg_winner']:.2f}")
                            if 'avg_loser' in trade_log:
                                st.write(f"**Average Loser:** ${trade_log['avg_loser']:.2f}")
                    
                    # Evening Section
                    if 'evening' in entry and entry['evening']:
                        st.markdown("### 🌙 Evening Recap")
                        evening = entry['evening']
                        
                        if 'personal_recap' in evening and evening['personal_recap']:
                            st.write(f"**Personal Recap:** {evening['personal_recap']}")
                        if 'family_highlights' in evening and evening['family_highlights']:
                            st.write(f"**Family Highlights:** {evening['family_highlights']}")
        else:
            st.info("No trading data found for the selected date range.")

# Sidebar stats - FIXED RULE COMPLIANCE CALCULATION + PROCESS GRADE TRACKING
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Quick Stats")

# Calculate stats for different periods
def calculate_period_stats(days):
    period_data = {}
    current_date = date.today()
    for i in range(days):
        check_date = current_date - timedelta(days=i)
        date_key = get_date_key(check_date)
        if date_key in data:
            period_data[date_key] = data[date_key]
    return period_data

# 5-day and 30-day stats
recent_5_data = calculate_period_stats(5)
recent_30_data = calculate_period_stats(30)

def get_period_metrics(period_data):
    if not period_data:
        return 0, 0
    
    total_pnl = sum([entry.get('trading', {}).get('pnl', 0) for entry in period_data.values()])
    
    # Calculate EXACT rule compliance percentage (total rules followed / total rules)
    total_rules_followed = 0
    total_rules_possible = 0
    
    for entry in period_data.values():
        rule_compliance = entry.get('trading', {}).get('rule_compliance', {})
        if rule_compliance:  # Only count days with trading data
            # Count how many rules were followed vs total rules for this day
            rules_followed_today = sum(rule_compliance.values())
            total_rules_today = len(rule_compliance)
            
            total_rules_followed += rules_followed_today
            total_rules_possible += total_rules_today
    
    # Calculate exact percentage of all rules followed
    overall_compliance = (total_rules_followed / total_rules_possible * 100) if total_rules_possible > 0 else 0
    return total_pnl, overall_compliance

# Get metrics
pnl_5, compliance_5 = get_period_metrics(recent_5_data)
pnl_30, compliance_30 = get_period_metrics(recent_30_data)

# Calculate average grade from recent trading reviews
def get_recent_grades(period_data):
    grades = []
    for entry in period_data.values():
        grade = entry.get('trading', {}).get('process_grade')
        if grade:
            grades.append(grade)
    return grades

# Get recent grades for trending
recent_grades = get_recent_grades(recent_30_data)
if recent_grades:
    # Count frequency of each grade
    from collections import Counter
    grade_counts = Counter(recent_grades)
    most_common_grade = grade_counts.most_common(1)[0][0]
    
    # For display, show the trend of recent grades
    recent_5_grades = get_recent_grades(recent_5_data)
    if len(recent_5_grades) >= 2:
        latest_grade_trend = Counter(recent_5_grades).most_common(1)[0][0]
    else:
        latest_grade_trend = most_common_grade
else:
    most_common_grade = "N/A"
    latest_grade_trend = "N/A"

# Display metrics in organized way
st.sidebar.markdown("**📈 Last 5 Days**")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("P&L", f"${pnl_5:.2f}")
with col2:
    st.metric("Rules", f"{compliance_5:.1f}%")

st.sidebar.markdown("**📊 Last 30 Days**")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("P&L", f"${pnl_30:.2f}")
with col2:
    st.metric("Rules", f"{compliance_30:.1f}%")

# FIXED: Process Grade Trend
st.sidebar.markdown("**🎯 Process Grade**")
if recent_grades:
    grade_color = {
        "A": "green", 
        "B": "blue", 
        "C": "orange", 
        "D": "red", 
        "F": "darkred"
    }.get(latest_grade_trend, "gray")
    
    st.sidebar.markdown(f"Recent Trend: <span style='color: {grade_color}; font-weight: bold; font-size: 1.2em'>{latest_grade_trend}</span>", unsafe_allow_html=True)
    if len(recent_grades) > 1:
        st.sidebar.write(f"Last {len(recent_grades)} grades: {' → '.join(recent_grades[-5:])}")
else:
    st.sidebar.write("No grades yet")

# Export/Import functionality
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Data Management")

if st.sidebar.button("📤 Export Data"):
    st.sidebar.download_button(
        label="Download JSON",
        data=json.dumps(data, indent=2, default=str),
        file_name=f"trading_journal_{date.today().strftime('%Y%m%d')}.json",
        mime="application/json"
    )

uploaded_file = st.sidebar.file_uploader("📥 Import Data", type=['json'])
if uploaded_file is not None:
    try:
        imported_data = json.load(uploaded_file)
        data.update(imported_data)
        
        # Save to both GitHub and local
        if st.session_state.get('github_connected', False):
            for date_key, entry in imported_data.items():
                st.session_state.github_storage.save_journal_entry(date_key, entry, data)
        save_local_data(data)
        
        st.sidebar.success("Data imported successfully!")
        st.rerun()
    except:
        st.sidebar.error("Error importing data")
