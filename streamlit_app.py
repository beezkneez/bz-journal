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

def get_point_value(symbol):
    """Get point value for P&L calculation"""
    if 'ENQU25' in symbol:
        return 20.0
    elif 'mNQU25' in symbol or 'MNQU25' in symbol:
        return 2.0
    else:
        return 1.0

def group_fills_into_trades(trades_data):
    """Group individual fills into complete trades based on position changes"""
    if not trades_data:
        return []
    
    # Group by symbol first
    symbol_groups = {}
    for fill in trades_data:
        symbol = fill.get('Symbol', 'Unknown')
        if symbol not in symbol_groups:
            symbol_groups[symbol] = []
        symbol_groups[symbol].append(fill)
    
    individual_trades = []
    
    for symbol, fills in symbol_groups.items():
        # Sort fills by time
        fills.sort(key=lambda x: x.get('DateTime', ''))
        
        trade_fills = []
        
        for fill in fills:
            position_qty = float(fill.get('PositionQuantity', 0)) if fill.get('PositionQuantity') else 0
            open_close = fill.get('OpenClose', '')
            
            trade_fills.append(fill)
            
            # Check if this completes a trade (position returns to 0)
            if position_qty == 0 and len(trade_fills) > 1:
                # Trade completed - position back to zero
                trade_summary = create_trade_summary_from_fills(trade_fills, symbol)
                if trade_summary:
                    individual_trades.append(trade_summary)
                trade_fills = []
            elif len(trade_fills) == 1 and open_close == 'Open':
                # Starting a new trade
                pass
    
    return individual_trades

def create_trade_summary_from_fills(fills, symbol):
    """Create a trade summary from a group of fills"""
    if not fills:
        return None
    
    # Calculate trade details
    entry_fills = [f for f in fills if f.get('OpenClose') == 'Open']
    exit_fills = [f for f in fills if f.get('OpenClose') == 'Close']
    
    if not entry_fills or not exit_fills:
        return None
    
    # Get entry and exit info
    entry_time = entry_fills[0].get('DateTime', '')
    exit_time = exit_fills[-1].get('DateTime', '')
    
    # Calculate quantity and average prices
    total_quantity = sum(float(f.get('Quantity', 0)) for f in entry_fills)
    
    # Calculate weighted average entry price
    total_entry_value = sum(float(f.get('Quantity', 0)) * float(f.get('FillPrice', 0)) for f in entry_fills)
    entry_avg_price = total_entry_value / total_quantity if total_quantity > 0 else 0
    
    # Calculate weighted average exit price
    total_exit_quantity = sum(float(f.get('Quantity', 0)) for f in exit_fills)
    total_exit_value = sum(float(f.get('Quantity', 0)) * float(f.get('FillPrice', 0)) for f in exit_fills)
    exit_avg_price = total_exit_value / total_exit_quantity if total_exit_quantity > 0 else 0
    
    # Determine direction
    direction = "Long" if entry_fills and entry_fills[0].get('BuySell') == 'Buy' else "Short"
    
    # Calculate P&L
    pnl = 0
    if entry_avg_price and exit_avg_price and total_quantity:
        point_value = get_point_value(symbol)
        if direction == "Long":
            pnl = (exit_avg_price - entry_avg_price) * total_quantity * point_value
        else:
            pnl = (entry_avg_price - exit_avg_price) * total_quantity * point_value
    
    # Determine outcome
    outcome = "win" if pnl > 0 else "loss" if pnl < 0 else "pending"
    
    # Create description
    description = f"{direction} {total_quantity} {symbol} @ {entry_avg_price:.2f}"
    if exit_avg_price:
        description += f" → {exit_avg_price:.2f}"
    if pnl != 0:
        description += f" (P&L: ${pnl:.2f})"
    
    # Add timing info
    if entry_time and exit_time:
        entry_time_only = entry_time.split(' ')[1] if ' ' in entry_time else entry_time
        exit_time_only = exit_time.split(' ')[1] if ' ' in exit_time else exit_time
        description += f" | {entry_time_only} - {exit_time_only}"
    
    return {
        'id': str(uuid.uuid4()),
        'timestamp': entry_time,
        'description': description,
        'tags': [],  # Will be filled by user
        'outcome': outcome,
        'screenshot': None,  # Will be added by user
        'raw_fills': fills,  # Keep original data for reference
        'symbol': symbol,
        'direction': direction,
        'quantity': total_quantity,
        'entry_price': entry_avg_price,
        'exit_price': exit_avg_price,
        'pnl': pnl
    }

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
    """Get all deposits and withdrawals"""
    return data.get('transactions', [])

