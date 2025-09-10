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
import uuid  # NEW: Added for trade IDs

# Set page config
st.set_page_config(
    page_title="Trading Journal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize theme in session state
if 'theme' not in st.session_state:
    st.session_state.theme = "dark"

# Theme selector at the very top
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    theme_option = st.selectbox(
        "🎨 Theme",
        options=["dark", "light"],
        index=0 if st.session_state.theme == "dark" else 1,
        key="theme_selector"
    )
    
    if theme_option != st.session_state.theme:
        st.session_state.theme = theme_option
        st.rerun()

# Apply theme-specific CSS
def get_theme_css(theme):
    if theme == "dark":
        return """
<style>
    /* DARK THEME - Override Streamlit's core elements */
    .stApp {
        background: linear-gradient(180deg, #0e1117 0%, #1a1a2e 100%) !important;
    }
    
    /* Main content background */
    .main .block-container {
        background: rgba(14, 17, 23, 0.9) !important;
        padding-top: 2rem !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1q8dd3e {
        background: linear-gradient(180deg, #16213e 0%, #0f1419 100%) !important;
    }
    
    /* Override all text colors */
    .stApp, .stApp * {
        color: #fafafa !important;
    }
    
    /* Selectbox and input styling */
    .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #fafafa !important;
        border: 1px solid #64ffda !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #fafafa !important;
        border: 1px solid #64ffda !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: rgba(100, 255, 218, 0.1) !important;
        color: #64ffda !important;
        border: 1px solid #64ffda !important;
    }
    
    .stButton > button:hover {
        background-color: rgba(100, 255, 218, 0.2) !important;
        color: #ffffff !important;
    }
    
    /* Metrics styling */
    .metric-container {
        background-color: rgba(0, 20, 40, 0.6) !important;
        border: 1px solid #64ffda !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
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
        color: #64ffda !important;
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
</style>
"""
    else:  # light theme
        return """
<style>
    /* LIGHT THEME - Override Streamlit's core elements */
    .stApp {
        background: linear-gradient(180deg, #ffffff 0%, #f0f2f6 100%) !important;
    }
    
    /* Main content background */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95) !important;
        padding-top: 2rem !important;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1q8dd3e {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%) !important;
        border-right: 1px solid #dee2e6 !important;
    }
    
    /* Override text colors for light theme */
    .stApp, .stApp * {
        color: #212529 !important;
    }
    
    /* Selectbox and input styling */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #212529 !important;
        border: 1px solid #1976d2 !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background-color: #ffffff !important;
        color: #212529 !important;
        border: 1px solid #1976d2 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: rgba(25, 118, 210, 0.1) !important;
        color: #1976d2 !important;
        border: 1px solid #1976d2 !important;
    }
    
    .stButton > button:hover {
        background-color: rgba(25, 118, 210, 0.2) !important;
        color: #0d47a1 !important;
    }
    
    /* Primary button styling */
    .stButton > button[kind="primary"] {
        background-color: #1976d2 !important;
        color: #ffffff !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #0d47a1 !important;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(45deg, #1976d2, #1565c0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .section-header {
        font-size: 1.5rem;
        color: #1976d2 !important;
        border-bottom: 2px solid #1976d2;
        padding-bottom: 0.5rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #1976d2;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .calendar-day {
        border: 2px solid #ccc;
        padding: 10px;
        height: 80px;
        margin: 2px;
        border-radius: 5px;
        background: rgba(255,255,255,0.9);
        text-align: center;
        cursor: pointer;
        color: #333 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .trade-row {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.2rem 0;
        color: #333 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .balance-display {
        background: rgba(255, 255, 255, 0.95);
        border: 2px solid #1976d2;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .balance-amount {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1976d2;
    }
    
    .trade-card {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid #1976d2;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        color: #333 !important;
    }
    
    .tag-chip {
        display: inline-block;
        background: rgba(25, 118, 210, 0.1);
        border: 1px solid #1976d2;
        border-radius: 15px;
        padding: 0.2rem 0.8rem;
        margin: 0.2rem;
        font-size: 0.8rem;
        color: #1976d2;
    }
    
    .win-tag {
        background: rgba(46, 125, 50, 0.1);
        border-color: #2e7d32;
        color: #2e7d32;
    }
    
    .loss-tag {
        background: rgba(211, 47, 47, 0.1);
        border-color: #d32f2f;
        color: #d32f2f;
    }
    
    .pending-tag {
        background: rgba(245, 124, 0, 0.1);
        border-color: #f57c00;
        color: #f57c00;
    }
    
    /* Fix sidebar text colors */
    .css-1d391kg *, .css-1q8dd3e * {
        color: #212529 !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.5) !important;
        border: 1px solid #dee2e6 !important;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        background-color: #ffffff !important;
    }
</style>
"""

# Apply the selected theme CSS
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

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

# NEW TRADE DAY FUNCTIONS
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
    pending_trades = [t for t in all_trades if t.get('outcome') == 'pending']
    
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
        'pending_trades': len(pending_trades),
        'win_rate': (len(win_trades) / (len(win_trades) + len(loss_trades)) * 100) if (len(win_trades) + len(loss_trades)) > 0 else 0,
        'tag_counts': tag_counts,
        'tag_win_rates': tag_win_rates,
        'recent_trades': sorted(all_trades, key=lambda x: x['timestamp'], reverse=True)[:10]
    }

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
if 'trade_analysis' not in st.session_state:
    st.session_state.trade_analysis = None
