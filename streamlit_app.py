import streamlit as st
import pandas as pd
import json
import os
import requests
import base64
import time
import uuid
import calendar
from datetime import date, datetime, timedelta
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="Trading Journal v7.5",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #64ffda;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .section-header {
        font-size: 2rem;
        color: #64ffda;
        border-bottom: 2px solid #64ffda;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: rgba(100, 255, 218, 0.1);
        border: 1px solid #64ffda;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
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
    outcomes = [trade.get('outcome', 'pending') for trade in all_trades]
    
    win_trades = outcomes.count('win')
    loss_trades = outcomes.count('loss')
    pending_trades = outcomes.count('pending')
    
    win_rate = (win_trades / (win_trades + loss_trades) * 100) if (win_trades + loss_trades) > 0 else 0
    
    # Tag analysis
    tag_counts = {}
    for trade in all_trades:
        for tag in trade.get('tags', []):
            if tag not in tag_counts:
                tag_counts[tag] = {'total': 0, 'wins': 0, 'losses': 0}
            tag_counts[tag]['total'] += 1
            if trade.get('outcome') == 'win':
                tag_counts[tag]['wins'] += 1
            elif trade.get('outcome') == 'loss':
                tag_counts[tag]['losses'] += 1
    
    return {
        'total_trades': total_trades,
        'win_trades': win_trades,
        'loss_trades': loss_trades,
        'pending_trades': pending_trades,
        'win_rate': win_rate,
        'tag_counts': tag_counts
    }

# Account balance functions
def get_account_settings(data):
    """Get account balance settings"""
    return data.get('account_settings', {})

def save_account_settings(data, starting_balance, start_date):
    """Save account balance settings"""
    data['account_settings'] = {
        'starting_balance': starting_balance,
        'start_date': start_date.strftime("%Y-%m-%d")
    }
    return data

def calculate_daily_balance_data(data):
    """Calculate daily balance data"""
    account_settings = get_account_settings(data)
    if not account_settings.get('starting_balance') or not account_settings.get('start_date'):
        return []
    
    start_date = datetime.strptime(account_settings['start_date'], "%Y-%m-%d").date()
    starting_balance = account_settings['starting_balance']
    
    balance_data = []
    current_balance = starting_balance
    current_date = start_date
    
    while current_date <= date.today():
        date_key = get_date_key(current_date)
        entry = data.get(date_key, {})
        
        # Get P&L and transactions for this day
        daily_pnl = entry.get('trading', {}).get('pnl', 0)
        transactions = entry.get('transactions', [])
        
        daily_deposits = sum(t['amount'] for t in transactions if t['type'] == 'deposit')
        daily_withdrawals = sum(t['amount'] for t in transactions if t['type'] == 'withdrawal')
        
        # Calculate net change
        net_transactions = daily_deposits - daily_withdrawals
        daily_change = daily_pnl + net_transactions
        current_balance += daily_change
        
        balance_data.append({
            'date': current_date,
            'date_str': current_date.strftime("%Y-%m-%d"),
            'balance': current_balance,
            'daily_pnl': daily_pnl,
            'daily_deposits': daily_deposits,
            'daily_withdrawals': daily_withdrawals,
            'net_transactions': net_transactions,
            'daily_change': daily_change
        })
        
        current_date += timedelta(days=1)
    
    return balance_data

# Parse trade log functions
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
        'winning_trades': 0,
        'losing_trades': 0,
        'total_trades': 0,
        'avg_winner': 0,
        'avg_loser': 0,
        'win_rate': 0,
        'daily_pnl': 0
    }
    
    # Track positions for P&L calculation
    open_positions = {}
    individual_trade_pnls = []
    
    for trade in trades:
        symbol = trade.get('Symbol', '')
        quantity = float(trade.get('Quantity', 0))
        price = float(trade.get('FillPrice', 0))
        side = trade.get('BuySell', '').lower()
        
        analysis['symbols'].add(symbol)
        analysis['order_types'].add(trade.get('OrderType', ''))
        analysis['total_volume'] += abs(quantity)
        analysis['prices'].append(price)
        
        if side == 'buy':
            analysis['buy_orders'] += 1
        elif side == 'sell':
            analysis['sell_orders'] += 1
        
        # Initialize position tracking for this symbol
        if symbol not in open_positions:
            open_positions[symbol] = {'qty': 0, 'avg_price': 0, 'total_cost': 0}
        
        # Calculate P&L for completed trades
        point_value = 20  # Default for MNQ
        pnl_change = 0
        
        if side == 'buy':
            if open_positions[symbol]['qty'] <= 0:
                # Opening new long or covering short
                current_qty = open_positions[symbol]['qty']
                if current_qty < 0:
                    # Covering short position
                    cover_qty = min(abs(current_qty), quantity)
                    avg_price = open_positions[symbol]['avg_price']
                    price_diff = avg_price - price
                    pnl_change = cover_qty * price_diff * point_value
                    
                    remaining_short = current_qty + cover_qty
                    if remaining_short < 0:
                        open_positions[symbol]['qty'] = remaining_short
                    else:
                        # Position fully covered, any remaining is new long
                        remaining_long = quantity - cover_qty
                        if remaining_long > 0:
                            open_positions[symbol]['qty'] = remaining_long
                            open_positions[symbol]['avg_price'] = price
                            open_positions[symbol]['total_cost'] = remaining_long * price
                        else:
                            open_positions[symbol] = {'qty': 0, 'avg_price': 0, 'total_cost': 0}
                else:
                    # Adding to long position or opening new long
                    total_cost = open_positions[symbol]['total_cost'] + (quantity * price)
                    total_qty = open_positions[symbol]['qty'] + quantity
                    open_positions[symbol]['qty'] = total_qty
                    open_positions[symbol]['avg_price'] = total_cost / total_qty
                    open_positions[symbol]['total_cost'] = total_cost
            else:
                # Adding to existing long position
                total_cost = open_positions[symbol]['total_cost'] + (quantity * price)
                total_qty = open_positions[symbol]['qty'] + quantity
                open_positions[symbol]['qty'] = total_qty
                open_positions[symbol]['avg_price'] = total_cost / total_qty
                open_positions[symbol]['total_cost'] = total_cost
        else:  # sell
            if open_positions[symbol]['qty'] > 0:
                # Closing long position
                avg_price = open_positions[symbol]['avg_price']
                price_diff = price - avg_price
                pnl_change = quantity * price_diff * point_value
                
                remaining_qty = open_positions[symbol]['qty'] - quantity
                if remaining_qty > 0:
                    open_positions[symbol]['qty'] = remaining_qty
                    open_positions[symbol]['total_cost'] = remaining_qty * avg_price
                else:
                    open_positions[symbol] = {'qty': 0, 'avg_price': 0, 'total_cost': 0}
            else:
                if open_positions[symbol]['qty'] < 0:
                    avg_price = open_positions[symbol]['avg_price']
                    price_diff = avg_price - price
                    pnl_change = quantity * price_diff * point_value
                    
                    remaining_qty = open_positions[symbol]['qty'] + quantity
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