def add_transaction(data, transaction_date, transaction_type, amount, description=""):
    """Add a deposit or withdrawal transaction"""
    if 'transactions' not in data:
        data['transactions'] = []
    
    transaction = {
        'date': transaction_date.strftime("%Y-%m-%d") if isinstance(transaction_date, date) else transaction_date,
        'type': transaction_type,  # 'deposit' or 'withdrawal'
        'amount': float(amount),
        'description': description,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data['transactions'].append(transaction)
    
    # Sort transactions by date
    data['transactions'].sort(key=lambda x: x['date'])
    
    return data

def delete_transaction(data, transaction_index):
    """Delete a transaction by index"""
    if 'transactions' in data and 0 <= transaction_index < len(data['transactions']):
        data['transactions'].pop(transaction_index)
    return data

def get_transactions_for_date(data, target_date):
    """Get all transactions for a specific date"""
    if isinstance(target_date, date):
        target_date = target_date.strftime("%Y-%m-%d")
    
    transactions = data.get('transactions', [])
    return [t for t in transactions if t['date'] == target_date]

def calculate_total_deposits(data, up_to_date=None):
    """Calculate total deposits up to a specific date"""
    transactions = data.get('transactions', [])
    total = 0
    
    for transaction in transactions:
        transaction_date = transaction['date']
        if up_to_date and transaction_date > up_to_date.strftime("%Y-%m-%d"):
            continue
        if transaction['type'] == 'deposit':
            total += transaction['amount']
    
    return total

def calculate_total_withdrawals(data, up_to_date=None):
    """Calculate total withdrawals up to a specific date"""
    transactions = data.get('transactions', [])
    total = 0
    
    for transaction in transactions:
        transaction_date = transaction['date']
        if up_to_date and transaction_date > up_to_date.strftime("%Y-%m-%d"):
            continue
        if transaction['type'] == 'withdrawal':
            total += transaction['amount']
    
    return total

# Initialize session state - CALENDAR VIEW FIRST!
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
        
        # Show transaction summary
        total_deposits = calculate_total_deposits(data, st.session_state.current_date)
        total_withdrawals = calculate_total_withdrawals(data, st.session_state.current_date)
        
        st.write(f"**Total Deposits:** ${total_deposits:,.2f}")
        st.write(f"**Total Withdrawals:** ${total_withdrawals:,.2f}")
        
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
        starting_balance = account_settings['starting_balance']
        start_date_str = account_settings['start_date']
        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        
        # Add Transaction Ledger at the top
        st.subheader("💳 Transaction Ledger")
        
        # Quick add transaction form
        col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 2, 1])
        
        with col1:
            ledger_transaction_type = st.selectbox(
                "Type",
                ["deposit", "withdrawal"],
                format_func=lambda x: "💰 Deposit" if x == "deposit" else "💸 Withdrawal",
                key="ledger_type"
            )
        
        with col2:
            ledger_transaction_amount = st.number_input(
                "Amount ($)",
                min_value=0.01,
                step=50.0,
                format="%.2f",
                key="ledger_amount"
            )
        
        with col3:
            ledger_transaction_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today(),
                key="ledger_date"
            )
        
        with col4:
            ledger_transaction_description = st.text_input(
                "Description",
                placeholder="e.g., Monthly deposit, Profit withdrawal...",
                key="ledger_description"
            )
        
        with col5:
            st.markdown("<br>", unsafe_allow_html=True)  # Add space for alignment
            if st.button("💾 Add", type="primary", key="ledger_add"):
                if ledger_transaction_amount > 0:
                    data = add_transaction(data, ledger_transaction_date, ledger_transaction_type, ledger_transaction_amount, ledger_transaction_description)
                    
                    # Save to storage
                    if st.session_state.get('github_connected', False):
                        st.session_state.github_storage.save_journal_entry("transactions", {}, data)
                    save_local_data(data)
                    
                    transaction_verb = "deposited" if ledger_transaction_type == "deposit" else "withdrawn"
                    st.success(f"${ledger_transaction_amount:.2f} {transaction_verb}! Balance updated.")
                    st.rerun()
                else:
                    st.error("Amount must be greater than 0")
        
        # Recent transactions summary
        all_transactions = get_all_transactions(data)
        if all_transactions:
            st.markdown("---")
            st.subheader("📋 Recent Transactions")
            
            # Show last 5 transactions
            recent_transactions = list(reversed(all_transactions[-5:]))
            
            for transaction in recent_transactions:
                type_icon = "💰" if transaction['type'] == 'deposit' else "💸"
                type_color = "green" if transaction['type'] == 'deposit' else "red"
                amount_display = f"+${transaction['amount']:,.2f}" if transaction['type'] == 'deposit' else f"-${transaction['amount']:,.2f}"
                desc = f" - {transaction['description']}" if transaction.get('description') else ""
                
                st.markdown(f"""
                <div style="background: rgba(0,20,40,0.3); padding: 0.5rem; margin: 0.2rem 0; border-radius: 5px; border-left: 3px solid {type_color};">
                    <strong>{transaction['date']}</strong> | {type_icon} <span style="color: {type_color};">{amount_display}</span>{desc}
                </div>
                """, unsafe_allow_html=True)
            
            if len(all_transactions) > 5:
                st.info(f"Showing 5 most recent transactions. Total: {len(all_transactions)} transactions.")
        
        st.markdown("---")
        
        # Date range for analysis
        st.subheader("📊 Balance History Analysis")
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
        
        # Calculate daily balances including transactions
        balance_data = []
        current_date = analysis_start
        running_balance = calculate_running_balance(data, analysis_start, starting_balance, start_date_obj)
        
        while current_date <= analysis_end:
            date_key = get_date_key(current_date)
            daily_pnl = 0
            daily_deposits = 0
            daily_withdrawals = 0
            
            # Get trading P&L
            if date_key in data and 'trading' in data[date_key]:
                daily_pnl = data[date_key]['trading'].get('pnl', 0)
            
            # Get transactions for this date
            day_transactions = get_transactions_for_date(data, current_date)
            for transaction in day_transactions:
                if transaction['type'] == 'deposit':
                    daily_deposits += transaction['amount']
                else:
                    daily_withdrawals += transaction['amount']
            
            balance_data.append({
                'date': current_date,
                'date_str': current_date.strftime("%Y-%m-%d"),
                'balance': running_balance,
                'daily_pnl': daily_pnl,
                'daily_deposits': daily_deposits,
                'daily_withdrawals': daily_withdrawals,
                'net_transactions': daily_deposits - daily_withdrawals,
                'cumulative_pnl': running_balance - starting_balance - calculate_total_deposits(data, current_date) + calculate_total_withdrawals(data, current_date)
            })
            
            # Update running balance for next day
            running_balance += daily_pnl + daily_deposits - daily_withdrawals
            current_date += timedelta(days=1)
        
        # Display summary metrics
        if balance_data:
            latest_balance = balance_data[-1]['balance']
            total_deposits = calculate_total_deposits(data, analysis_end)
            total_withdrawals = calculate_total_withdrawals(data, analysis_end)
            total_pnl = latest_balance - starting_balance - total_deposits + total_withdrawals
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Balance", f"${latest_balance:,.2f}")
            with col2:
                st.metric("Trading P&L", f"${total_pnl:,.2f}", delta=f"{(total_pnl/starting_balance)*100:.2f}%")
            with col3:
                st.metric("Total Deposits", f"${total_deposits:,.2f}")
            with col4:
                st.metric("Total Withdrawals", f"${total_withdrawals:,.2f}")
            
            # Enhanced balance chart with transactions
            fig = go.Figure()
            
            # Balance line
            fig.add_trace(go.Scatter(
                x=[d['date'] for d in balance_data],
                y=[d['balance'] for d in balance_data],
                mode='lines+markers',
                name='Account Balance',
                line=dict(color='#64ffda', width=3),
                marker=dict(size=4),
                hovertemplate='<b>%{x}</b><br>Balance: $%{y:,.2f}<extra></extra>'
            ))
            
            # Add deposit markers
            deposit_dates = [d['date'] for d in balance_data if d['daily_deposits'] > 0]
            deposit_balances = [d['balance'] for d in balance_data if d['daily_deposits'] > 0]
            deposit_amounts = [d['daily_deposits'] for d in balance_data if d['daily_deposits'] > 0]
            
            if deposit_dates:
                fig.add_trace(go.Scatter(
                    x=deposit_dates,
                    y=deposit_balances,
                    mode='markers',
                    name='💰 Deposits',
                    marker=dict(color='green', size=8, symbol='triangle-up'),
                    hovertemplate='<b>%{x}</b><br>Deposit: $%{text}<br>Balance: $%{y:,.2f}<extra></extra>',
                    text=[f"{amt:,.2f}" for amt in deposit_amounts]
                ))
            
            # Add withdrawal markers
            withdrawal_dates = [d['date'] for d in balance_data if d['daily_withdrawals'] > 0]
            withdrawal_balances = [d['balance'] for d in balance_data if d['daily_withdrawals'] > 0]
            withdrawal_amounts = [d['daily_withdrawals'] for d in balance_data if d['daily_withdrawals'] > 0]
            
            if withdrawal_dates:
                fig.add_trace(go.Scatter(
                    x=withdrawal_dates,
                    y=withdrawal_balances,
                    mode='markers',
                    name='💸 Withdrawals',
                    marker=dict(color='red', size=8, symbol='triangle-down'),
                    hovertemplate='<b>%{x}</b><br>Withdrawal: $%{text}<br>Balance: $%{y:,.2f}<extra></extra>',
                    text=[f"{amt:,.2f}" for amt in withdrawal_amounts]
                ))
            
            # Starting balance reference line
            fig.add_hline(
                y=starting_balance,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Starting Balance: ${starting_balance:,.2f}"
            )
            
            fig.update_layout(
                title="Account Balance Over Time (with Transactions)",
                xaxis_title="Date",
                yaxis_title="Balance ($)",
                template="plotly_dark",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Transaction management section
            if all_transactions:
                st.markdown("---")
                st.subheader("🛠️ Manage All Transactions")
                
                # Create DataFrame for display
                df_transactions = []
                for i, transaction in enumerate(reversed(all_transactions)):
                    df_transactions.append({
                        'Date': transaction['date'],
                        'Type': "💰 Deposit" if transaction['type'] == 'deposit' else "💸 Withdrawal",
                        'Amount': f"${transaction['amount']:,.2f}",
                        'Description': transaction.get('description', ''),
                        'Index': len(all_transactions) - 1 - i
                    })
                
                # Display transaction table
                st.dataframe(
                    pd.DataFrame(df_transactions)[['Date', 'Type', 'Amount', 'Description']], 
                    use_container_width=True, 
                    hide_index=True
                )
                
                # Delete transaction functionality
                with st.expander("🗑️ Delete Transaction"):
                    transaction_options = []
                    for i, transaction in enumerate(all_transactions):
                        type_icon = "💰" if transaction['type'] == 'deposit' else "💸"
                        desc = f" - {transaction['description']}" if transaction.get('description') else ""
                        option = f"{transaction['date']} | {type_icon} ${transaction['amount']:,.2f}{desc}"
                        transaction_options.append(option)
                    
                    if transaction_options:
                        selected_transaction = st.selectbox(
                            "Select transaction to delete:",
                            range(len(transaction_options)),
                            format_func=lambda x: transaction_options[x]
                        )
                        
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("🗑️ Delete Selected", key="delete_transaction_balance"):
                                data = delete_transaction(data, selected_transaction)
                                
                                # Save to storage
                                if st.session_state.get('github_connected', False):
                                    st.session_state.github_storage.save_journal_entry("transactions", {}, data)
                                save_local_data(data)
                                
                                st.success("Transaction deleted! Balance will update.")
                                st.rerun()
                        
                        with col2:
                            st.warning("⚠️ Deleting a transaction will affect your balance calculations.")
                
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

# ======== ENHANCED TRADE DAY PAGE WITH IMPORT ========
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
        current_entry['trade_day'] = {'market_observations': '', 'trades': []}
    
    # NEW: Trade Log Import Section
    st.subheader("📁 Import Trades from Log")
    
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
    
    with col2:
        if trade_log_file and st.button("🔄 Parse & Import Trades", type="primary"):
            file_content = trade_log_file.read().decode('utf-8')
            fills_data, error = parse_trade_log(file_content)
            
            if error:
                st.error(f"Error parsing file: {error}")
            else:
                # Group fills into individual trades
                individual_trades = group_fills_into_trades(fills_data)
                
                if individual_trades:
                    # Add to session state for bulk editing
                    st.session_state.imported_trades = individual_trades
                    st.success(f"✅ Parsed {len(fills_data)} fills into {len(individual_trades)} individual trades!")
                    st.info("👇 Review and enhance your trades below, then save all at once.")
                    st.rerun()
                else:
                    st.warning("No complete trades found in the log file.")
    
    # NEW: Bulk Edit Imported Trades
    if st.session_state.get('imported_trades'):
        st.markdown("---")
        st.subheader("✏️ Review & Enhance Imported Trades")
        
        imported_trades = st.session_state.imported_trades
        
        # Show summary
        total_pnl = sum(trade.get('pnl', 0) for trade in imported_trades)
        winners = len([t for t in imported_trades if t.get('pnl', 0) > 0])
        losers = len([t for t in imported_trades if t.get('pnl', 0) < 0])
        
        st.markdown(f"""
        <div class="import-summary">
            <h4>📊 Import Summary</h4>
            <strong>Total Trades:</strong> {len(imported_trades)} | 
            <strong>Total P&L:</strong> ${total_pnl:.2f} | 
            <strong>Winners:</strong> {winners} | 
            <strong>Losers:</strong> {losers}
        </div>
        """, unsafe_allow_html=True)
        
        # Bulk actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Bulk tag application
            all_tags = get_all_tags(data)
            bulk_tags = st.multiselect(
                "Apply tags to all trades",
                options=all_tags,
                key="bulk_tags_select"
            )
            
            bulk_new_tags = st.text_input(
                "New tags for all (comma-separated)",
                placeholder="session-tag, market-condition",
                key="bulk_new_tags"
            )
        
        with col2:
            if st.button("🏷️ Apply Bulk Tags"):
                new_tags = []
                if bulk_new_tags.strip():
                    new_tags = [tag.strip() for tag in bulk_new_tags.split(',') if tag.strip()]
                
                combined_tags = bulk_tags + new_tags
                
                for trade in imported_trades:
                    existing_tags = trade.get('tags', [])
                    trade['tags'] = list(set(existing_tags + combined_tags))
                
                # Add new tags to system
                for tag in new_tags:
                    data = add_tag_to_system(data, tag)
                
                st.success(f"Applied {len(combined_tags)} tags to all trades!")
                st.rerun()
        
        with col3:
            if st.button("💾 Save All Trades to Trade Day", type="primary"):
                # Add all imported trades to current entry
                existing_trades = current_entry['trade_day'].get('trades', [])
                current_entry['trade_day']['trades'] = existing_trades + imported_trades
                
                # Save
                if st.session_state.get('github_connected', False):
                    if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                        st.success("✅ All trades saved to Trade Day!")
                    else:
                        save_local_data(data)
                        st.success("💾 All trades saved locally!")
                else:
                    save_local_data(data)
                    st.success("💾 All trades saved locally!")
                
                # Clear imported trades
                del st.session_state.imported_trades
                st.rerun()
        
        # Individual trade editing
        st.markdown("### 📝 Individual Trade Details")
        
        for i, trade in enumerate(imported_trades):
            with st.expander(f"Trade {i+1}: {trade['description']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Editable description
                    new_description = st.text_area(
                        "Description",
                        value=trade['description'],
                        height=80,
                        key=f"import_desc_{i}"
                    )
                    trade['description'] = new_description
                    
                    # Screenshot upload
                    screenshot_file = st.file_uploader(
                        "Add screenshot",
                        type=['png', 'jpg', 'jpeg'],
                        key=f"import_screenshot_{i}"
                    )
                    
                    if screenshot_file:
                        screenshot_caption = st.text_input(
                            "Screenshot caption",
                            key=f"import_caption_{i}"
                        )
                        
                        if st.button(f"📤 Upload", key=f"upload_import_{i}"):
                            if screenshot_caption.strip():
                                # Handle screenshot upload
                                screenshot_data = None
                                if st.session_state.get('github_connected', False):
                                    file_data = screenshot_file.getvalue()
                                    timestamp = int(datetime.now().timestamp())
                                    filename = f"imported_trade_{timestamp}_{screenshot_file.name}"
                                    screenshot_url = st.session_state.github_storage.upload_screenshot(
                                        file_data, filename, date_key
                                    )
                                    if screenshot_url:
                                        screenshot_data = {'url': screenshot_url, 'caption': screenshot_caption}
                                else:
                                    screenshot_path = save_uploaded_file_local(screenshot_file, date_key, "imported_trade")
                                    if screenshot_path:
                                        screenshot_data = {'url': screenshot_path, 'caption': screenshot_caption}
                                
                                if screenshot_data:
                                    trade['screenshot'] = screenshot_data
                                    st.success("Screenshot added!")
                                    st.rerun()
                
                with col2:
                    # Tags for this specific trade
                    trade_tags = st.multiselect(
                        "Tags",
                        options=all_tags,
                        default=trade.get('tags', []),
                        key=f"import_tags_{i}"
                    )
                    
                    trade_new_tags = st.text_input(
                        "New tags",
                        placeholder="specific, setup-type",
                        key=f"import_new_tags_{i}"
                    )
                    
                    if trade_new_tags.strip():
                        new_tags = [tag.strip() for tag in trade_new_tags.split(',') if tag.strip()]
                        trade_tags.extend(new_tags)
                        for tag in new_tags:
                            data = add_tag_to_system(data, tag)
                    
                    trade['tags'] = list(set(trade_tags))
                    
                    # Outcome adjustment
                    new_outcome = st.selectbox(
                        "Outcome",
                        options=["win", "loss", "pending"],
                        index=["win", "loss", "pending"].index(trade.get('outcome', 'pending')),
                        format_func=lambda x: {"win": "✅ Win", "loss": "❌ Loss", "pending": "⏳ Pending"}[x],
                        key=f"import_outcome_{i}"
                    )
                    trade['outcome'] = new_outcome
                    
                    # Show trade details
                    pnl_color = "green" if trade.get('pnl', 0) > 0 else "red" if trade.get('pnl', 0) < 0 else "gray"
                    st.markdown(f"**P&L:** <span style='color: {pnl_color}; font-weight: bold;'>${trade.get('pnl', 0):.2f}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Symbol:** {trade.get('symbol', 'N/A')}")
                    st.markdown(f"**Direction:** {trade.get('direction', 'N/A')}")
        
        # Cancel import
        if st.button("❌ Cancel Import"):
            del st.session_state.imported_trades
            st.rerun()
    
    # Market Observations Section
    if not st.session_state.get('imported_trades'):  # Only show if not importing
        st.markdown("---")
    
    st.subheader("🔍 Market Observations")
    market_observations = st.text_area(
        "What do you see in the markets today?",
        value=current_entry['trade_day'].get('market_observations', ''),
        height=150,
        placeholder="Market conditions, trends, key levels, news impact, volume patterns, sector rotation, etc.",
        key="market_observations"
    )
    
    # Save market observations
    if st.button("💾 Save Market Observations", key="save_observations"):
        current_entry['trade_day']['market_observations'] = market_observations
        
        if st.session_state.get('github_connected', False):
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Market observations saved!")
        else:
            save_local_data(data)
            st.success("💾 Market observations saved!")
    
    st.markdown("---")
    
    # Add New Trade Section (Manual Entry)
    st.subheader("➕ Add New Trade (Manual Entry)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Trade description
        trade_description = st.text_area(
            "Trade Description",
            placeholder="Describe your trade setup, entry reasoning, target, stop loss, etc.",
            height=100,
            key="new_trade_description"
        )
        
        # Screenshot upload for trade
        trade_screenshot = st.file_uploader(
            "Trade Screenshot",
            type=['png', 'jpg', 'jpeg'],
            help="Upload entry chart, setup screenshot, or other relevant image",
            key="new_trade_screenshot"
        )
        
        screenshot_caption = ""
        if trade_screenshot:
            screenshot_caption = st.text_input(
                "Screenshot Caption",
                placeholder="Describe this screenshot...",
                key="new_trade_screenshot_caption"
            )
    
    with col2:
        # Tags section
        st.markdown("**Tags:**")
        
        # Get existing tags
        all_tags = get_all_tags(data)
        
        # Multi-select for existing tags
        selected_tags = st.multiselect(
            "Select existing tags",
            options=all_tags,
            key="trade_tags_select"
        )
        
        # Add new tags
        new_tags_input = st.text_input(
            "Add new tags (comma-separated)",
            placeholder="scalp, breakout, TSLA",
            key="new_tags_input"
        )
        
        # Parse new tags
        new_tags = []
        if new_tags_input.strip():
            new_tags = [tag.strip() for tag in new_tags_input.split(',') if tag.strip()]
            
        # Combine all tags
        all_trade_tags = selected_tags + new_tags
        
        # Trade outcome
        trade_outcome = st.selectbox(
            "Trade Outcome",
            options=["pending", "win", "loss"],
            format_func=lambda x: {
                "pending": "⏳ Pending", 
                "win": "✅ Win", 
                "loss": "❌ Loss"
            }[x],
            key="trade_outcome"
        )
    
    # Add trade button
    if st.button("🚀 Add Trade", type="primary", key="add_trade"):
        if not trade_description.strip():
            st.warning("⚠️ Please add a trade description!")
        else:
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
                        
                        # Quick outcome update (kept for convenience)
                        new_outcome = st.selectbox(
                            "Quick Update Outcome",
                            options=["pending", "win", "loss"],
                            index=["pending", "win", "loss"].index(outcome),
                            format_func=lambda x: {"pending": "⏳ Pending", "win": "✅ Win", "loss": "❌ Loss"}[x],
                            key=f"outcome_update_{trade['id']}"
                        )
                        
                        if new_outcome != outcome:
                            if st.button(f"💾 Update", key=f"update_outcome_{trade['id']}"):
                                trade['outcome'] = new_outcome
                                
                                # Save updated trade
                                if st.session_state.get('github_connected', False):
                                    st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                                save_local_data(data)
                                st.success("Trade outcome updated!")
                                st.rerun()
                        
                        # Delete trade button
                        if st.button(f"🗑️ Delete", key=f"delete_trade_{trade['id']}"):
                            current_entry['trade_day']['trades'].pop(i)
                            
                            if st.session_state.get('github_connected', False):
                                st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                            save_local_data(data)
                            st.success("Trade deleted!")
                            st.rerun()
                
                else:
                    # Edit mode
                    st.markdown("### ✏️ **Edit Trade**")
                    
                    with st.form(key=f"edit_trade_form_{trade['id']}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            # Editable description
                            edit_description = st.text_area(
                                "Trade Description",
                                value=trade.get('description', ''),
                                height=100,
                                key=f"edit_desc_{trade['id']}"
                            )
                            
                            # Screenshot caption editing (if screenshot exists)
                            edit_screenshot_caption = ""
                            if trade.get('screenshot'):
                                edit_screenshot_caption = st.text_input(
                                    "Screenshot Caption",
                                    value=trade['screenshot'].get('caption', ''),
                                    key=f"edit_caption_{trade['id']}"
                                )
                                
                                # Show current screenshot
                                st.markdown("**Current Screenshot:**")
                                display_image_full_size(trade['screenshot']['url'], trade['screenshot']['caption'])
                        
                        with col2:
                            # Get current tags for editing
                            current_tags = trade.get('tags', [])
                            all_tags = get_all_tags(data)
                            
                            # Multi-select for existing tags (pre-select current tags)
                            edit_selected_tags = st.multiselect(
                                "Select existing tags",
                                options=all_tags,
                                default=current_tags,
                                key=f"edit_tags_select_{trade['id']}"
                            )
                            
                            # Add new tags
                            edit_new_tags_input = st.text_input(
                                "Add new tags (comma-separated)",
                                placeholder="scalp, breakout, TSLA",
                                key=f"edit_new_tags_{trade['id']}"
                            )
                            
                            # Parse new tags
                            edit_new_tags = []
                            if edit_new_tags_input.strip():
                                edit_new_tags = [tag.strip() for tag in edit_new_tags_input.split(',') if tag.strip()]
                            
                            # Combine all tags
                            edit_all_trade_tags = edit_selected_tags + edit_new_tags
                            
                            # Trade outcome
                            edit_trade_outcome = st.selectbox(
                                "Trade Outcome",
                                options=["pending", "win", "loss"],
                                index=["pending", "win", "loss"].index(trade.get('outcome', 'pending')),
                                format_func=lambda x: {
                                    "pending": "⏳ Pending", 
                                    "win": "✅ Win", 
                                    "loss": "❌ Loss"
                                }[x],
                                key=f"edit_outcome_{trade['id']}"
                            )
                        
                        # Form buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            save_changes = st.form_submit_button("💾 Save Changes", type="primary")
                        with col2:
                            cancel_edit = st.form_submit_button("❌ Cancel")
                        
                        if save_changes:
                            if not edit_description.strip():
                                st.error("⚠️ Trade description cannot be empty!")
                            else:
                                # Add new tags to system
                                for tag in edit_new_tags:
                                    data = add_tag_to_system(data, tag)
                                
                                # Update the trade
                                trade['description'] = edit_description
                                trade['tags'] = edit_all_trade_tags
                                trade['outcome'] = edit_trade_outcome
                                
                                # Update screenshot caption if it exists
                                if trade.get('screenshot') and edit_screenshot_caption.strip():
                                    trade['screenshot']['caption'] = edit_screenshot_caption
                                
                                # Save changes
                                try:
                                    if st.session_state.get('github_connected', False):
                                        if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                                            st.success("✅ Trade updated and saved to GitHub!")
                                        else:
                                            save_local_data(data)
                                            st.success("💾 Trade updated and saved locally!")
                                    else:
                                        save_local_data(data)
                                        st.success("💾 Trade updated and saved locally!")
                                    
                                    # Exit edit mode
                                    st.session_state[edit_key] = False
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error saving changes: {str(e)}")
                                    save_local_data(data)
                                    st.warning("⚠️ Saved to local backup")
                        
                        if cancel_edit:
                            # Exit edit mode without saving
                            st.session_state[edit_key] = False
                            st.rerun()
    else:
        st.info("No trades recorded for today. Add your first trade above or import from a trade log!")

# ======== TAG MANAGEMENT PAGE ========
elif page == "🏷️ Tag Management":
    st.markdown('<div class="section-header">🏷️ Tag Management & Statistics</div>', unsafe_allow_html=True)
    
    # Get trade statistics
    trade_stats = get_trade_statistics(data)
    
    if trade_stats:
        # Overall statistics
        st.subheader("📊 Overall Trade Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", trade_stats['total_trades'])
        with col2:
            st.metric("Win Rate", f"{trade_stats['win_rate']:.1f}%")
        with col3:
            st.metric("Wins", trade_stats['win_trades'], delta=None)
        with col4:
            st.metric("Losses", trade_stats['loss_trades'], delta=None)
        
        # Tag statistics table
        st.subheader("🏷️ Tag Performance")
        
        if trade_stats['tag_counts']:
            # Create DataFrame for tag statistics
            tag_data = []
            for tag, counts in trade_stats['tag_counts'].items():
                completed = counts['wins'] + counts['losses']
                win_rate = (counts['wins'] / completed * 100) if completed > 0 else 0
                
                tag_data.append({
                    'Tag': tag,
                    'Total Trades': counts['total'],
                    'Wins': counts['wins'],
                    'Losses': counts['losses'],
                    'Pending': counts['total'] - completed,
                    'Win Rate %': f"{win_rate:.1f}%"
                })
            
            # Sort by total trades
            tag_df = pd.DataFrame(tag_data)
            tag_df = tag_df.sort_values('Total Trades', ascending=False)
            
            st.dataframe(tag_df, use_container_width=True, hide_index=True)
            
            # Tag performance chart
            if len(tag_data) > 0:
                # Filter tags with at least one completed trade for the chart
                chart_data = [t for t in tag_data if t['Wins'] + t['Losses'] > 0]
                
                if chart_data:
                    fig = go.Figure()
                    
                    tags = [t['Tag'] for t in chart_data]
                    win_rates = [float(t['Win Rate %'].replace('%', '')) for t in chart_data]
                    total_trades = [t['Total Trades'] for t in chart_data]
                    
                    # Color bars by win rate
                    colors = ['green' if wr >= 60 else 'orange' if wr >= 40 else 'red' for wr in win_rates]
                    
                    fig.add_trace(go.Bar(
                        x=tags,
                        y=win_rates,
                        marker_color=colors,
                        text=[f"{wr:.1f}%<br>({tt} trades)" for wr, tt in zip(win_rates, total_trades)],
                        textposition='auto',
                        name="Win Rate"
                    ))
                    
                    fig.update_layout(
                        title="Tag Performance by Win Rate",
                        xaxis_title="Tags",
                        yaxis_title="Win Rate (%)",
                        template="plotly_dark",
                        showlegend=False
                    )
                    
                    # Add horizontal line at 50%
                    fig.add_hline(y=50, line_dash="dash", line_color="gray", 
                                 annotation_text="Break-even line")
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        # Recent trades
        st.subheader("📈 Recent Trades")
        recent_trades = trade_stats.get('recent_trades', [])[:5]
        
        for trade in recent_trades:
            outcome_colors = {
                'win': 'green',
                'loss': 'red',
                'pending': 'orange'
            }
            outcome_icons = {
                'win': '✅',
                'loss': '❌',
                'pending': '⏳'
            }
            
            color = outcome_colors.get(trade.get('outcome', 'pending'), 'gray')
            icon = outcome_icons.get(trade.get('outcome', 'pending'), '❓')
            
            # Create tags display
            tags_html = ""
            for tag in trade.get('tags', []):
                tags_html += f'<span class="tag-chip">{tag}</span>'
            
            st.markdown(f"""
            <div class="trade-card">
                <strong>{trade.get('date', 'Unknown Date')} - {trade.get('timestamp', 'Unknown Time').split(' ')[1]}</strong>
                <span style="color: {color}; float: right;">{icon} {trade.get('outcome', 'pending').upper()}</span>
                <br>
                <strong>Description:</strong> {trade.get('description', 'No description')[:100]}{'...' if len(trade.get('description', '')) > 100 else ''}
                <br>
                <strong>Tags:</strong> {tags_html}
            </div>
            """, unsafe_allow_html=True)
    
    # Tag management
    st.markdown("---")
    st.subheader("🛠️ Manage Tags")
    
    all_tags = get_all_tags(data)
    
    if all_tags:
        st.write(f"**Current tags ({len(all_tags)}):**")
        
        # Display all tags with delete option
        for tag in all_tags:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f'<span class="tag-chip">{tag}</span>', unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"delete_tag_{tag}", help=f"Delete tag '{tag}'"):
                    # Remove tag from system
                    data['tags'].remove(tag)
                    
                    # Remove tag from all trades
                    for date_key, entry in data.items():
                        if date_key != 'tags' and 'trade_day' in entry:
                            for trade in entry['trade_day'].get('trades', []):
                                if 'tags' in trade and tag in trade['tags']:
                                    trade['tags'].remove(tag)
                    
                    # Save changes
                    if st.session_state.get('github_connected', False):
                        st.session_state.github_storage.save_journal_entry("tags", {}, data)
                    save_local_data(data)
                    st.success(f"Tag '{tag}' deleted from system!")
                    st.rerun()
    else:
        st.info("No tags created yet. Add tags when creating trades.")
    
    # Add new tags manually
    st.subheader("➕ Add New Tags")
    new_tags_manual = st.text_input(
        "Add tags (comma-separated)",
        placeholder="momentum, reversal, gap-up, earnings-play",
        key="manual_tags_input"
    )
    
    if st.button("💾 Add Tags", key="add_manual_tags"):
        if new_tags_manual.strip():
            tags_to_add = [tag.strip() for tag in new_tags_manual.split(',') if tag.strip()]
            added_count = 0
            
            for tag in tags_to_add:
                if tag not in get_all_tags(data):
                    data = add_tag_to_system(data, tag)
                    added_count += 1
            
            if added_count > 0:
                # Save changes
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry("tags", {}, data)
                save_local_data(data)
                st.success(f"Added {added_count} new tags!")
                st.rerun()
            else:
                st.info("All tags already exist in the system.")

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
        
        # Market News text box
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
        
        # Screenshot upload for morning prep WITH CAPTIONS
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
            height=200
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
            help="Manual entry or can be calculated from Trade Day entries"
        )
        
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
            'trading_screenshots': current_entry['trading'].get('trading_screenshots', [])
        }
        
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
                    
                    # Trade Day Section
                    if 'trade_day' in entry and entry['trade_day']:
                        st.markdown("### 📈 Trade Day")
                        trade_day = entry['trade_day']
                        
                        if 'market_observations' in trade_day and trade_day['market_observations']:
                            st.write(f"**Market Observations:** {trade_day['market_observations']}")
                        
                        # Display trades
                        trades = trade_day.get('trades', [])
                        if trades:
                            st.write(f"**Trades ({len(trades)}):**")
                            for k, trade in enumerate(trades):
                                outcome = trade.get('outcome', 'pending')
                                outcome_colors = {
                                    'win': 'green',
                                    'loss': 'red',
                                    'pending': 'orange'
                                }
                                outcome_icons = {
                                    'win': '✅',
                                    'loss': '❌',
                                    'pending': '⏳'
                                }
                                
                                color = outcome_colors.get(outcome, 'gray')
                                icon = outcome_icons.get(outcome, '❓')
                                
                                # Create tags display
                                tags_html = ""
                                for tag in trade.get('tags', []):
                                    tags_html += f'<span class="tag-chip">{tag}</span>'
                                
                                st.markdown(f"""
                                <div class="trade-card">
                                    <strong>Trade {k+1} - {trade.get('timestamp', 'Unknown Time').split(' ')[1]}</strong>
                                    <span style="color: {color}; float: right;">{icon} {outcome.upper()}</span>
                                    <br>
                                    <strong>Description:</strong> {trade.get('description', 'No description')[:100]}{'...' if len(trade.get('description', '')) > 100 else ''}
                                    <br>
                                    <strong>Tags:</strong> {tags_html}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Display trade screenshot if exists
                                if trade.get('screenshot'):
                                    st.write(f"*{trade['screenshot']['caption']}:*")
                                    display_image_full_size(trade['screenshot']['url'], trade['screenshot']['caption'])
                    
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

# UPDATED SIDEBAR STATS - FIXED RULE COMPLIANCE CALCULATION + PROCESS GRADE TRACKING + TRADE STATS
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

# Process Grade Trend
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

# Display trade stats in sidebar if available
trade_stats = get_trade_statistics(data)
if trade_stats and trade_stats['total_trades'] > 0:
    st.sidebar.markdown("**🏷️ Trade Stats**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Total Trades", trade_stats['total_trades'])
    with col2:
        st.metric("Win Rate", f"{trade_stats['win_rate']:.1f}%")
    
    if trade_stats['recent_trades']:
        latest_outcome = trade_stats['recent_trades'][0].get('outcome', 'pending').upper()
        outcome_emoji = {'WIN': '✅', 'LOSS': '❌', 'PENDING': '⏳'}.get(latest_outcome, '❓')
        st.sidebar.write(f"**Latest:** {outcome_emoji} {latest_outcome}")

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

# GitHub status at the very bottom
st.sidebar.markdown("---")
st.sidebar.title("☁️ Cloud Storage")
if st.session_state.get('github_connected', False):
    st.sidebar.success("✅ Connected to GitHub")
    repo_url = f"https://github.com/{st.session_state.repo_owner}/{st.session_state.repo_name}"
    st.sidebar.markdown(f"🔗 [View Repository]({repo_url})")
    screenshots_url = f"{repo_url}/tree/main/screenshots"
    st.sidebar.markdown(f"📸 [View Screenshots]({screenshots_url})")
else:
    st.sidebar.warning("⚠️ GitHub not connected")