if 'trade_data' not in st.session_state:
    st.session_state.trade_data = None
if 'last_analysis_date' not in st.session_state:
    st.session_state.last_analysis_date = None
if 'trade_log_action' not in st.session_state:
    st.session_state.trade_log_action = None

# Main header - UPDATED VERSION TO 7.4
theme_emoji = "🌙" if st.session_state.theme == "dark" else "☀️"
st.markdown(f'<h1 class="main-header">{theme_emoji} Trading Journal v7.4</h1>', unsafe_allow_html=True)

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
    balance_color = "#00ff88" if balance_change > 0 else "#ff4444" if balance_change < 0 else ("#64ffda" if st.session_state.theme == "dark" else "#1976d2")
    change_symbol = "↗" if balance_change > 0 else "↘" if balance_change < 0 else "→"
    
    st.sidebar.markdown(f"""
    <div class="balance-display">
        <div style="font-size: 1rem; color: {"#aaa" if st.session_state.theme == "dark" else "#666"};">Current Balance</div>
        <div class="balance-amount" style="color: {balance_color};">
            ${current_balance:,.2f} {change_symbol}
        </div>
        <div style="font-size: 0.9rem; color: {"#aaa" if st.session_state.theme == "dark" else "#666"};">
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

# UPDATED SIDEBAR NAVIGATION - ADDED TRADE DAY AND TAG MANAGEMENT
st.sidebar.markdown("---")
st.sidebar.title("📋 Navigation")

# Navigation buttons - CALENDAR VIEW FIRST, THEN TRADE DAY!
if st.sidebar.button("📊 Calendar View", key="nav_calendar", use_container_width=True):
    st.session_state.page = "📊 Calendar View"

if st.sidebar.button("🌅 Morning Prep", key="nav_morning", use_container_width=True):
    st.session_state.page = "🌅 Morning Prep"

# NEW: TRADE DAY NAVIGATION BUTTON
if st.sidebar.button("📈 Trade Day", key="nav_trade_day", use_container_width=True):
    st.session_state.page = "📈 Trade Day"

if st.sidebar.button("📈 Trading Review", key="nav_trading", use_container_width=True):
    st.session_state.page = "📈 Trading Review"

if st.sidebar.button("🌙 Evening Recap", key="nav_evening", use_container_width=True):
    st.session_state.page = "🌙 Evening Recap"

if st.sidebar.button("📊 Trade Log Analysis", key="nav_tradelog", use_container_width=True):
    st.session_state.page = "📊 Trade Log Analysis"

if st.sidebar.button("📚 Historical Analysis", key="nav_history", use_container_width=True):
    st.session_state.page = "📚 Historical Analysis"

# Enhanced Balance History Page
if st.sidebar.button("💰 Balance & Ledger", key="nav_balance_history", use_container_width=True):
    st.session_state.page = "💰 Balance & Ledger"

# NEW: Tag Management Button
if st.sidebar.button("🏷️ Tag Management", key="nav_tag_management", use_container_width=True):
    st.session_state.page = "🏷️ Tag Management"

page = st.session_state.page

date_key = get_date_key(selected_date)

# UPDATED: Initialize date entry if doesn't exist - ADDED TRADE_DAY
if date_key not in data:
    data[date_key] = {
        'morning': {},
        'trade_day': {},  # NEW: Initialize trade_day section
        'trading': {},
        'evening': {},
        'rules': []
    }

current_entry = data[date_key]

# Note: Rest of the code remains the same as the original v7.4, just with theme-aware styling...
# (I'll include a key section to show the structure, but the full code would be too long for this response)

# ======== CALENDAR VIEW PAGE EXAMPLE ========
if page == "📊 Calendar View":
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
                    '<div class="calendar-day" style="padding: 10px; height: 80px; opacity: 0.3; display: flex; align-items: center; justify-content: center;">&nbsp;</div>', 
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
                    bg_color = "rgba(0,20,40,0.3)" if st.session_state.theme == "dark" else "rgba(255,255,255,0.9)"
                    
                    # Create clickable day button with fixed height
                    button_key = f"cal_day_{day_key}"
                    week_cols[i].markdown(f'''
                    <div style="border: 2px solid #333; padding: 10px; height: 80px; background: {bg_color}; 
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
                    bg_color = "rgba(0,0,0,0.2)" if st.session_state.theme == "dark" else "rgba(240,240,240,0.5)"
                    
                    week_cols[i].markdown(f'''
                    <div style="border: 2px solid #333; padding: 10px; height: 80px; background: {bg_color}; 
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

# The rest of the pages would follow the same pattern with theme-aware styling...
# This includes all other pages: Morning Prep, Trade Day, Trading Review, Evening Recap, 
# Trade Log Analysis, Historical Analysis, Balance & Ledger, and Tag Management

# Sidebar stats remain the same but with theme-aware colors in the CSS
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Quick Stats")

# Rest of the sidebar stats code remains the same...

# Export/Import functionality at bottom of sidebar
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