# Initialize session state
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()
if 'page' not in st.session_state:
    st.session_state.page = "📊 Calendar View"
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
    balance_data = calculate_daily_balance_data(data)
    if balance_data:
        current_balance = balance_data[-1]['balance']
        balance_color = "green" if current_balance >= account_settings['starting_balance'] else "red"
        
        st.sidebar.markdown(f"**Current Balance:** <span style='color: {balance_color}'>${current_balance:.2f}</span>", unsafe_allow_html=True)
        
        # Show recent P&L
        recent_5_data = {k: v for k, v in data.items() if k.startswith('2025') and 'trading' in v}
        recent_30_data = {k: v for k, v in data.items() if k.startswith('2025') and 'trading' in v}
        
        # Calculate period metrics
        def get_period_metrics(period_data):
            total_pnl = sum(entry.get('trading', {}).get('pnl', 0) for entry in period_data.values())
            total_rules_followed = 0
            total_rules_possible = 0
            
            for entry in period_data.values():
                rule_compliance = entry.get('trading', {}).get('rule_compliance', {})
                total_rules_followed += sum(rule_compliance.values())
                total_rules_possible += len(rule_compliance)
            
            overall_compliance = (total_rules_followed / total_rules_possible * 100) if total_rules_possible > 0 else 0
            return total_pnl, overall_compliance

        # Get metrics
        pnl_5, compliance_5 = get_period_metrics(recent_5_data)
        pnl_30, compliance_30 = get_period_metrics(recent_30_data)

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

# GitHub Setup Section
st.sidebar.markdown("---")
st.sidebar.title("⚙️ GitHub Sync")

if st.session_state.get('github_connected', False):
    st.sidebar.success("✅ Connected to GitHub")
    st.sidebar.write(f"📂 Repo: {st.session_state.get('repo_owner', '')}/{st.session_state.get('repo_name', '')}")
    
    if st.sidebar.button("🔄 Sync Now"):
        if st.session_state.github_storage.save_journal_entry("manual_sync", {}, data):
            st.sidebar.success("✅ Data synced to GitHub!")
        else:
            st.sidebar.error("❌ Sync failed")
else:
    with st.sidebar.expander("🔗 Connect GitHub", expanded=False):
        github_token = st.text_input("GitHub Token", type="password", help="Personal Access Token with repo permissions")
        repo_owner = st.text_input("Repository Owner", help="GitHub username or organization")
        repo_name = st.text_input("Repository Name", help="Repository name (e.g., 'trading-journal')")
        
        if st.button("Connect"):
            if github_token and repo_owner and repo_name:
                if st.session_state.github_storage.connect(github_token, repo_owner, repo_name):
                    st.session_state.github_connected = True
                    st.session_state.github_token = github_token
                    st.session_state.repo_owner = repo_owner
                    st.session_state.repo_name = repo_name
                    st.success("✅ Connected to GitHub!")
                    st.rerun()
                else:
                    st.error("❌ Failed to connect. Check your credentials.")
            else:
                st.warning("⚠️ Please fill in all fields")

# Date selector
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

# SIDEBAR NAVIGATION
st.sidebar.markdown("---")
st.sidebar.title("📋 Navigation")

# Navigation buttons
if st.sidebar.button("📊 Calendar View", key="nav_calendar", use_container_width=True):
    st.session_state.page = "📊 Calendar View"

if st.sidebar.button("🌅 Morning Prep", key="nav_morning", use_container_width=True):
    st.session_state.page = "🌅 Morning Prep"

if st.sidebar.button("📈 Trade Day", key="nav_trade_day", use_container_width=True):
    st.session_state.page = "📈 Trade Day"

if st.sidebar.button("📈 Trading Review", key="nav_trading", use_container_width=True):
    st.session_state.page = "📈 Trading Review"

if st.sidebar.button("🌙 Evening Recap", key="nav_evening", use_container_width=True):
    st.session_state.page = "🌙 Evening Recap"

if st.sidebar.button("📚 Historical Analysis", key="nav_history", use_container_width=True):
    st.session_state.page = "📚 Historical Analysis"

if st.sidebar.button("💰 Balance & Ledger", key="nav_balance_history", use_container_width=True):
    st.session_state.page = "💰 Balance & Ledger"

if st.sidebar.button("🏷️ Tag Management", key="nav_tag_management", use_container_width=True):
    st.session_state.page = "🏷️ Tag Management"

page = st.session_state.page

date_key = get_date_key(selected_date)

# Initialize date entry if doesn't exist
if date_key not in data:
    data[date_key] = {
        'morning': {},
        'trade_day': {},
        'trading': {},
        'evening': {},
        'rules': []
    }

current_entry = data[date_key]

