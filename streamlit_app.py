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
import uuid

# Set page config
st.set_page_config(
    page_title="Trading Journal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme - UPDATED WITH NEW TRADE DAY STYLES
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
    
    .trade-card {
        background: rgba(0, 20, 40, 0.4);
        border: 1px solid #64ffda;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .tag-chip {
        display: inline-block;
        background: rgba(100, 255, 218, 0.2);
        border: 1px solid #64ffda;
        border-radius: 15px;
        padding: 0.2rem 0.8rem;
        margin: 0.2rem;
        font-size: 0.8rem;
        color: #64ffda;
    }
    
    .win-tag {
        background: rgba(0, 255, 0, 0.2);
        border-color: #00ff00;
        color: #00ff00;
    }
    
    .loss-tag {
        background: rgba(255, 0, 0, 0.2);
        border-color: #ff0000;
        color: #ff0000;
    }
    
    .pending-tag {
        background: rgba(255, 255, 0, 0.2);
        border-color: #ffff00;
        color: #ffff00;
    }
    
    .import-summary {
        background: rgba(100, 255, 218, 0.1);
        border: 1px solid #64ffda;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
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
            return None, None
            
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
        
        # Convert content to JSON and encode
        json_content = json.dumps(content, indent=2, default=str)
        encoded_content = base64.b64encode(json_content.encode()).decode()
        
        data = {
            'message': f'Update {file_path}',
            'content': encoded_content
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
    
    def upload_screenshot(self, file_data, filename, date_folder):
        """Upload screenshot to GitHub repo"""
        if not self.connected:
            return None
            
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Encode file data
        encoded_content = base64.b64encode(file_data).decode()
        file_path = f"screenshots/{date_folder}/{filename}"
        
        data = {
            'message': f'Upload screenshot {filename}',
            'content': encoded_content
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

# TRADE DAY FUNCTIONS
def get_all_tags(data):
    """Get all unique tags from the system"""
    return data.get('tags', [])

def add_tag_to_system(data, new_tag):
    """Add a new tag to the global tag system"""
    if 'tags' not in data:
        data['tags'] = []
    
    # Normalize tag (lowercase, strip whitespace)
    normalized_tag = new_tag.strip().lower()
    
    if normalized_tag and normalized_tag not in [tag.lower() for tag in data['tags']]:
        data['tags'].append(new_tag.strip())
        data['tags'].sort()  # Keep tags sorted
    
    return data

def create_new_trade(trade_description, tags, outcome, screenshot_data=None):
    """Create a new trade entry"""
    return {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'description': trade_description,
        'tags': tags,
        'outcome': outcome,  # 'win', 'loss', 'pending'
        'screenshot': screenshot_data  # {'url': '', 'caption': ''} or None
    }

def get_trade_statistics(data):
    """Get statistics across all trades"""
    all_trades = []
    
    # Collect all trades from all dates
    for date_key, entry in data.items():
        if date_key != 'tags' and 'trade_day' in entry:
            trades = entry['trade_day'].get('trades', [])
            for trade in trades:
                trade['date'] = date_key
                all_trades.append(trade)
    
    if not all_trades:
        return {}
    
    # Calculate statistics
    total_trades = len(all_trades)
    win_trades = [t for t in all_trades if t.get('outcome') == 'win']
    loss_trades = [t for t in all_trades if t.get('outcome') == 'loss']
    break_even_trades = [t for t in all_trades if t.get('outcome') == 'break-even']
    pending_trades = [t for t in all_trades if t.get('outcome') == 'pending']
    
    # Win rate calculation (exclude break-evens and pending from denominator)
    completed_trades = len(win_trades) + len(loss_trades)
    win_rate = (len(win_trades) / completed_trades * 100) if completed_trades > 0 else 0
    
    # Tag statistics
    tag_counts = {}
    tag_win_rates = {}
    
    for trade in all_trades:
        for tag in trade.get('tags', []):
            if tag not in tag_counts:
                tag_counts[tag] = {'total': 0, 'wins': 0, 'losses': 0}
            
            tag_counts[tag]['total'] += 1
            if trade.get('outcome') == 'win':
                tag_counts[tag]['wins'] += 1
            elif trade.get('outcome') == 'loss':
                tag_counts[tag]['losses'] += 1
    
    # Calculate win rates for each tag
    for tag, counts in tag_counts.items():
        completed = counts['wins'] + counts['losses']
        tag_win_rates[tag] = (counts['wins'] / completed * 100) if completed > 0 else 0
    
    return {
        'total_trades': total_trades,
        'win_trades': len(win_trades),
        'loss_trades': len(loss_trades),
        'break_even_trades': len(break_even_trades),
        'pending_trades': len(pending_trades),
        'win_rate': win_rate,
        'tag_counts': tag_counts,
        'tag_win_rates': tag_win_rates,
        'recent_trades': sorted(all_trades, key=lambda x: x['timestamp'], reverse=True)[:10]
    }

# NEW: TRADE LOG PARSING AND GROUPING FUNCTIONS
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
        'daily_pnl': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'total_trades': 0,
        'avg_winner': 0,
        'avg_loser': 0,
        'win_rate': 0,
        'trade_pnls': []
    }
    
    # Track positions by symbol to calculate individual trade P&L
    open_positions = {}
    individual_trade_pnls = []
    
    for trade in trades:
        # Basic analysis
        symbol = trade.get('Symbol', '')
        side = trade.get('Side', '')
        quantity = int(trade.get('Quantity', 0))
        price = float(trade.get('Price', 0))
        
        analysis['symbols'].add(symbol)
        analysis['order_types'].add(side)
        analysis['total_volume'] += abs(quantity)
        analysis['prices'].append(price)
        
        if side.upper() == 'BUY':
            analysis['buy_orders'] += 1
        else:
            analysis['sell_orders'] += 1
        
        # Track positions for P&L calculation
        if symbol not in open_positions:
            open_positions[symbol] = {'qty': 0, 'avg_price': 0, 'total_cost': 0}
        
        # Calculate P&L for position changes
        pnl_change = 0
        point_value = 1  # Assume $1 per point, adjust as needed
        
        current_pos = open_positions[symbol]
        
        if side.upper() == 'BUY':
            if current_pos['qty'] >= 0:
                # Adding to long or opening long
                new_total_cost = current_pos['total_cost'] + (quantity * price)
                new_qty = current_pos['qty'] + quantity
                open_positions[symbol] = {
                    'qty': new_qty,
                    'avg_price': new_total_cost / new_qty if new_qty != 0 else 0,
                    'total_cost': new_total_cost
                }
            else:
                # Covering short position
                avg_price = current_pos['avg_price']
                price_diff = avg_price - price
                pnl_change = quantity * price_diff * point_value
                
                remaining_qty = current_pos['qty'] + quantity
                if remaining_qty <= 0:
                    open_positions[symbol]['qty'] = remaining_qty
                    open_positions[symbol]['total_cost'] = remaining_qty * avg_price
                else:
                    open_positions[symbol] = {'qty': 0, 'avg_price': 0, 'total_cost': 0}
        else:
            if current_pos['qty'] <= 0:
                # Adding to short or opening short
                new_total_cost = current_pos['total_cost'] - (quantity * price)
                new_qty = current_pos['qty'] - quantity
                open_positions[symbol] = {
                    'qty': new_qty,
                    'avg_price': abs(new_total_cost / new_qty) if new_qty != 0 else 0,
                    'total_cost': new_total_cost
                }
            else:
                # Closing long position
                avg_price = current_pos['avg_price']
                price_diff = price - avg_price
                pnl_change = quantity * price_diff * point_value
                
                remaining_qty = current_pos['qty'] - quantity
                if remaining_qty >= 0:
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

# Account Balance Functions with Transaction Support
def calculate_running_balance(data, target_date, starting_balance, start_date):
    """Calculate running account balance up to target date including deposits/withdrawals"""
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
        
        # Add trading P&L
        if date_key in data and 'trading' in data[date_key]:
            pnl = data[date_key]['trading'].get('pnl', 0)
            running_balance += pnl
        
        # Add deposits/withdrawals for this date
        transactions = get_transactions_for_date(data, current_date)
        for transaction in transactions:
            if transaction['type'] == 'deposit':
                running_balance += transaction['amount']
            elif transaction['type'] == 'withdrawal':
                running_balance -= transaction['amount']
        
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

# Transaction Management Functions
def get_all_transactions(data):
    """Get all transactions from data"""
    return data.get('transactions', [])

def get_transactions_for_date(data, target_date):
    """Get transactions for a specific date"""
    target_date_str = target_date.strftime("%Y-%m-%d") if isinstance(target_date, date) else target_date
    transactions = get_all_transactions(data)
    return [t for t in transactions if t.get('date') == target_date_str]

def add_transaction(data, transaction_type, amount, description, transaction_date):
    """Add a new transaction"""
    if 'transactions' not in data:
        data['transactions'] = []
    
    transaction = {
        'id': str(uuid.uuid4()),
        'type': transaction_type,  # 'deposit' or 'withdrawal'
        'amount': amount,
        'description': description,
        'date': transaction_date.strftime("%Y-%m-%d") if isinstance(transaction_date, date) else transaction_date,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data['transactions'].append(transaction)
    return data

def delete_transaction(data, transaction_id):
    """Delete a transaction by ID"""
    if 'transactions' in data:
        data['transactions'] = [t for t in data['transactions'] if t.get('id') != transaction_id]
    return data

# Initialize session state
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()
if 'page' not in st.session_state:
    st.session_state.page = "📊 Calendar View"  # STARTS ON CALENDAR!
if 'github_connected' not in st.session_state:
    st.session_state.github_connected = False
if 'github_storage' not in st.session_state:
    st.session_state.github_storage = GitHubStorage()

# Main header - UPDATED VERSION TO 7.5
st.markdown('<h1 class="main-header">📊 Trading Journal v7.5</h1>', unsafe_allow_html=True)

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

# Account Balance Management in Sidebar
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
else:
    # Show current balance
    current_balance = calculate_running_balance(
        data, 
        st.session_state.current_date, 
        account_settings['starting_balance'], 
        account_settings['start_date']
    )
    
    # Balance display with color coding
    balance_color = "#00ff00" if current_balance >= account_settings['starting_balance'] else "#ff0000"
    profit_loss = current_balance - account_settings['starting_balance']
    
    st.sidebar.markdown(f'''
    <div class="balance-display">
        <div class="balance-amount" style="color: {balance_color};">${current_balance:,.2f}</div>
        <div style="color: {balance_color};">
            {"📈" if profit_loss >= 0 else "📉"} ${abs(profit_loss):,.2f}
        </div>
    </div>
    ''', unsafe_allow_html=True)

# Sidebar GitHub status (commented out by default)
# st.sidebar.title("☁️ Cloud Storage")
# if st.session_state.get('github_connected', False):
#     st.sidebar.success("✅ Connected to GitHub")
#     repo_url = f"https://github.com/{st.session_state.repo_owner}/{st.session_state.repo_name}"
#     st.sidebar.markdown(f"🔗 [View Repository]({repo_url})")
#     screenshots_url = f"{repo_url}/tree/main/screenshots"
#     st.sidebar.markdown(f"📸 [View Screenshots]({screenshots_url})")
# else:
#     st.sidebar.warning("⚠️ GitHub not connected")

# MOVED: Date selector - Now ABOVE navigation menu
st.sidebar.markdown("---")
st.sidebar.title("📅 Date Selection")
selected_date = st.sidebar.date_input(
    "Select Date",
    value=st.session_state.current_date,
    key="date_selector"
)

# Update current date when changed
if selected_date != st.session_state.current_date:
    st.session_state.current_date = selected_date

# UPDATED SIDEBAR NAVIGATION - REMOVED TRADE LOG ANALYSIS
st.sidebar.markdown("---")
st.sidebar.title("📋 Navigation")

# Navigation buttons - CALENDAR VIEW FIRST, THEN TRADE DAY!
if st.sidebar.button("📊 Calendar View", key="nav_calendar", use_container_width=True):
    st.session_state.page = "📊 Calendar View"

if st.sidebar.button("🌅 Morning Prep", key="nav_morning", use_container_width=True):
    st.session_state.page = "🌅 Morning Prep"

# TRADE DAY NAVIGATION BUTTON (Enhanced with import functionality)
if st.sidebar.button("📈 Trade Day", key="nav_trade_day", use_container_width=True):
    st.session_state.page = "📈 Trade Day"

if st.sidebar.button("📈 Trading Review", key="nav_trading", use_container_width=True):
    st.session_state.page = "📈 Trading Review"

if st.sidebar.button("🌙 Evening Recap", key="nav_evening", use_container_width=True):
    st.session_state.page = "🌙 Evening Recap"

if st.sidebar.button("📚 Historical Analysis", key="nav_history", use_container_width=True):
    st.session_state.page = "📚 Historical Analysis"

# Enhanced Balance History Page
if st.sidebar.button("💰 Balance & Ledger", key="nav_balance_history", use_container_width=True):
    st.session_state.page = "💰 Balance & Ledger"

# Tag Management Button
if st.sidebar.button("🏷️ Tag Management", key="nav_tag_management", use_container_width=True):
    st.session_state.page = "🏷️ Tag Management"

page = st.session_state.page

date_key = get_date_key(selected_date)

# UPDATED: Initialize date entry if doesn't exist - ADDED TRADE_DAY
if date_key not in data:
    data[date_key] = {
        'morning': {},
        'trade_day': {},  # Initialize trade_day section
        'trading': {},
        'evening': {},
        'rules': []
    }

current_entry = data[date_key]

# Enhanced Balance History Page with Transaction Ledger
if page == "💰 Balance & Ledger":
    st.markdown('<div class="section-header">💰 Account Balance & Transaction Ledger</div>', unsafe_allow_html=True)
    
    account_settings = get_account_settings(data)
    
    if not account_settings.get('starting_balance') or not account_settings.get('start_date'):
        st.warning("⚠️ Please set up your account balance tracking in the sidebar first.")
        st.info("Go to the sidebar and expand '⚙️ Setup Account Tracking' to get started.")
    else:
        # Show balance history
        st.subheader("📈 Balance History")
        
        # Get date range
        start_date = datetime.strptime(account_settings['start_date'], "%Y-%m-%d").date()
        end_date = date.today()
        
        # Calculate daily balances
        balance_data = []
        current_date = start_date
        running_balance = account_settings['starting_balance']
        
        while current_date <= end_date:
            date_key_temp = get_date_key(current_date)
            
            # Get P&L for the day
            daily_pnl = 0
            if date_key_temp in data and 'trading' in data[date_key_temp]:
                daily_pnl = data[date_key_temp]['trading'].get('pnl', 0)
            
            # Get transactions for the day
            transactions = get_transactions_for_date(data, current_date)
            daily_deposits = sum(t['amount'] for t in transactions if t['type'] == 'deposit')
            daily_withdrawals = sum(t['amount'] for t in transactions if t['type'] == 'withdrawal')
            net_transactions = daily_deposits - daily_withdrawals
            
            # Update running balance
            running_balance += daily_pnl + net_transactions
            
            balance_data.append({
                'date': current_date,
                'date_str': current_date.strftime("%Y-%m-%d"),
                'balance': running_balance,
                'daily_pnl': daily_pnl,
                'daily_deposits': daily_deposits,
                'daily_withdrawals': daily_withdrawals,
                'net_transactions': net_transactions
            })
            
            current_date += timedelta(days=1)
        
        # Create balance chart
        if balance_data:
            df_balance = pd.DataFrame(balance_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_balance['date'],
                y=df_balance['balance'],
                mode='lines',
                name='Account Balance',
                line=dict(color='#64ffda', width=2)
            ))
            
            fig.update_layout(
                title="Account Balance Over Time",
                xaxis_title="Date",
                yaxis_title="Balance ($)",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Transaction Management
        st.subheader("💳 Add Transaction")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            transaction_type = st.selectbox(
                "Transaction Type",
                ["deposit", "withdrawal"]
            )
        
        with col2:
            transaction_amount = st.number_input(
                "Amount ($)",
                min_value=0.01,
                step=0.01,
                format="%.2f"
            )
        
        with col3:
            transaction_date = st.date_input(
                "Date",
                value=selected_date,
                max_value=date.today()
            )
        
        with col4:
            transaction_description = st.text_input(
                "Description",
                placeholder="Reason for transaction..."
            )
        
        if st.button("💾 Add Transaction"):
            if transaction_amount > 0 and transaction_description.strip():
                data = add_transaction(data, transaction_type, transaction_amount, transaction_description, transaction_date)
                
                # Save
                if st.session_state.get('github_connected', False):
                    if st.session_state.github_storage.save_journal_entry("transactions", {}, data):
                        st.success(f"✅ {transaction_type.title()} of ${transaction_amount:.2f} added!")
                    else:
                        save_local_data(data)
                        st.success(f"💾 {transaction_type.title()} of ${transaction_amount:.2f} added locally!")
                else:
                    save_local_data(data)
                    st.success(f"💾 {transaction_type.title()} of ${transaction_amount:.2f} added locally!")
                
                st.rerun()
            else:
                st.warning("Please enter a valid amount and description.")
        
        # Show recent transactions
        all_transactions = get_all_transactions(data)
        if all_transactions:
            st.subheader("📋 Recent Transactions")
            
            # Sort by date (newest first)
            sorted_transactions = sorted(all_transactions, key=lambda x: x['date'], reverse=True)
            
            for transaction in sorted_transactions[:10]:  # Show last 10
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    transaction_color = "#00ff00" if transaction['type'] == 'deposit' else "#ff0000"
                    symbol = "+" if transaction['type'] == 'deposit' else "-"
                    
                    st.markdown(f"""
                    **{transaction['date']}** - {transaction['description']}<br>
                    <span style='color: {transaction_color}; font-weight: bold;'>{symbol}${transaction['amount']:.2f}</span>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"🗑️", key=f"delete_transaction_{transaction['id']}", help="Delete transaction"):
                        data = delete_transaction(data, transaction['id'])
                        
                        # Save
                        if st.session_state.get('github_connected', False):
                            if st.session_state.github_storage.save_journal_entry("transactions", {}, data):
                                st.success("✅ Transaction deleted! Balance will update.")
                            else:
                                save_local_data(data)
                                st.success("💾 Transaction deleted! Balance will update.")
                        else:
                            save_local_data(data)
                            st.success("💾 Transaction deleted! Balance will update.")
                        st.rerun()
        
        # Export functionality
        st.markdown("---")
        if st.button("📤 Export Complete Ledger as CSV"):
            # Create comprehensive export with balance data
            export_data = []
            for day in balance_data:
                export_data.append({
                    'Date': day['date_str'],
                    'Balance': day['balance'],
                    'Trading_PnL': day['daily_pnl'],
                    'Deposits': day['daily_deposits'],
                    'Withdrawals': day['daily_withdrawals'],
                    'Net_Transactions': day['net_transactions']
                })
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Download Balance Ledger CSV",
                data=csv,
                file_name=f"balance_ledger_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

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
    
    # Create header row
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    header_cols = st.columns(7)
    for i, day in enumerate(days):
        header_cols[i].markdown(f"**{day}**")
    
    # Create calendar grid
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")  # Empty cell for days not in this month
            else:
                current_day = first_day.replace(day=day)
                day_key = get_date_key(current_day)
                
                # Calculate PnL for this day
                day_pnl = 0
                has_data = False
                rule_compliance = 0
                
                if day_key in data:
                    has_data = True
                    if 'trading' in data[day_key] and 'pnl' in data[day_key]['trading']:
                        day_pnl = data[day_key]['trading']['pnl']
                    
                    # Calculate rule compliance
                    rules = data[day_key].get('rules', [])
                    rule_compliance_dict = data[day_key].get('trading', {}).get('rule_compliance', {})
                    if rules and rule_compliance_dict:
                        total_rules = len([r for r in rules if r.strip()])
                        followed_rules = sum(rule_compliance_dict.values())
                        rule_compliance = (followed_rules / total_rules * 100) if total_rules > 0 else 0
                
                # Determine cell color
                if not has_data:
                    cell_color = "white"
                    icon = "⚪"
                elif rule_compliance >= 80:
                    cell_color = "green"
                    icon = "🟢"
                else:
                    cell_color = "red"
                    icon = "🔴"
                
                # Create clickable day cell
                if cols[i].button(f"{icon}\n{day}\n${day_pnl:.0f}", key=f"day_{day_key}"):
                    st.session_state.current_date = current_day
                    st.session_state.page = "🌅 Morning Prep"
                    st.rerun()
    
    # Week summary row
    st.markdown("---")
    
    # Calculate week totals
    week_cols = st.columns(8)
    week_cols[0].markdown("**Week Totals:**")
    
    for week_num, week in enumerate(cal):
        if week_num < 7:  # Only show first 7 weeks to fit in columns
            week_pnl = 0
            for day in week:
                if day != 0:
                    current_day = first_day.replace(day=day)
                    day_key = get_date_key(current_day)
                    if day_key in data and 'trading' in data[day_key]:
                        week_pnl += data[day_key]['trading'].get('pnl', 0)
            
            # Display week total - treating weeks as calendar days
            week_color = "green" if week_pnl > 0 else "red" if week_pnl < 0 else "gray"
            week_cols[week_num + 1].markdown(f'''
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

# ======== ENHANCED TRADE DAY PAGE WITH IMPORT AND STATISTICS ========
elif page == "📈 Trade Day":
    st.markdown('<div class="section-header">📈 Live Trade Day</div>', unsafe_allow_html=True)
    
    # Show current date and delete option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📅 {selected_date.strftime('%A, %B %d, %Y')}")
    with col2:
        if st.button("🗑️ Delete Entry", key="delete_trade_day", help="Delete all trade day data for this date"):
            if 'trade_day' in current_entry:
                del current_entry['trade_day']
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                save_local_data(data)
                st.success("Trade day entry deleted!")
                st.rerun()
    
    # Initialize trade_day if doesn't exist
    if 'trade_day' not in current_entry:
        current_entry['trade_day'] = {'market_observations': '', 'trades': [], 'trade_statistics': {}}
    
    # NEW: Trade Log Import Section
    st.subheader("📊 Import Trades from Log")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        trade_log_file = st.file_uploader(
            "Upload trade log file (CSV/TSV)",
            type=['txt', 'csv', 'tsv'],
            help="Upload your broker's trade log to automatically create trade entries",
            key="trade_log_import"
        )
        
        if trade_log_file:
            st.info("💡 This will parse your trade log and create individual trade entries that you can enhance with tags and screenshots.")
            
            # Show expected format info
            with st.expander("📋 Expected File Format", expanded=False):
                st.markdown("""
                **Your trade log file should be a CSV or TSV with headers like:**
                - `Symbol` - Stock/instrument symbol (e.g., AAPL, SPY)
                - `Side` - BUY or SELL
                - `Quantity` - Number of shares/contracts
                - `Price` - Execution price
                - `Time` - Time of execution (optional)
                
                **Example:**
                ```
                Symbol,Side,Quantity,Price,Time
                AAPL,BUY,100,150.25,09:30:15
                AAPL,SELL,100,150.75,09:45:22
                ```
                
                ⚠️ **Note:** Empty cells will be handled gracefully, but Symbol, Side, Quantity, and Price are recommended for best results.
                """)
    
    with col2:
        if trade_log_file:
            if st.button("📤 Process Trade Log", type="primary"):
                try:
                    file_content = trade_log_file.read().decode('utf-8')
                    trades, error = parse_trade_log(file_content)
                    
                    if error:
                        st.error(f"Error parsing file: {error}")
                    else:
                        # Analyze trades and create statistics
                        analysis = analyze_trades(trades)
                        
                        # Convert to individual trade entries
                        imported_trades = []
                        for trade in trades:
                            new_trade = {
                                'id': str(uuid.uuid4()),
                                'timestamp': trade.get('Time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                'description': f"{trade.get('Side', 'Unknown')} {trade.get('Quantity', 0)} {trade.get('Symbol', 'Unknown')} @ {trade.get('Price', 0)}",
                                'tags': ['imported'],
                                'outcome': 'pending',  # Will be calculated from P&L later
                                'screenshot': None,
                                'raw_data': trade
                            }
                            imported_trades.append(new_trade)
                        
                        # Add imported trades to current entry
                        existing_trades = current_entry['trade_day'].get('trades', [])
                        current_entry['trade_day']['trades'] = existing_trades + imported_trades
                        
                        # Save trade statistics
                        current_entry['trade_day']['trade_statistics'] = {
                            'total_trades': analysis.get('total_trades', 0),
                            'winning_trades': analysis.get('winning_trades', 0),
                            'losing_trades': analysis.get('losing_trades', 0),
                            'break_even_trades': 0,  # Calculate based on +/- $5
                            'avg_winner': analysis.get('avg_winner', 0),
                            'avg_loser': analysis.get('avg_loser', 0),
                            'win_rate': analysis.get('win_rate', 0),
                            'gross_pnl': analysis.get('daily_pnl', 0),
                            'total_volume': analysis.get('total_volume', 0),
                            'avg_trade_duration_winners': 0,  # Will be calculated
                            'avg_trade_duration_losers': 0,   # Will be calculated
                            'trade_pnls': analysis.get('trade_pnls', [])
                        }
                        
                        # Calculate break-even trades (within +/- $5)
                        trade_pnls = analysis.get('trade_pnls', [])
                        break_even_count = len([pnl for pnl in trade_pnls if -5 <= pnl <= 5])
                        current_entry['trade_day']['trade_statistics']['break_even_trades'] = break_even_count
                        
                        # Save
                        if st.session_state.get('github_connected', False):
                            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                                st.success(f"✅ Successfully imported {len(imported_trades)} trades!")
                            else:
                                save_local_data(data)
                                st.success(f"💾 Successfully imported {len(imported_trades)} trades locally!")
                        else:
                            save_local_data(data)
                            st.success(f"💾 Successfully imported {len(imported_trades)} trades locally!")
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error processing trade log: {str(e)}")
    
    # Display trade statistics if available
    trade_stats = current_entry['trade_day'].get('trade_statistics', {})
    if trade_stats and any(trade_stats.values()):
        st.markdown("---")
        st.subheader("📊 Trade Statistics")
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", trade_stats.get('total_trades', 0))
            st.metric("Win/Loss Ratio", f"{trade_stats.get('winning_trades', 0)}/{trade_stats.get('losing_trades', 0)}")
        
        with col2:
            avg_winner = trade_stats.get('avg_winner', 0)
            avg_loser = trade_stats.get('avg_loser', 0)
            st.metric("Avg Winner", f"${avg_winner:.2f}" if avg_winner else "$0.00")
            st.metric("Avg Loser", f"${avg_loser:.2f}" if avg_loser else "$0.00")
        
        with col3:
            win_rate = trade_stats.get('win_rate', 0)
            break_even = trade_stats.get('break_even_trades', 0)
            st.metric("Win Rate", f"{win_rate:.1f}%")
            st.metric("Break Even (±$5)", break_even)
        
        with col4:
            gross_pnl = trade_stats.get('gross_pnl', 0)
            pnl_color = "normal" if gross_pnl == 0 else "inverse" if gross_pnl < 0 else "normal"
            st.metric("Gross P&L", f"${gross_pnl:.2f}", delta=None, delta_color=pnl_color)
            st.metric("Total Volume", f"{trade_stats.get('total_volume', 0):.0f}")
        
        # Commission input and net P&L calculation
        st.markdown("### 💰 P&L and Commissions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            commission_input = st.number_input(
                "Session Commissions ($)",
                min_value=0.0,
                value=trade_stats.get('commissions', 0.0),
                step=0.01,
                format="%.2f",
                help="Enter total commission costs for this session"
            )
        
        with col2:
            net_pnl = gross_pnl - commission_input
            st.metric("Net P&L", f"${net_pnl:.2f}", delta=f"${-commission_input:.2f}" if commission_input > 0 else None)
        
        with col3:
            if st.button("🔄 Update Trading Review P&L", help="Sync P&L to Trading Review page"):
                # Update the trading review P&L with net P&L from trade day
                if 'trading' not in current_entry:
                    current_entry['trading'] = {}
                
                current_entry['trading']['pnl'] = net_pnl
                current_entry['trading']['trade_day_sync'] = True
                current_entry['trading']['gross_pnl'] = gross_pnl
                current_entry['trading']['commissions'] = commission_input
                
                # Save commissions to trade statistics
                current_entry['trade_day']['trade_statistics']['commissions'] = commission_input
                current_entry['trade_day']['trade_statistics']['net_pnl'] = net_pnl
                
                if st.session_state.get('github_connected', False):
                    if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                        st.success(f"✅ Trading Review P&L updated to ${net_pnl:.2f}!")
                    else:
                        save_local_data(data)
                        st.success(f"💾 Trading Review P&L updated locally!")
                else:
                    save_local_data(data)
                    st.success(f"💾 Trading Review P&L updated locally!")
    
    st.markdown("---")
    
    # Market Observations Section
    st.subheader("🌍 Market Observations")
    market_observations = st.text_area(
        "What did you observe about the market today?",
        value=current_entry['trade_day'].get('market_observations', ""),
        height=100,
        placeholder="Market conditions, unusual activity, news events..."
    )
    
    # Manual Trade Entry Section
    st.subheader("➕ Add Manual Trade")
    
    with st.form("new_trade_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            trade_description = st.text_area(
                "Trade Description",
                placeholder="Describe your trade setup, entry, exit...",
                height=100
            )
            
            # Tag Selection (existing + new)
            existing_tags = get_all_tags(data)
            selected_tags = st.multiselect(
                "Select Tags",
                options=existing_tags,
                help="Choose relevant tags for this trade"
            )
            
            # New tags input
            new_tags_input = st.text_input(
                "Add New Tags (comma-separated)",
                placeholder="scalp, breakout, news-driven",
                help="Enter new tags separated by commas"
            )
            
            # Parse new tags
            new_tags = []
            if new_tags_input.strip():
                new_tags = [tag.strip() for tag in new_tags_input.split(',') if tag.strip()]
            
            all_trade_tags = selected_tags + new_tags
        
        with col2:
            trade_outcome = st.selectbox(
                "Trade Outcome",
                options=['pending', 'win', 'loss', 'break-even'],
                help="Select the outcome of this trade"
            )
        
        # Screenshot Upload Section
        st.markdown("**📷 Trade Screenshot**")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            trade_screenshot = st.file_uploader(
                "Upload trade screenshot",
                type=['png', 'jpg', 'jpeg'],
                key="manual_trade_screenshot"
            )
        
        with col2:
            screenshot_caption = st.text_input(
                "Screenshot Caption",
                placeholder="Entry setup, exit, P&L...",
                key="manual_trade_caption"
            )
        
        submitted = st.form_submit_button("💾 Add Trade", type="primary")
        
        if submitted and trade_description.strip():
            # Handle screenshot upload
            screenshot_data = None
            if trade_screenshot and screenshot_caption.strip():
                if st.session_state.get('github_connected', False):
                    # Upload to GitHub
                    file_data = trade_screenshot.getvalue()
                    timestamp = int(datetime.now().timestamp())
                    filename = f"trade_{timestamp}_{trade_screenshot.name}"
                    screenshot_url = st.session_state.github_storage.upload_screenshot(
                        file_data, filename, date_key
                    )
                    if screenshot_url:
                        screenshot_data = {'url': screenshot_url, 'caption': screenshot_caption}
                else:
                    # Save locally
                    screenshot_path = save_uploaded_file_local(trade_screenshot, date_key, "trade")
                    if screenshot_path:
                        screenshot_data = {'url': screenshot_path, 'caption': screenshot_caption}
            
            # Add new tags to system
            for tag in new_tags:
                data = add_tag_to_system(data, tag)
            
            # Create trade
            new_trade = create_new_trade(
                trade_description, 
                all_trade_tags, 
                trade_outcome, 
                screenshot_data
            )
            
            # Add trade to current entry
            if 'trades' not in current_entry['trade_day']:
                current_entry['trade_day']['trades'] = []
            
            current_entry['trade_day']['trades'].append(new_trade)
            current_entry['trade_day']['market_observations'] = market_observations
            
            # Save
            if st.session_state.get('github_connected', False):
                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                    st.success("✅ Trade added and saved to GitHub!")
                else:
                    save_local_data(data)
                    st.success("💾 Trade added and saved locally!")
            else:
                save_local_data(data)
                st.success("💾 Trade added and saved locally!")
            
            # Clear the form by rerunning
            st.rerun()
    
    st.markdown("---")
    
    # Display Existing Trades for Today
    existing_trades = current_entry['trade_day'].get('trades', [])
    
    if existing_trades:
        st.subheader(f"📋 Today's Trades ({len(existing_trades)})")
        
        for i, trade in enumerate(existing_trades):
            with st.expander(f"Trade {i+1}: {trade['description'][:50]}..." if len(trade['description']) > 50 else f"Trade {i+1}: {trade['description']}"):
                
                # Check if this trade is being edited
                edit_key = f"edit_trade_{trade['id']}"
                is_editing = st.session_state.get(edit_key, False)
                
                if not is_editing:
                    # Display mode
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Time:** {trade['timestamp']}")
                        st.markdown(f"**Description:** {trade['description']}")
                        
                        # Display tags
                        if trade.get('tags'):
                            tags_html = ""
                            for tag in trade['tags']:
                                tags_html += f'<span class="tag-chip">{tag}</span>'
                            st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)
                        else:
                            st.markdown("**Tags:** None")
                        
                        # Display outcome with styling
                        outcome = trade.get('outcome', 'pending')
                        outcome_colors = {
                            'win': ('#00ff00', '✅'),
                            'loss': ('#ff0000', '❌'), 
                            'break-even': ('#ffff00', '➖'),
                            'pending': ('#ffff00', '⏳')
                        }
                        color, icon = outcome_colors.get(outcome, ('#ffffff', '❓'))
                        st.markdown(f"**Outcome:** <span style='color: {color}; font-weight: bold;'>{icon} {outcome.upper()}</span>", unsafe_allow_html=True)
                        
                        # Display screenshot if exists
                        if trade.get('screenshot'):
                            st.markdown(f"**Screenshot:** {trade['screenshot']['caption']}")
                            display_image_full_size(trade['screenshot']['url'], trade['screenshot']['caption'])
                    
                    with col2:
                        # Edit button
                        if st.button(f"✏️ Edit", key=f"start_edit_{trade['id']}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                        
                        # Delete button
                        if st.button(f"🗑️ Delete", key=f"delete_{trade['id']}"):
                            current_entry['trade_day']['trades'] = [t for t in current_entry['trade_day']['trades'] if t['id'] != trade['id']]
                            
                            # Save
                            if st.session_state.get('github_connected', False):
                                st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                            save_local_data(data)
                            st.success("Trade deleted!")
                            st.rerun()
                        
                        # Add Screenshot to Existing Trade
                        st.markdown("**📷 Add Screenshot**")
                        screenshot_file = st.file_uploader(
                            "Upload screenshot",
                            type=['png', 'jpg', 'jpeg'],
                            key=f"screenshot_{trade['id']}"
                        )
                        
                        screenshot_caption = st.text_input(
                            "Caption",
                            placeholder="Screenshot description...",
                            key=f"caption_{trade['id']}"
                        )
                        
                        if st.button(f"📷 Add Screenshot", key=f"add_screenshot_{trade['id']}"):
                            if screenshot_file and screenshot_caption.strip():
                                # Handle screenshot upload
                                screenshot_data = None
                                if st.session_state.get('github_connected', False):
                                    # Upload to GitHub
                                    file_data = screenshot_file.getvalue()
                                    timestamp = int(datetime.now().timestamp())
                                    filename = f"trade_{timestamp}_{screenshot_file.name}"
                                    screenshot_url = st.session_state.github_storage.upload_screenshot(
                                        file_data, filename, date_key
                                    )
                                    if screenshot_url:
                                        screenshot_data = {'url': screenshot_url, 'caption': screenshot_caption}
                                else:
                                    # Save locally
                                    screenshot_path = save_uploaded_file_local(screenshot_file, date_key, "trade")
                                    if screenshot_path:
                                        screenshot_data = {'url': screenshot_path, 'caption': screenshot_caption}
                                
                                if screenshot_data:
                                    # Update trade with screenshot
                                    for j, t in enumerate(current_entry['trade_day']['trades']):
                                        if t['id'] == trade['id']:
                                            current_entry['trade_day']['trades'][j]['screenshot'] = screenshot_data
                                            break
                                    
                                    # Save
                                    if st.session_state.get('github_connected', False):
                                        if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                                            st.success("✅ Screenshot added and saved!")
                                        else:
                                            save_local_data(data)
                                            st.success("💾 Screenshot added and saved locally!")
                                    else:
                                        save_local_data(data)
                                        st.success("💾 Screenshot added and saved locally!")
                                    
                                    st.rerun()
                            else:
                                st.warning("Please select a file and enter a caption.")
                
                else:
                    # Edit mode
                    st.markdown("### Editing Trade")
                    
                    edit_description = st.text_area(
                        "Description",
                        value=trade['description'],
                        key=f"edit_desc_{trade['id']}"
                    )
                    
                    # Edit tags
                    existing_tags = get_all_tags(data)
                    current_tags = trade.get('tags', [])
                    
                    edit_tags = st.multiselect(
                        "Tags",
                        options=existing_tags,
                        default=current_tags,
                        key=f"edit_tags_{trade['id']}"
                    )
                    
                    edit_outcome = st.selectbox(
                        "Outcome",
                        options=['pending', 'win', 'loss', 'break-even'],
                        index=['pending', 'win', 'loss', 'break-even'].index(trade.get('outcome', 'pending')),
                        key=f"edit_outcome_{trade['id']}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"💾 Save Changes", key=f"save_{trade['id']}"):
                            # Update trade
                            for j, t in enumerate(current_entry['trade_day']['trades']):
                                if t['id'] == trade['id']:
                                    current_entry['trade_day']['trades'][j]['description'] = edit_description
                                    current_entry['trade_day']['trades'][j]['tags'] = edit_tags
                                    current_entry['trade_day']['trades'][j]['outcome'] = edit_outcome
                                    break
                            
                            # Save
                            if st.session_state.get('github_connected', False):
                                st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                            save_local_data(data)
                            
                            st.session_state[edit_key] = False
                            st.success("Trade updated!")
                            st.rerun()
                    
                    with col2:
                        if st.button(f"❌ Cancel", key=f"cancel_{trade['id']}"):
                            st.session_state[edit_key] = False
                            st.rerun()
    else:
        st.info("No trades recorded for today. Add trades using the form above or import from a trade log.")
    
    # Save market observations
    if st.button("💾 Save Market Observations", type="secondary"):
        current_entry['trade_day']['market_observations'] = market_observations
        
        if st.session_state.get('github_connected', False):
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Market observations saved!")
            else:
                save_local_data(data)
                st.success("💾 Market observations saved locally!")
        else:
            save_local_data(data)
            st.success("💾 Market observations saved locally!")

# ======== MORNING PREP PAGE ========
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
        st.subheader("Physical & Mental State")
        
        sleep_quality = st.slider(
            "Sleep Quality (1-10)",
            min_value=1,
            max_value=10,
            value=current_entry['morning'].get('sleep_quality', 7)
        )
        
        emotional_state = st.selectbox(
            "Emotional State",
            ["Excited", "Calm", "Focused", "Anxious", "Tired", "Stressed", "Confident"],
            index=["Excited", "Calm", "Focused", "Anxious", "Tired", "Stressed", "Confident"].index(
                current_entry['morning'].get('emotional_state', "Calm")
            )
        )
        
        post_night_shift = st.checkbox(
            "Did you work a night shift?",
            value=current_entry['morning'].get('post_night_shift', False)
        )
        
        st.subheader("Market Preparation")
        
        checked_news = st.checkbox(
            "Checked financial news/events",
            value=current_entry['morning'].get('checked_news', False)
        )
        
        market_news = st.text_area(
            "Key market news/events",
            value=current_entry['morning'].get('market_news', ""),
            height=100,
            placeholder="Economic reports, earnings, geopolitical events..."
        )
    
    with col2:
        st.subheader("Trading Mindset")
        
        triggers_present = st.multiselect(
            "Emotional triggers present today?",
            ["None", "Financial stress", "Family issues", "Work stress", "Health concerns", "FOMO", "Revenge trading urge"],
            default=current_entry['morning'].get('triggers_present', ["None"])
        )
        
        grateful_for = st.text_area(
            "Three things you're grateful for today",
            value=current_entry['morning'].get('grateful_for', ""),
            height=100,
            placeholder="1. \n2. \n3. "
        )
        
        daily_goal = st.text_area(
            "Trading goal for today",
            value=current_entry['morning'].get('daily_goal', ""),
            height=100,
            placeholder="Specific, measurable goal for today's trading"
        )
        
        trading_process = st.text_area(
            "Trading process reminders",
            value=current_entry['morning'].get('trading_process', ""),
            height=100,
            placeholder="Key rules and process points to remember"
        )
    
    # Rules Section
    st.markdown("---")
    st.subheader("📋 Today's Trading Rules")
    st.write("Set up your trading rules for today. These will be checked during your trading review.")
    
    # Initialize rules if not present
    if 'rules' not in current_entry:
        current_entry['rules'] = ["", "", "", "", ""]
    
    # Ensure we have at least 5 rule slots
    while len(current_entry['rules']) < 5:
        current_entry['rules'].append("")
    
    # Rule input boxes
    for i in range(5):
        rule_value = st.text_input(
            f"Rule {i+1}",
            value=current_entry['rules'][i],
            key=f"rule_{i}",
            placeholder=f"Enter trading rule {i+1}..."
        )
        current_entry['rules'][i] = rule_value
    
    # Screenshot upload section
    st.markdown("---")
    st.subheader("📷 Morning Screenshots")
    
    # Display existing screenshots
    existing_screenshots = current_entry['morning'].get('morning_screenshots', [])
    if existing_screenshots:
        for i, screenshot_data in enumerate(existing_screenshots):
            if screenshot_data:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if isinstance(screenshot_data, dict):
                        screenshot_url = screenshot_data.get('url', '')
                        screenshot_caption = screenshot_data.get('caption', f"Morning Screenshot {i+1}")
                    else:
                        screenshot_url = screenshot_data
                        screenshot_caption = f"Morning Screenshot {i+1}"
                    
                    if screenshot_url:
                        st.write(f"*{screenshot_caption}*")
                        display_image_full_size(screenshot_url, screenshot_caption)
                
                with col2:
                    if st.button(f"🗑️", key=f"delete_morning_screenshot_{i}", help="Delete this screenshot"):
                        try:
                            current_entry['morning']['morning_screenshots'].pop(i)
                            
                            # Save immediately
                            if st.session_state.get('github_connected', False):
                                st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                            save_local_data(data)
                            st.success("Screenshot deleted!")
                        except Exception as e:
                            st.error(f"Error deleting screenshot: {str(e)}")
                        st.rerun()
    
    # Add new screenshot
    new_screenshot = st.file_uploader(
        "Add Morning Screenshot",
        type=['png', 'jpg', 'jpeg'],
        key="new_morning_screenshot"
    )
    
    screenshot_caption = st.text_input(
        "Screenshot Caption",
        placeholder="Describe what this screenshot shows..."
    )
    
    if st.button("📷 Add Screenshot") and new_screenshot and screenshot_caption.strip():
        # Handle screenshot upload
        screenshot_data = None
        if st.session_state.get('github_connected', False):
            # Upload to GitHub
            file_data = new_screenshot.getvalue()
            timestamp = int(datetime.now().timestamp())
            filename = f"morning_{timestamp}_{new_screenshot.name}"
            screenshot_url = st.session_state.github_storage.upload_screenshot(
                file_data, filename, date_key
            )
            if screenshot_url:
                screenshot_data = {'url': screenshot_url, 'caption': screenshot_caption}
        else:
            # Save locally
            screenshot_path = save_uploaded_file_local(new_screenshot, date_key, "morning")
            if screenshot_path:
                screenshot_data = {'url': screenshot_path, 'caption': screenshot_caption}
        
        if screenshot_data:
            # Add to morning screenshots
            if 'morning_screenshots' not in current_entry['morning']:
                current_entry['morning']['morning_screenshots'] = []
            current_entry['morning']['morning_screenshots'].append(screenshot_data)
            
            # Save
            if st.session_state.get('github_connected', False):
                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                    st.success("✅ Screenshot added and saved!")
                else:
                    save_local_data(data)
                    st.success("💾 Screenshot added and saved locally!")
            else:
                save_local_data(data)
                st.success("💾 Screenshot added and saved locally!")
            
            st.rerun()
    
    # Save morning data
    if st.button("💾 Save Morning Prep", type="primary"):
        current_entry['morning'] = {
            'sleep_quality': sleep_quality,
            'emotional_state': emotional_state,
            'post_night_shift': post_night_shift,
            'checked_news': checked_news,
            'market_news': market_news,
            'triggers_present': triggers_present,
            'grateful_for': grateful_for,
            'daily_goal': daily_goal,
            'trading_process': trading_process,
            'morning_screenshots': current_entry['morning'].get('morning_screenshots', [])
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

# ======== ENHANCED TRADING REVIEW PAGE ========
elif page == "📈 Trading Review":
    st.markdown('<div class="section-header">📈 Post-Trading Review</div>', unsafe_allow_html=True)
    
    # Show current date and delete option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📅 {selected_date.strftime('%A, %B %d, %Y')}")
    with col2:
        if st.button("🗑️ Delete Entry", key="delete_trading", help="Delete all trading data for this date"):
            if 'trading' in current_entry:
                del current_entry['trading']
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                save_local_data(data)
                st.success("Trading review deleted!")
                st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance Metrics")
        
        # P&L Input with commission support
        st.markdown("**💰 Profit & Loss**")
        
        # Check if synced from Trade Day
        is_trade_day_sync = current_entry['trading'].get('trade_day_sync', False)
        is_trade_log_sync = current_entry['trading'].get('trade_log_sync', False)
        
        if is_trade_day_sync:
            gross_pnl = current_entry['trading'].get('gross_pnl', 0)
            saved_commissions = current_entry['trading'].get('commissions', 0)
            synced_net_pnl = current_entry['trading'].get('pnl', 0)
            st.info(f"🔄 P&L synced from Trade Day: Gross ${gross_pnl:.2f} - Commissions ${saved_commissions:.2f} = Net ${synced_net_pnl:.2f}")
        elif is_trade_log_sync:
            gross_pnl = current_entry['trading'].get('gross_pnl', 0)
            saved_commissions = current_entry['trading'].get('commissions', 0)
            synced_net_pnl = current_entry['trading'].get('pnl', 0)
            st.info(f"🔄 P&L synced from Trade Log: Gross ${gross_pnl:.2f} - Commissions ${saved_commissions:.2f} = Net ${synced_net_pnl:.2f}")
        
        # Manual P&L entry options
        pnl_entry_method = st.radio(
            "P&L Entry Method",
            options=["Manual Net P&L", "Gross P&L + Commissions"],
            index=1 if (is_trade_day_sync or is_trade_log_sync) else 0,
            help="Choose how to enter your P&L data"
        )
        
        if pnl_entry_method == "Manual Net P&L":
            # Simple net P&L entry
            pnl = st.number_input(
                "Net P&L for the Day ($)",
                value=current_entry['trading'].get('pnl', 0.0),
                format="%.2f",
                help="Enter your final net P&L after all costs"
            )
            gross_pnl_calc = pnl
            commission_cost = 0.0
        else:
            # Gross P&L + Commissions entry
            col_a, col_b = st.columns(2)
            
            with col_a:
                gross_pnl_calc = st.number_input(
                    "Gross P&L ($)",
                    value=current_entry['trading'].get('gross_pnl', 0.0),
                    format="%.2f",
                    help="P&L before commissions and fees"
                )
            
            with col_b:
                commission_cost = st.number_input(
                    "Total Commissions ($)",
                    min_value=0.0,
                    value=current_entry['trading'].get('commissions', 0.0),
                    step=0.01,
                    format="%.2f",
                    help="Total commission costs for the session"
                )
            
            # Calculate net P&L
            pnl = gross_pnl_calc - commission_cost
            
            # Display calculation
            st.markdown(f"**Net P&L:** ${pnl:.2f} (${gross_pnl_calc:.2f} - ${commission_cost:.2f})")
        
        st.markdown("---")
        
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
            height=100,
            placeholder="Explain your process grade reasoning..."
        )
        
        general_comments = st.text_area(
            "General Comments About Your Trading",
            value=current_entry['trading'].get('general_comments', ""),
            height=120,
            placeholder="Overall thoughts about today's trading..."
        )
        
        # Trading Screenshots Section
        st.subheader("📷 Trading Screenshots")
        
        # Display existing screenshots
        existing_screenshots = current_entry['trading'].get('trading_screenshots', [])
        if existing_screenshots:
            for i, screenshot_data in enumerate(existing_screenshots):
                if screenshot_data:
                    col_img, col_del = st.columns([4, 1])
                    with col_img:
                        if isinstance(screenshot_data, dict):
                            screenshot_url = screenshot_data.get('url', '')
                            screenshot_caption = screenshot_data.get('caption', f"Trading Screenshot {i+1}")
                        else:
                            screenshot_url = screenshot_data
                            screenshot_caption = f"Trading Screenshot {i+1}"
                        
                        if screenshot_url:
                            st.write(f"*{screenshot_caption}*")
                            display_image_full_size(screenshot_url, screenshot_caption)
                    
                    with col_del:
                        if st.button(f"🗑️", key=f"delete_trading_screenshot_{i}", help="Delete this screenshot"):
                            try:
                                current_entry['trading']['trading_screenshots'].pop(i)
                                
                                # Save immediately
                                if st.session_state.get('github_connected', False):
                                    st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                                save_local_data(data)
                                st.success("Screenshot deleted!")
                            except Exception as e:
                                st.error(f"Error deleting screenshot: {str(e)}")
                            st.rerun()
        
        # Add new screenshot
        new_screenshot = st.file_uploader(
            "Add Trading Screenshot",
            type=['png', 'jpg', 'jpeg'],
            key="new_trading_screenshot"
        )
        
        screenshot_notes = st.text_input(
            "Screenshot Notes",
            value=current_entry['trading'].get('screenshot_notes', ""),
            placeholder="Describe what this screenshot shows..."
        )
        
        if st.button("📷 Add Screenshot") and new_screenshot and screenshot_notes.strip():
            # Handle screenshot upload
            screenshot_data = None
            if st.session_state.get('github_connected', False):
                # Upload to GitHub
                file_data = new_screenshot.getvalue()
                timestamp = int(datetime.now().timestamp())
                filename = f"trading_{timestamp}_{new_screenshot.name}"
                screenshot_url = st.session_state.github_storage.upload_screenshot(
                    file_data, filename, date_key
                )
                if screenshot_url:
                    screenshot_data = {'url': screenshot_url, 'caption': screenshot_notes}
            else:
                # Save locally
                screenshot_path = save_uploaded_file_local(new_screenshot, date_key, "trading")
                if screenshot_path:
                    screenshot_data = {'url': screenshot_path, 'caption': screenshot_notes}
            
            if screenshot_data:
                # Add to trading screenshots
                if 'trading_screenshots' not in current_entry['trading']:
                    current_entry['trading']['trading_screenshots'] = []
                current_entry['trading']['trading_screenshots'].append(screenshot_data)
                
                # Save
                if st.session_state.get('github_connected', False):
                    if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                        st.success("✅ Screenshot added and saved!")
                    else:
                        save_local_data(data)
                        st.success("💾 Screenshot added and saved locally!")
                else:
                    save_local_data(data)
                    st.success("💾 Screenshot added and saved locally!")
                
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
    
    # Show Trade Day sync status if available
    trade_day_trades = current_entry.get('trade_day', {}).get('trades', [])
    if trade_day_trades:
        st.markdown("---")
        st.subheader("📊 Trade Day Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Trades Recorded", len(trade_day_trades))
        with col2:
            win_trades = [t for t in trade_day_trades if t.get('outcome') == 'win']
            loss_trades = [t for t in trade_day_trades if t.get('outcome') == 'loss']
            if win_trades or loss_trades:
                win_rate = len(win_trades) / (len(win_trades) + len(loss_trades)) * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            if st.button("🔄 Update P&L from Trade Day"):
                trade_stats = current_entry.get('trade_day', {}).get('trade_statistics', {})
                if trade_stats:
                    # Get P&L data from trade day
                    trade_day_gross = trade_stats.get('gross_pnl', 0)
                    trade_day_commission = trade_stats.get('commissions', 0)
                    trade_day_net = trade_day_gross - trade_day_commission
                    
                    # Update trading review
                    current_entry['trading']['pnl'] = trade_day_net
                    current_entry['trading']['gross_pnl'] = trade_day_gross
                    current_entry['trading']['commissions'] = trade_day_commission
                    current_entry['trading']['trade_day_sync'] = True
                    
                    # Save
                    if st.session_state.get('github_connected', False):
                        if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                            st.success(f"✅ P&L updated from Trade Day: ${trade_day_net:.2f}")
                        else:
                            save_local_data(data)
                            st.success(f"💾 P&L updated locally: ${trade_day_net:.2f}")
                    else:
                        save_local_data(data)
                        st.success(f"💾 P&L updated locally: ${trade_day_net:.2f}")
                    
                    st.rerun()
                else:
                    st.warning("No trade statistics found in Trade Day. Upload and process a trade log first.")
    
    # Save trading data
    if st.button("💾 Save Trading Review", type="primary"):
        current_entry['trading'] = {
            'pnl': pnl,
            'gross_pnl': gross_pnl_calc,
            'commissions': commission_cost,
            'process_grade': process_grade,
            'grade_reasoning': grade_reasoning,
            'general_comments': general_comments,
            'screenshot_notes': screenshot_notes,
            'rule_compliance': rule_compliance,
            'what_could_improve': what_could_improve,
            'tomorrow_focus': tomorrow_focus,
            'trading_screenshots': current_entry['trading'].get('trading_screenshots', [])  # Keep existing screenshots
        }
        
        # Preserve sync data if it exists
        if current_entry['trading'].get('trade_day_sync', False):
            current_entry['trading']['trade_day_sync'] = True
        if current_entry['trading'].get('trade_log_sync', False):
            current_entry['trading']['trade_log_sync'] = True
        
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
                win_rate = (profitable_days / total_trading_days * 100) if total_trading_days > 0 else 0
                st.metric("Win Rate", f"{win_rate:.1f}%")
            
            with col3:
                avg_daily_pnl = total_pnl / total_trading_days if total_trading_days > 0 else 0
                st.metric("Avg Daily P&L", f"${avg_daily_pnl:.2f}")
            
            with col4:
                process_rate = (process_compliance_days / total_trading_days * 100) if total_trading_days > 0 else 0
                st.metric("Good Process Days", f"{process_rate:.1f}%")
            
            # P&L Chart
            if daily_pnls:
                st.subheader("📈 Daily P&L Chart")
                
                # Create DataFrame for plotting
                dates = []
                current_date = start_date
                pnl_index = 0
                
                chart_data = []
                for date_key, entry in filtered_data.items():
                    if 'trading' in entry and 'pnl' in entry['trading']:
                        chart_data.append({
                            'Date': datetime.strptime(date_key, "%Y-%m-%d").date(),
                            'P&L': entry['trading']['pnl'],
                            'Cumulative': sum(daily_pnls[:pnl_index+1])
                        })
                        pnl_index += 1
                
                df_chart = pd.DataFrame(chart_data)
                
                # Create dual-axis chart
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Daily P&L bars
                fig.add_trace(
                    go.Bar(
                        x=df_chart['Date'],
                        y=df_chart['P&L'],
                        name="Daily P&L",
                        marker_color=['green' if x > 0 else 'red' for x in df_chart['P&L']]
                    ),
                    secondary_y=False,
                )
                
                # Cumulative P&L line
                fig.add_trace(
                    go.Scatter(
                        x=df_chart['Date'],
                        y=df_chart['Cumulative'],
                        mode='lines+markers',
                        name="Cumulative P&L",
                        line=dict(color='#64ffda', width=3)
                    ),
                    secondary_y=True,
                )
                
                fig.update_layout(
                    title="Daily and Cumulative P&L",
                    template="plotly_dark",
                    height=500
                )
                
                fig.update_yaxes(title_text="Daily P&L ($)", secondary_y=False)
                fig.update_yaxes(title_text="Cumulative P&L ($)", secondary_y=True)
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Trade statistics if available
            trade_stats = get_trade_statistics(data)
            if trade_stats.get('total_trades', 0) > 0:
                st.subheader("🎯 Trade Analysis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Trades", trade_stats['total_trades'])
                    st.metric("Win Trades", trade_stats['win_trades'])
                
                with col2:
                    st.metric("Loss Trades", trade_stats['loss_trades'])
                    st.metric("Win Rate", f"{trade_stats['win_rate']:.1f}%")
                
                with col3:
                    st.metric("Break Even", trade_stats['break_even_trades'])
                    st.metric("Pending", trade_stats['pending_trades'])
                
                # Tag analysis
                if trade_stats.get('tag_win_rates'):
                    st.subheader("🏷️ Tag Performance")
                    
                    tag_data = []
                    for tag, win_rate in trade_stats['tag_win_rates'].items():
                        counts = trade_stats['tag_counts'][tag]
                        tag_data.append({
                            'Tag': tag,
                            'Win Rate': win_rate,
                            'Total Trades': counts['total'],
                            'Wins': counts['wins'],
                            'Losses': counts['losses']
                        })
                    
                    df_tags = pd.DataFrame(tag_data)
                    st.dataframe(df_tags, use_container_width=True)
        else:
            st.warning("No trading data found for the selected date range.")

# ======== TAG MANAGEMENT PAGE ========
elif page == "🏷️ Tag Management":
    st.markdown('<div class="section-header">🏷️ Tag Management</div>', unsafe_allow_html=True)
    
    # Get all tags
    all_tags = get_all_tags(data)
    
    if all_tags:
        st.subheader("📋 Current Tags")
        
        # Display tags in a grid
        cols = st.columns(4)
        for i, tag in enumerate(all_tags):
            col_index = i % 4
            with cols[col_index]:
                st.markdown(f'<span class="tag-chip">{tag}</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Tag statistics
        trade_stats = get_trade_statistics(data)
        if trade_stats.get('tag_counts'):
            st.subheader("📊 Tag Usage Statistics")
            
            tag_usage_data = []
            for tag, counts in trade_stats['tag_counts'].items():
                win_rate = trade_stats['tag_win_rates'].get(tag, 0)
                tag_usage_data.append({
                    'Tag': tag,
                    'Total Uses': counts['total'],
                    'Wins': counts['wins'],
                    'Losses': counts['losses'],
                    'Win Rate (%)': f"{win_rate:.1f}%"
                })
            
            df_tag_usage = pd.DataFrame(tag_usage_data)
            df_tag_usage = df_tag_usage.sort_values('Total Uses', ascending=False)
            st.dataframe(df_tag_usage, use_container_width=True)
        
        st.markdown("---")
        
        # Delete tags section
        st.subheader("🗑️ Delete Tags")
        st.warning("⚠️ Deleting tags will remove them from all trades. This action cannot be undone.")
        
        tags_to_delete = st.multiselect(
            "Select tags to delete",
            options=all_tags,
            help="Choose tags you want to remove from the system"
        )
        
        if tags_to_delete and st.button("🗑️ Delete Selected Tags", type="secondary"):
            # Remove tags from system
            for tag in tags_to_delete:
                if tag in data.get('tags', []):
                    data['tags'].remove(tag)
            
            # Remove tags from all trades
            for date_key, entry in data.items():
                if date_key != 'tags' and 'trade_day' in entry:
                    trades = entry['trade_day'].get('trades', [])
                    for trade in trades:
                        if 'tags' in trade:
                            trade['tags'] = [t for t in trade['tags'] if t not in tags_to_delete]
            
            # Save changes
            if st.session_state.get('github_connected', False):
                if st.session_state.github_storage.save_journal_entry("tag_management", {}, data):
                    st.success(f"✅ Deleted {len(tags_to_delete)} tags and updated all trades!")
                else:
                    save_local_data(data)
                    st.success(f"💾 Deleted {len(tags_to_delete)} tags locally!")
            else:
                save_local_data(data)
                st.success(f"💾 Deleted {len(tags_to_delete)} tags locally!")
            
            st.rerun()
    
    # Add new tags section
    st.subheader("➕ Add New Tags")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_tags_input = st.text_input(
            "Add new tags (comma-separated)",
            placeholder="scalp, breakout, news-driven, patience",
            help="Enter multiple tags separated by commas"
        )
    
    with col2:
        if st.button("➕ Add Tags", type="primary"):
            if new_tags_input.strip():
                new_tags = [tag.strip() for tag in new_tags_input.split(',') if tag.strip()]
                
                added_count = 0
                for tag in new_tags:
                    data = add_tag_to_system(data, tag)
                    added_count += 1
                
                # Save changes
                if st.session_state.get('github_connected', False):
                    if st.session_state.github_storage.save_journal_entry("tag_management", {}, data):
                        st.success(f"✅ Added {added_count} new tags!")
                    else:
                        save_local_data(data)
                        st.success(f"💾 Added {added_count} new tags locally!")
                else:
                    save_local_data(data)
                    st.success(f"💾 Added {added_count} new tags locally!")
                
                st.rerun()
            else:
                st.warning("Please enter at least one tag.")
    
    if not all_tags:
        st.info("No tags created yet. Add some tags above to get started with trade categorization.")