# ======== ENHANCED TRADE DAY PAGE WITH SESSION ANALYTICS ========
if page == "📈 Trade Day":
    st.markdown('<div class="section-header">📈 Live Trade Day</div>', unsafe_allow_html=True)
    
    # Show current date and delete option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📅 {selected_date.strftime('%A, %B %d, %Y')}")
    with col2:
        if st.button("🗑️ Delete Entry", key="delete_trade_day_entry", help="Delete all trade day data for this date"):
            if 'trade_day' in current_entry:
                del current_entry['trade_day']
                if st.session_state.get('github_connected', False):
                    st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                save_local_data(data)
                st.success("Trade day entry deleted!")
                st.rerun()
    
    # Initialize trade_day if doesn't exist
    if 'trade_day' not in current_entry:
        current_entry['trade_day'] = {
            'market_observations': '', 
            'trades': [],
            'session_analytics': {
                'total_trades': 0,
                'winners': 0,
                'losers': 0,
                'break_even': 0,
                'avg_winner': 0.0,
                'avg_loser': 0.0,
                'largest_winner': 0.0,
                'largest_loser': 0.0,
                'avg_winner_duration': 0,
                'avg_loser_duration': 0,
                'gross_pnl': 0.0,
                'daily_commission': 0.0,
                'net_pnl': 0.0
            }
        }
    
    # Ensure session_analytics exists (for existing data)
    if 'session_analytics' not in current_entry['trade_day']:
        current_entry['trade_day']['session_analytics'] = {
            'total_trades': 0,
            'winners': 0,
            'losers': 0,
            'break_even': 0,
            'avg_winner': 0.0,
            'avg_loser': 0.0,
            'largest_winner': 0.0,
            'largest_loser': 0.0,
            'avg_winner_duration': 0,
            'avg_loser_duration': 0,
            'gross_pnl': 0.0,
            'daily_commission': 0.0,
            'net_pnl': 0.0
        }
    
    # ======== TRADING SESSION ANALYTICS SECTION ========
    st.subheader("📊 Trading Session Analytics")
    
    # Get current analytics
    analytics = current_entry['trade_day']['session_analytics']
    
    # Calculate win rate
    total_trades = analytics.get('total_trades', 0)
    winners = analytics.get('winners', 0)
    losers = analytics.get('losers', 0)
    break_even = analytics.get('break_even', 0)
    win_rate = (winners / total_trades * 100) if total_trades > 0 else 0
    
    # Display analytics in styled container
    st.markdown("""
    <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 2px solid #333; margin-bottom: 20px;">
    """, unsafe_allow_html=True)
    
    # First row of metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trades", total_trades)
    with col2:
        st.metric("Winners", winners, delta=f"+{winners}" if winners > 0 else None)
    with col3:
        st.metric("Losers", losers, delta=f"-{losers}" if losers > 0 else None)
    with col4:
        st.metric("Break-Even", break_even)
    
    # Second row of metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col2:
        avg_winner = analytics.get('avg_winner', 0)
        st.metric("Avg Winner", f"${avg_winner:.2f}")
    with col3:
        avg_loser = analytics.get('avg_loser', 0)
        st.metric("Avg Loser", f"${avg_loser:.2f}")
    with col4:
        net_pnl = analytics.get('net_pnl', 0)
        color = "green" if net_pnl > 0 else "red" if net_pnl < 0 else "gray"
        st.markdown(f'<h3 style="color: {color}; text-align: center;">Net P&L: ${net_pnl:.2f}</h3>', unsafe_allow_html=True)
    
    # Third row - Duration and largest trades
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_winner_duration = analytics.get('avg_winner_duration', 0)
        st.metric("Avg Winner Duration", f"{avg_winner_duration} min")
    with col2:
        avg_loser_duration = analytics.get('avg_loser_duration', 0)
        st.metric("Avg Loser Duration", f"{avg_loser_duration} min")
    with col3:
        largest_winner = analytics.get('largest_winner', 0)
        st.metric("Largest Winner", f"${largest_winner:.2f}")
    with col4:
        largest_loser = analytics.get('largest_loser', 0)
        st.metric("Largest Loser", f"${largest_loser:.2f}")
    
    # P&L Summary row
    col1, col2, col3 = st.columns(3)
    with col1:
        gross_pnl = analytics.get('gross_pnl', 0)
        st.metric("Gross P&L", f"${gross_pnl:.2f}")
    with col2:
        daily_commission = analytics.get('daily_commission', 0)
        st.metric("Commissions", f"${daily_commission:.2f}")
    with col3:
        calculated_net = gross_pnl - daily_commission
        st.metric("Net P&L", f"${calculated_net:.2f}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ======== COMMISSION INPUT AND UPDATE SECTION ========
    st.subheader("💰 Session Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Daily Commission Input**")
        commission_input = st.number_input(
            "Total Daily Commission ($)",
            min_value=0.0,
            value=analytics.get('daily_commission', 0.0),
            step=0.01,
            format="%.2f",
            help="Enter the total commission costs for today's trading session",
            key="daily_commission_input_field"
        )
        
        if st.button("💾 Update Commission", key="save_commission_button"):
            current_entry['trade_day']['session_analytics']['daily_commission'] = commission_input
            # Recalculate net P&L
            gross = current_entry['trade_day']['session_analytics'].get('gross_pnl', 0)
            current_entry['trade_day']['session_analytics']['net_pnl'] = gross - commission_input
            
            if st.session_state.get('github_connected', False):
                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                    st.success("✅ Commission updated!")
                else:
                    save_local_data(data)
                    st.success("💾 Commission updated locally!")
            else:
                save_local_data(data)
                st.success("💾 Commission updated locally!")
            st.rerun()
    
    with col2:
        st.markdown("**Trading Review Integration**")
        st.markdown("Transfer today's P&L to Trading Review page")
        
        if st.button("🔄 Update Trading Review P&L", key="update_trading_review_button", type="primary"):
            # Update the trading review P&L with net P&L from trade day
            if 'trading' not in current_entry:
                current_entry['trading'] = {}
            
            net_pnl_value = current_entry['trade_day']['session_analytics'].get('net_pnl', 0)
            gross_pnl_value = current_entry['trade_day']['session_analytics'].get('gross_pnl', 0)
            commission_value = current_entry['trade_day']['session_analytics'].get('daily_commission', 0)
            
            current_entry['trading']['pnl'] = net_pnl_value
            current_entry['trading']['trade_day_sync'] = True
            current_entry['trading']['gross_pnl'] = gross_pnl_value
            current_entry['trading']['commissions'] = commission_value
            
            if st.session_state.get('github_connected', False):
                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                    st.success(f"✅ Trading Review P&L updated to ${net_pnl_value:.2f}!")
                else:
                    save_local_data(data)
                    st.success(f"💾 Trading Review P&L updated to ${net_pnl_value:.2f} locally!")
            else:
                save_local_data(data)
                st.success(f"💾 Trading Review P&L updated to ${net_pnl_value:.2f} locally!")
    
    # ======== MANUAL ANALYTICS UPDATE SECTION ========
    st.markdown("---")
    with st.expander("✏️ Manual Analytics Entry", expanded=False):
        st.markdown("**Update your trading session statistics manually:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_total_trades = st.number_input("Total Trades", min_value=0, value=total_trades, key="manual_total_trades_field")
            new_winners = st.number_input("Winners", min_value=0, value=winners, key="manual_winners_field")
            new_losers = st.number_input("Losers", min_value=0, value=losers, key="manual_losers_field")
            new_break_even = st.number_input("Break-Even", min_value=0, value=break_even, key="manual_break_even_field")
            new_avg_winner = st.number_input("Avg Winner ($)", value=avg_winner, format="%.2f", key="manual_avg_winner_field")
            new_avg_loser = st.number_input("Avg Loser ($)", value=avg_loser, format="%.2f", key="manual_avg_loser_field")
        
        with col2:
            new_largest_winner = st.number_input("Largest Winner ($)", value=analytics.get('largest_winner', 0), format="%.2f", key="manual_largest_winner_field")
            new_largest_loser = st.number_input("Largest Loser ($)", value=analytics.get('largest_loser', 0), format="%.2f", key="manual_largest_loser_field")
            new_avg_winner_duration = st.number_input("Avg Winner Duration (min)", min_value=0, value=analytics.get('avg_winner_duration', 0), key="manual_avg_winner_duration_field")
            new_avg_loser_duration = st.number_input("Avg Loser Duration (min)", min_value=0, value=analytics.get('avg_loser_duration', 0), key="manual_avg_loser_duration_field")
            new_gross_pnl = st.number_input("Gross P&L ($)", value=analytics.get('gross_pnl', 0), format="%.2f", key="manual_gross_pnl_field")
        
        if st.button("💾 Save Analytics", key="save_manual_analytics_button", type="primary"):
            # Update all analytics
            current_entry['trade_day']['session_analytics'] = {
                'total_trades': new_total_trades,
                'winners': new_winners,
                'losers': new_losers,
                'break_even': new_break_even,
                'avg_winner': new_avg_winner,
                'avg_loser': new_avg_loser,
                'largest_winner': new_largest_winner,
                'largest_loser': new_largest_loser,
                'avg_winner_duration': new_avg_winner_duration,
                'avg_loser_duration': new_avg_loser_duration,
                'gross_pnl': new_gross_pnl,
                'daily_commission': commission_input,
                'net_pnl': new_gross_pnl - commission_input
            }
            
            if st.session_state.get('github_connected', False):
                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                    st.success("✅ Session analytics updated!")
                else:
                    save_local_data(data)
                    st.success("💾 Session analytics updated locally!")
            else:
                save_local_data(data)
                st.success("💾 Session analytics updated locally!")
            st.rerun()
    
    # Quick populate button for example data
    if st.button("🎯 Load Example Analytics", key="load_example_analytics", help="Load the example analytics data"):
        current_entry['trade_day']['session_analytics'] = {
            'total_trades': 15,
            'winners': 9,
            'losers': 4,
            'break_even': 2,
            'avg_winner': 45.50,
            'avg_loser': -28.75,
            'largest_winner': 89.25,
            'largest_loser': -52.00,
            'avg_winner_duration': 12,
            'avg_loser_duration': 8,
            'gross_pnl': 312.50,
            'daily_commission': 14.00,
            'net_pnl': 298.50
        }
        
        if st.session_state.get('github_connected', False):
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Example analytics loaded!")
            else:
                save_local_data(data)
                st.success("💾 Example analytics loaded locally!")
        else:
            save_local_data(data)
            st.success("💾 Example analytics loaded locally!")
        st.rerun()
    
    # ======== TRADE LOG IMPORT SECTION ========
    st.markdown("---")
    st.subheader("📁 Import Trades from Log")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        trade_log_file = st.file_uploader(
            "Upload trade log file (CSV/TSV/PDF)",
            type=['txt', 'csv', 'tsv', 'pdf'],
            help="Upload your broker's trade log to automatically parse trades and calculate analytics",
            key="trade_log_import_uploader"
        )
        
        if trade_log_file:
            st.info("💡 This will parse your trade log and automatically populate the session analytics above.")
            
            if st.button("🔄 Process Trade Log", key="process_trade_log_button", type="primary"):
                try:
                    if trade_log_file.type == "application/pdf":
                        st.info("📄 Processing PDF file...")
                        st.warning("⚠️ PDF parsing requires additional implementation")
                    else:
                        file_content = trade_log_file.read().decode('utf-8')
                        trades, error = parse_trade_log(file_content)
                        
                        if error:
                            st.error(f"Error parsing file: {error}")
                        else:
                            analysis = analyze_trades(trades)
                            
                            # Auto-populate analytics from parsed data
                            if analysis:
                                current_entry['trade_day']['session_analytics'] = {
                                    'total_trades': analysis.get('total_trades', 0),
                                    'winners': analysis.get('winning_trades', 0),
                                    'losers': analysis.get('losing_trades', 0),
                                    'break_even': analysis.get('total_trades', 0) - analysis.get('winning_trades', 0) - analysis.get('losing_trades', 0),
                                    'avg_winner': analysis.get('avg_winner', 0),
                                    'avg_loser': analysis.get('avg_loser', 0),
                                    'largest_winner': max(analysis.get('trade_pnls', [0])) if analysis.get('trade_pnls') else 0,
                                    'largest_loser': min(analysis.get('trade_pnls', [0])) if analysis.get('trade_pnls') else 0,
                                    'avg_winner_duration': 0,  # Would need timestamps to calculate
                                    'avg_loser_duration': 0,   # Would need timestamps to calculate
                                    'gross_pnl': analysis.get('daily_pnl', 0),
                                    'daily_commission': commission_input,
                                    'net_pnl': analysis.get('daily_pnl', 0) - commission_input
                                }
                                
                                if st.session_state.get('github_connected', False):
                                    if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                                        st.success(f"✅ Trade log processed! Found {analysis.get('total_trades', 0)} completed trades.")
                                    else:
                                        save_local_data(data)
                                        st.success(f"💾 Trade log processed locally! Found {analysis.get('total_trades', 0)} completed trades.")
                                else:
                                    save_local_data(data)
                                    st.success(f"💾 Trade log processed locally! Found {analysis.get('total_trades', 0)} completed trades.")
                                st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
    
    with col2:
        st.markdown("**Supported Formats:**")
        st.write("📄 CSV/TSV trade logs")
        st.write("📄 PDF broker statements")
        st.write("📄 AMP Futures exports")
        
        st.markdown("**Auto-Populates:**")
        st.write("📊 All session analytics")
        st.write("💰 Commission calculations")
        st.write("🎯 P&L metrics")
    
    # Show sample format
    with st.expander("📋 Sample File Format", expanded=False):
        st.markdown("**CSV/TSV Format Example:**")
        st.code("""
DateTime, Symbol, BuySell, Quantity, FillPrice, OrderType, OpenClose, PositionQuantity
2025-09-08 05:49:31, F.US.mNQU25, Buy, 3, 23736.50, Market, Open, 3
2025-09-08 06:06:38, F.US.mNQU25, Sell, 1, 23746.75, Market, Close, 2
        """)
    
    # ======== MANUAL TRADE ENTRY SECTION ========
    st.markdown("---")
    st.subheader("➕ Add New Trade (Manual Entry)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Trade description
        trade_description = st.text_area(
            "Trade Description",
            placeholder="Describe your trade setup, entry reasoning, target, stop loss, etc.",
            height=100,
            key="new_trade_description_input"
        )
        
        # Screenshot upload for trade
        trade_screenshot = st.file_uploader(
            "Trade Screenshot",
            type=['png', 'jpg', 'jpeg'],
            help="Upload entry chart, setup screenshot, or other relevant image",
            key="new_trade_screenshot_uploader"
        )
        
        screenshot_caption = ""
        if trade_screenshot:
            screenshot_caption = st.text_input(
                "Screenshot Caption",
                placeholder="Describe this screenshot...",
                key="new_trade_screenshot_caption_input"
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
            key="trade_tags_select_input"
        )
        
        # Add new tags
        new_tags_input = st.text_input(
            "Add new tags (comma-separated)",
            placeholder="scalp, breakout, TSLA",
            key="new_tags_input_field"
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
            key="trade_outcome_select"
        )
    
    # Add trade button
    if st.button("🚀 Add Trade", type="primary", key="add_trade_button"):
        if not trade_description.strip():
            st.warning("⚠️ Please add a trade description!")
        else:
            # Create new trade entry
            new_trade = {
                'id': f"trade_{int(time.time())}",
                'description': trade_description,
                'tags': all_trade_tags,
                'outcome': trade_outcome,
                'timestamp': datetime.now().isoformat(),
                'screenshots': []
            }
            
            # Handle screenshot upload if present
            if trade_screenshot:
                new_trade['screenshots'].append({
                    'filename': trade_screenshot.name,
                    'caption': screenshot_caption
                })
            
            # Add trade to current entry
            if 'trades' not in current_entry['trade_day']:
                current_entry['trade_day']['trades'] = []
            
            # Add new tags to the system
            for tag in new_tags:
                if 'tags' not in data:
                    data['tags'] = []
                if tag not in data['tags']:
                    data['tags'].append(tag)
            
            current_entry['trade_day']['trades'].append(new_trade)
            
            # Save the trade
            if st.session_state.get('github_connected', False):
                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                    st.success(f"✅ Trade added! Tags: {', '.join(all_trade_tags) if all_trade_tags else 'None'}")
                else:
                    save_local_data(data)
                    st.success(f"💾 Trade added locally! Tags: {', '.join(all_trade_tags) if all_trade_tags else 'None'}")
            else:
                save_local_data(data)
                st.success(f"💾 Trade added locally! Tags: {', '.join(all_trade_tags) if all_trade_tags else 'None'}")
            
            st.rerun()
    
    # ======== EXISTING TRADES DISPLAY SECTION ========
    st.markdown("---")
    st.subheader("📋 Today's Trades")
    
    trades = current_entry['trade_day'].get('trades', [])
    
    if trades:
        for i, trade in enumerate(trades):
            # Create outcome color and icon
            outcome_icons = {
                'pending': '⏳',
                'win': '✅', 
                'loss': '❌'
            }
            
            outcome_colors = {
                'pending': '#ffa500',
                'win': '#00ff00',
                'loss': '#ff0000'
            }
            
            outcome = trade.get('outcome', 'pending')
            icon = outcome_icons.get(outcome, '⏳')
            color = outcome_colors.get(outcome, '#ffa500')
            
            # Trade tags display
            tags = trade.get('tags', [])
            tags_html = ' '.join([f'<span class="tag-chip">{tag}</span>' for tag in tags]) if tags else '<em>No tags</em>'
            
            # Display trade card
            st.markdown(f"""
            <div style="border: 2px solid {color}; padding: 15px; margin: 10px 0; border-radius: 10px; background: rgba(0,0,0,0.1);">
                <h4>{icon} Trade #{i+1} - {outcome.upper()}</h4>
                <p><strong>Description:</strong> {trade.get('description', '')[:100]}{'...' if len(trade.get('description', '')) > 100 else ''}</p>
                <p><strong>Tags:</strong> {tags_html}</p>
                <p><small><strong>Time:</strong> {trade.get('timestamp', 'N/A')}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Edit button for each trade
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("✏️ Edit", key=f"edit_trade_button_{i}"):
                    st.session_state[f"editing_trade_{i}"] = True
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"delete_trade_button_{i}"):
                    current_entry['trade_day']['trades'].pop(i)
                    
                    if st.session_state.get('github_connected', False):
                        if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                            st.success("✅ Trade deleted!")
                        else:
                            save_local_data(data)
                            st.success("💾 Trade deleted locally!")
                    else:
                        save_local_data(data)
                        st.success("💾 Trade deleted locally!")
                    st.rerun()
            
            # Edit mode for this trade
            if st.session_state.get(f"editing_trade_{i}", False):
                with st.expander(f"Edit Trade #{i+1}", expanded=True):
                    edit_description = st.text_area(
                        "Edit Description",
                        value=trade.get('description', ''),
                        key=f"edit_desc_input_{i}"
                    )
                    
                    edit_outcome = st.selectbox(
                        "Edit Outcome",
                        options=["pending", "win", "loss"],
                        index=["pending", "win", "loss"].index(trade.get('outcome', 'pending')),
                        format_func=lambda x: {
                            "pending": "⏳ Pending", 
                            "win": "✅ Win", 
                            "loss": "❌ Loss"
                        }[x],
                        key=f"edit_outcome_select_{i}"
                    )
                    
                    edit_tags_str = st.text_input(
                        "Edit Tags (comma-separated)",
                        value=", ".join(trade.get('tags', [])),
                        key=f"edit_tags_input_{i}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Save Changes", key=f"save_edit_button_{i}"):
                            # Update trade
                            current_entry['trade_day']['trades'][i]['description'] = edit_description
                            current_entry['trade_day']['trades'][i]['outcome'] = edit_outcome
                            edit_tags = [tag.strip() for tag in edit_tags_str.split(',') if tag.strip()]
                            current_entry['trade_day']['trades'][i]['tags'] = edit_tags
                            
                            # Save changes
                            if st.session_state.get('github_connected', False):
                                if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                                    st.success("✅ Trade updated!")
                                else:
                                    save_local_data(data)
                                    st.success("💾 Trade updated locally!")
                            else:
                                save_local_data(data)
                                st.success("💾 Trade updated locally!")
                            
                            st.session_state[f"editing_trade_{i}"] = False
                            st.rerun()
                    
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_edit_button_{i}"):
                            st.session_state[f"editing_trade_{i}"] = False
                            st.rerun()
    
    else:
        st.info("No trades recorded for today. Add your first trade above or import from a trade log!")
    
    # ======== MARKET OBSERVATIONS SECTION ========
    st.markdown("---")
    st.subheader("🔍 Market Observations")
    market_observations = st.text_area(
        "What do you see in the markets today?",
        value=current_entry['trade_day'].get('market_observations', ''),
        height=150,
        placeholder="Market conditions, trends, key levels, news impact, volume patterns, sector rotation, etc.",
        key="market_observations_input"
    )
    
    # Save market observations
    if st.button("💾 Save Market Observations", key="save_observations_button"):
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
    
    st.subheader(f"{first_day.strftime('%B %Y')}")
    
    # Calendar headers
    header_cols = st.columns(8)  # 7 days + 1 for week totals
    headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Week Total"]
    for i, header in enumerate(headers):
        header_cols[i].markdown(f"**{header}**")
    
    # Display calendar weeks
    for week in cal:
        week_cols = st.columns(8)  # 7 days + 1 for week total
        week_pnl = 0
        
        for i, day in enumerate(week):
            if day == 0:
                # Empty day
                week_cols[i].markdown("---")
            else:
                # Create date for this day
                day_date = date(first_day.year, first_day.month, day)
                day_key = get_date_key(day_date)
                
                if day_key in data:
                    # Get P&L and process compliance for this day
                    pnl = data[day_key].get('trading', {}).get('pnl', 0)
                    week_pnl += pnl
                    
                    # Determine compliance color
                    rule_compliance = data[day_key].get('trading', {}).get('rule_compliance', {})
                    if rule_compliance:
                        compliance_rate = sum(rule_compliance.values()) / len(rule_compliance)
                        compliance_color = "🟢" if compliance_rate >= 0.8 else "🔴"
                    else:
                        compliance_color = "⚪"
                    
                    # P&L color
                    pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "gray"
                    
                    # Display day with data
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
        
        # Weekly total column
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
        
        market_news = st.text_area(
            "Key Market News & Events",
            value=current_entry['morning'].get('market_news', ""),
            height=100,
            help="Economic calendar, earnings, Fed announcements, geopolitical events"
        )
        
        triggers_present = st.text_area(
            "Emotional/Psychological Triggers Present?",
            value=current_entry['morning'].get('triggers_present', ""),
            height=100,
            help="Work stress, family issues, financial pressure, FOMO, revenge trading urges"
        )
    
    with col2:
        st.subheader("Trading Preparation")
        
        grateful_for = st.text_area(
            "Three Things I'm Grateful For",
            value=current_entry['morning'].get('grateful_for', ""),
            height=100,
            help="Start with gratitude to frame your mindset positively"
        )
        
        daily_goal = st.text_area(
            "Today's Goal (Non-Financial)",
            value=current_entry['morning'].get('daily_goal', ""),
            height=100,
            help="Focus on process goals like 'follow all rules' rather than P&L targets"
        )
        
        trading_process = st.text_area(
            "Trading Process Focus",
            value=current_entry['morning'].get('trading_process', ""),
            height=100,
            help="What specific part of your process will you focus on today?"
        )
    
    # Screenshots section
    st.markdown("---")
    st.subheader("📸 Morning Market Screenshots")
    
    # Upload new screenshot
    uploaded_screenshot = st.file_uploader(
        "Upload morning market screenshot",
        type=['png', 'jpg', 'jpeg'],
        help="Charts, market overview, key levels",
        key="morning_screenshot_upload"
    )
    
    if uploaded_screenshot:
        caption = st.text_input("Screenshot Caption", key="morning_screenshot_caption")
        
        if st.button("💾 Save Screenshot", key="save_morning_screenshot"):
            # Save screenshot
            if st.session_state.get('github_connected', False):
                screenshot_url = st.session_state.github_storage.upload_screenshot(
                    uploaded_screenshot.getbuffer(), 
                    f"morning_{uploaded_screenshot.name}", 
                    date_key
                )
                
                if screenshot_url:
                    if 'morning_screenshots' not in current_entry['morning']:
                        current_entry['morning']['morning_screenshots'] = []
                    
                    current_entry['morning']['morning_screenshots'].append({
                        'url': screenshot_url,
                        'caption': caption,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
                    st.success("✅ Screenshot saved to GitHub!")
                    st.rerun()
                else:
                    st.error("❌ Failed to upload screenshot")
            else:
                # Local storage fallback
                local_path = save_uploaded_file_local(uploaded_screenshot, date_key, "morning")
                if local_path:
                    if 'morning_screenshots' not in current_entry['morning']:
                        current_entry['morning']['morning_screenshots'] = []
                    
                    current_entry['morning']['morning_screenshots'].append({
                        'url': local_path,
                        'caption': caption,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    save_local_data(data)
                    st.success("💾 Screenshot saved locally!")
                    st.rerun()
    
    # Display existing screenshots
    morning_screenshots = current_entry['morning'].get('morning_screenshots', [])
    if morning_screenshots:
        st.subheader("Saved Screenshots")
        for i, screenshot in enumerate(morning_screenshots):
            col1, col2 = st.columns([3, 1])
            with col1:
                display_image_full_size(screenshot['url'], screenshot.get('caption', 'Morning Screenshot'))
            with col2:
                if st.button("🗑️ Delete", key=f"delete_morning_screenshot_{i}"):
                    current_entry['morning']['morning_screenshots'].pop(i)
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
        
        what_went_well = st.text_area(
            "What Went Well?",
            value=current_entry['trading'].get('what_went_well', ""),
            height=100,
            help="Celebrate wins and positive behaviors"
        )
        
        what_to_improve = st.text_area(
            "What Could Be Improved?",
            value=current_entry['trading'].get('what_to_improve', ""),
            height=100,
            help="Specific areas for growth without self-criticism"
        )
    
    with col2:
        st.subheader("Rule Compliance")
        st.write("Rate your adherence to each trading rule (1-5 scale)")
        
        # Trading rules
        rules = [
            "Position sizing according to plan",
            "Proper risk management/stop losses",
            "Followed entry criteria",
            "Avoided FOMO trades",
            "Maintained emotional discipline",
            "Stuck to trading hours",
            "Followed exit strategy",
            "Did not overtrade"
        ]
        
        rule_compliance = {}
        for rule in rules:
            rule_compliance[rule] = st.slider(
                rule,
                1, 5,
                value=current_entry['trading'].get('rule_compliance', {}).get(rule, 3),
                key=f"rule_{rule.replace(' ', '_').replace('/', '_')}"
            )
        
        # Calculate overall compliance
        avg_compliance = sum(rule_compliance.values()) / len(rule_compliance)
        compliance_color = "green" if avg_compliance >= 4 else "orange" if avg_compliance >= 3 else "red"
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; border: 2px solid {compliance_color};">
            <h4 style="color: {compliance_color};">Overall Compliance: {avg_compliance:.1f}/5</h4>
        </div>
        """, unsafe_allow_html=True)
    
    # Save trading review
    if st.button("💾 Save Trading Review", type="primary"):
        current_entry['trading'] = {
            'pnl': pnl,
            'process_grade': process_grade,
            'grade_reasoning': grade_reasoning,
            'what_went_well': what_went_well,
            'what_to_improve': what_to_improve,
            'rule_compliance': rule_compliance
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
                st.metric("Trading Days", total_trading_days)
            with col3:
                win_rate = (profitable_days / total_trading_days * 100) if total_trading_days > 0 else 0
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with col4:
                avg_daily = total_pnl / total_trading_days if total_trading_days > 0 else 0
                st.metric("Avg Daily P&L", f"${avg_daily:.2f}")
            
            # Process compliance
            if total_trading_days > 0:
                compliance_rate = (process_compliance_days / total_trading_days * 100)
                st.metric("Process Compliance Rate", f"{compliance_rate:.1f}%")
            
            # Additional statistics
            if daily_pnls:
                st.subheader("Detailed Statistics")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Best Day:** ${max(daily_pnls):.2f}")
                    st.write(f"**Worst Day:** ${min(daily_pnls):.2f}")
                    st.write(f"**Largest Drawdown:** ${min(daily_pnls):.2f}")
                
                with col2:
                    profitable_pnls = [pnl for pnl in daily_pnls if pnl > 0]
                    losing_pnls = [pnl for pnl in daily_pnls if pnl < 0]
                    
                    if profitable_pnls:
                        avg_winner = sum(profitable_pnls) / len(profitable_pnls)
                        st.write(f"**Average Winner:** ${avg_winner:.2f}")
                    
                    if losing_pnls:
                        avg_loser = sum(losing_pnls) / len(losing_pnls)
                        st.write(f"**Average Loser:** ${avg_loser:.2f}")
                
                # Simple P&L chart
                if len(daily_pnls) > 1:
                    st.subheader("P&L Progression")
                    df = pd.DataFrame({
                        'Date': [datetime.strptime(date_key, "%Y-%m-%d").date() for date_key in sorted(filtered_data.keys())],
                        'P&L': daily_pnls
                    })
                    st.line_chart(df.set_index('Date'))
        else:
            st.warning("No trading data found for the selected period.")

# ======== BALANCE & LEDGER PAGE ========
elif page == "💰 Balance & Ledger":
    st.markdown('<div class="section-header">💰 Account Balance & Transaction Ledger</div>', unsafe_allow_html=True)
    
    account_settings = get_account_settings(data)
    
    if not account_settings.get('starting_balance') or not account_settings.get('start_date'):
        st.warning("⚠️ Please set up your account balance tracking in the sidebar first.")
        st.info("Go to the sidebar and expand '⚙️ Setup Account Tracking' to get started.")
    else:
        # Display balance chart and management
        balance_data = calculate_daily_balance_data(data)
        
        if balance_data:
            # Current balance display
            current_balance = balance_data[-1]['balance']
            starting_balance = account_settings['starting_balance']
            total_change = current_balance - starting_balance
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Balance", f"${current_balance:.2f}")
            with col2:
                st.metric("Starting Balance", f"${starting_balance:.2f}")
            with col3:
                change_color = "green" if total_change >= 0 else "red"
                st.metric("Total Change", f"${total_change:.2f}", delta=f"{total_change:.2f}")
            
            # Balance chart
            st.subheader("📈 Balance History")
            df_balance = pd.DataFrame(balance_data)
            df_balance['Date'] = pd.to_datetime(df_balance['date_str'])
            st.line_chart(df_balance.set_index('Date')['balance'])
            
            # Recent transactions
            st.subheader("📝 Transaction Management")
            
            # Add new transaction
            with st.expander("➕ Add Transaction", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    transaction_date = st.date_input(
                        "Transaction Date",
                        value=selected_date,
                        key="transaction_date"
                    )
                
                with col2:
                    transaction_type = st.selectbox(
                        "Type",
                        ["deposit", "withdrawal"],
                        format_func=lambda x: "💰 Deposit" if x == "deposit" else "💸 Withdrawal",
                        key="transaction_type"
                    )
                
                with col3:
                    transaction_amount = st.number_input(
                        "Amount ($)",
                        min_value=0.01,
                        step=100.0,
                        format="%.2f",
                        key="transaction_amount"
                    )
                
                transaction_description = st.text_input(
                    "Description",
                    placeholder="Optional description for this transaction",
                    key="transaction_description"
                )
                
                if st.button("💾 Add Transaction", key="add_transaction"):
                    trans_date_key = get_date_key(transaction_date)
                    
                    if trans_date_key not in data:
                        data[trans_date_key] = {
                            'morning': {},
                            'trade_day': {},
                            'trading': {},
                            'evening': {},
                            'rules': []
                        }
                    
                    if 'transactions' not in data[trans_date_key]:
                        data[trans_date_key]['transactions'] = []
                    
                    data[trans_date_key]['transactions'].append({
                        'type': transaction_type,
                        'amount': transaction_amount,
                        'description': transaction_description,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if st.session_state.get('github_connected', False):
                        if st.session_state.github_storage.save_journal_entry(trans_date_key, data[trans_date_key], data):
                            st.success(f"✅ {transaction_type.title()} of ${transaction_amount:.2f} added!")
                        else:
                            save_local_data(data)
                            st.success(f"💾 {transaction_type.title()} of ${transaction_amount:.2f} added locally!")
                    else:
                        save_local_data(data)
                        st.success(f"💾 {transaction_type.title()} of ${transaction_amount:.2f} added locally!")
                    st.rerun()
            
            # Display recent transactions
            st.subheader("📋 Recent Transactions")
            
            # Collect all transactions
            all_transactions = []
            for date_key, entry in data.items():
                if 'transactions' in entry:
                    for transaction in entry['transactions']:
                        transaction['date'] = date_key
                        all_transactions.append(transaction)
            
            # Sort by date (most recent first)
            all_transactions.sort(key=lambda x: x['date'], reverse=True)
            
            if all_transactions:
                # Display last 10 transactions
                for i, transaction in enumerate(all_transactions[:10]):
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 2, 1])
                    
                    with col1:
                        st.write(transaction['date'])
                    with col2:
                        icon = "💰" if transaction['type'] == 'deposit' else "💸"
                        st.write(f"{icon} {transaction['type'].title()}")
                    with col3:
                        color = "green" if transaction['type'] == 'deposit' else "red"
                        st.markdown(f"<span style='color: {color}'>${transaction['amount']:.2f}</span>", unsafe_allow_html=True)
                    with col4:
                        st.write(transaction.get('description', ''))
                    with col5:
                        if st.button("🗑️", key=f"delete_transaction_{i}", help="Delete transaction"):
                            # Remove transaction
                            trans_date = transaction['date']
                            data[trans_date]['transactions'] = [
                                t for t in data[trans_date]['transactions'] 
                                if t['timestamp'] != transaction['timestamp']
                            ]
                            
                            if st.session_state.get('github_connected', False):
                                if st.session_state.github_storage.save_journal_entry(trans_date, data[trans_date], data):
                                    st.success("✅ Transaction deleted!")
                                else:
                                    save_local_data(data)
                                    st.success("💾 Transaction deleted locally!")
                            else:
                                save_local_data(data)
                                st.success("💾 Transaction deleted locally!")
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
            else:
                st.info("No transactions recorded yet. Add your first transaction above.")

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
            tag_data.sort(key=lambda x: x['Total Trades'], reverse=True)
            
            # Display as table
            df_tags = pd.DataFrame(tag_data)
            st.dataframe(df_tags, use_container_width=True)
            
            # Tag insights
            st.subheader("📈 Tag Insights")
            
            # Best performing tags
            best_tags = [item for item in tag_data if item['Wins'] + item['Losses'] >= 3]  # At least 3 completed trades
            if best_tags:
                best_tags.sort(key=lambda x: float(x['Win Rate %'].replace('%', '')), reverse=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🏆 Best Performing Tags:**")
                    for tag in best_tags[:3]:
                        st.markdown(f"• **{tag['Tag']}**: {tag['Win Rate %']} ({tag['Wins']}W/{tag['Losses']}L)")
                
                with col2:
                    st.markdown("**⚠️ Tags to Review:**")
                    worst_tags = [tag for tag in best_tags if float(tag['Win Rate %'].replace('%', '')) < 50]
                    if worst_tags:
                        for tag in worst_tags[:3]:
                            st.markdown(f"• **{tag['Tag']}**: {tag['Win Rate %']} ({tag['Wins']}W/{tag['Losses']}L)")
                    else:
                        st.markdown("• All tags performing well! 🎉")
        else:
            st.info("No tag statistics available. Add some trades with tags to see performance data.")
    
    # Tag management
    st.markdown("---")
    st.subheader("🛠️ Manage Tags")
    
    all_tags = get_all_tags(data)
    
    if all_tags:
        st.write(f"**Current tags ({len(all_tags)}):**")
        
        # Display all tags with delete option
        for i, tag in enumerate(all_tags):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f'<span class="tag-chip">{tag}</span>', unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"delete_tag_btn_{i}", help=f"Delete tag '{tag}'"):
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
        else:
            st.warning("Please enter at least one tag.")

    # Export tag data
    st.markdown("---")
    if st.button("📤 Export Tag Statistics as CSV"):
        if trade_stats and trade_stats['tag_counts']:
            tag_data = []
            for tag, counts in trade_stats['tag_counts'].items():
                completed = counts['wins'] + counts['losses']
                win_rate = (counts['wins'] / completed * 100) if completed > 0 else 0
                
                tag_data.append({
                    'Tag': tag,
                    'Total_Trades': counts['total'],
                    'Wins': counts['wins'],
                    'Losses': counts['losses'],
                    'Pending': counts['total'] - completed,
                    'Win_Rate_Percent': win_rate
                })
            
            df_export = pd.DataFrame(tag_data)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Download Tag Statistics CSV",
                data=csv,
                file_name=f"tag_statistics_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No tag statistics available to export.")

# ======== FOOTER ========
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>📊 Trading Journal v7.5 | Built with Streamlit</p>
    <p>💡 <strong>Remember:</strong> Focus on process over profits. Consistency and discipline lead to long-term success.</p>
</div>
""", unsafe_allow_html=True)
