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
    
    .setup-box {
        background: rgba(0, 20, 40, 0.6);
        border: 2px solid #64ffda;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background: rgba(0, 255, 0, 0.1);
        border: 2px solid #00ff00;
        border-radius: 10px;
        padding: 1rem;
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
        height: 100px;
        margin: 2px;
        border-radius: 5px;
        background: rgba(0,20,40,0.3);
        text-align: center;
        cursor: pointer;
    }
    
    .screenshot-container {
        border: 1px solid #64ffda;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        background: rgba(0,20,40,0.3);
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
            st.error(f"Error getting file: {e}")
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
            st.error(f"Error saving file: {e}")
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
            st.error(f"Error uploading screenshot: {e}")
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

# Initialize session state
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()
if 'page' not in st.session_state:
    st.session_state.page = "🌅 Morning Prep"
if 'github_connected' not in st.session_state:
    st.session_state.github_connected = False
if 'github_storage' not in st.session_state:
    st.session_state.github_storage = GitHubStorage()

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

# Main header
st.markdown('<h1 class="main-header">📊 Trading Journal</h1>', unsafe_allow_html=True)

# Debug info at the top
st.sidebar.markdown("### 🔍 Debug Info")
st.sidebar.write(f"GitHub connected: {st.session_state.github_connected}")

# Test secrets access
try:
    if hasattr(st, 'secrets') and 'github' in st.secrets:
        st.sidebar.write("✅ Secrets found!")
        st.sidebar.write(f"Token starts with: {st.secrets.github.token[:10]}...")
        st.sidebar.write(f"Owner: {st.secrets.github.owner}")
        st.sidebar.write(f"Repo: {st.secrets.github.repo}")
        
        # Manual connection test
        if st.sidebar.button("🔗 Test Connection"):
            test_storage = GitHubStorage()
            with st.sidebar:
                with st.spinner("Testing connection..."):
                    if test_storage.connect(st.secrets.github.token, st.secrets.github.owner, st.secrets.github.repo):
                        st.success("✅ Connection successful!")
                        st.session_state.github_connected = True
                        st.session_state.github_token = st.secrets.github.token
                        st.session_state.repo_owner = st.secrets.github.owner
                        st.session_state.repo_name = st.secrets.github.repo
                        st.session_state.github_storage = test_storage
                        st.rerun()
                    else:
                        st.error("❌ Connection failed!")
                        st.write("Check if repo exists and is public:")
                        st.write(f"https://github.com/{st.secrets.github.owner}/{st.secrets.github.repo}")
        
    else:
        st.sidebar.write("❌ No secrets found")
except Exception as e:
    st.sidebar.write(f"❌ Secrets error: {e}")

st.sidebar.markdown("---")

# GitHub Setup in sidebar
st.sidebar.title("🔗 GitHub Integration")

if not st.session_state.github_connected:
    st.sidebar.markdown("""
    <div class="setup-box">
    <h3>💾 Free GitHub Database Setup</h3>
    <p>Connect to your GitHub repo for free cloud storage!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # GitHub connection form
    with st.sidebar.form("github_setup"):
        st.markdown("**Step 1: Create GitHub Repo**")
        st.markdown("1. Go to [GitHub.com](https://github.com)")
        st.markdown("2. Create a new **public** repository")
        st.markdown("3. Name it: `trading-journal`")
        
        st.markdown("**Step 2: Get Personal Access Token**")
        st.markdown("1. Go to GitHub Settings → Developer settings")
        st.markdown("2. Personal access tokens → Tokens (classic)")
        st.markdown("3. Generate new token with `repo` permissions")
        
        st.markdown("**Step 3: Connect**")
        github_token = st.text_input("GitHub Token", type="password", help="Your personal access token")
        repo_owner = st.text_input("GitHub Username", help="Your GitHub username")
        repo_name = st.text_input("Repository Name", value="trading-journal", help="Name of your repo")
        
        if st.form_submit_button("🔗 Connect to GitHub", type="primary"):
            if github_token and repo_owner and repo_name:
                with st.spinner("Connecting to GitHub..."):
                    if st.session_state.github_storage.connect(github_token, repo_owner, repo_name):
                        st.session_state.github_connected = True
                        # Store credentials in session state
                        st.session_state.github_token = github_token
                        st.session_state.repo_owner = repo_owner
                        st.session_state.repo_name = repo_name
                        st.success("✅ Connected to GitHub!")
                        st.rerun()
                    else:
                        st.error("❌ Connection failed. Check your token and repo details.")
            else:
                st.error("Please fill in all fields")

else:
    # Show connection status
    st.sidebar.markdown("""
    <div class="success-box">
    <h3>✅ GitHub Connected</h3>
    </div>
    """, unsafe_allow_html=True)
    
    repo_url = f"https://github.com/{st.session_state.repo_owner}/{st.session_state.repo_name}"
    st.sidebar.markdown(f"📁 [View Repository]({repo_url})")
    
    screenshots_url = f"{repo_url}/tree/main/screenshots"
    st.sidebar.markdown(f"📸 [View Screenshots]({screenshots_url})")
    
    if st.sidebar.button("🔌 Disconnect"):
        st.session_state.github_connected = False
        st.rerun()

# Sidebar navigation with buttons
st.sidebar.markdown("---")
st.sidebar.title("📋 Navigation")

# Navigation buttons
if st.sidebar.button("🌅 Morning Prep", key="nav_morning", use_container_width=True):
    st.session_state.page = "🌅 Morning Prep"

if st.sidebar.button("📈 Trading Review", key="nav_trading", use_container_width=True):
    st.session_state.page = "📈 Trading Review"

if st.sidebar.button("🌙 Evening Recap", key="nav_evening", use_container_width=True):
    st.session_state.page = "🌙 Evening Recap"

if st.sidebar.button("📊 Calendar View", key="nav_calendar", use_container_width=True):
    st.session_state.page = "📊 Calendar View"

if st.sidebar.button("📚 Historical Analysis", key="nav_history", use_container_width=True):
    st.session_state.page = "📚 Historical Analysis"

page = st.session_state.page

# Date selector
st.sidebar.markdown("---")
selected_date = st.sidebar.date_input(
    "📅 Select Date",
    value=st.session_state.current_date,
    max_value=date.today(),
    key="date_selector"
)

# Update current date when changed
if selected_date != st.session_state.current_date:
    st.session_state.current_date = selected_date

date_key = get_date_key(selected_date)

# Load data (GitHub first, then local fallback)
if st.session_state.github_connected:
    try:
        # Reconnect using stored credentials
        st.session_state.github_storage.connect(
            st.session_state.github_token,
            st.session_state.repo_owner,
            st.session_state.repo_name
        )
        data = st.session_state.github_storage.load_all_journal_data()
        if not data:  # If GitHub is empty, try to load local data
            data = load_local_data()
    except:
        data = load_local_data()
        st.sidebar.warning("⚠️ Using local data (GitHub connection issue)")
else:
    data = load_local_data()

# Initialize date entry if doesn't exist
if date_key not in data:
    data[date_key] = {
        'morning': {},
        'trading': {},
        'evening': {},
        'rules': []
    }

current_entry = data[date_key]

# ======== MORNING PREP PAGE ========
if page == "🌅 Morning Prep":
    st.markdown('<div class="section-header">🌅 Morning Preparation</div>', unsafe_allow_html=True)
    
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
        
        # Screenshot upload for morning prep
        st.subheader("📸 Morning Screenshots")
        morning_screenshot = st.file_uploader(
            "Upload market analysis, news, or prep screenshots",
            type=['png', 'jpg', 'jpeg'],
            key="morning_screenshot",
            help="Upload full-size screenshots - they'll be displayed at full resolution"
        )
        
        # Display existing morning screenshots at full size
        if 'morning_screenshots' in current_entry['morning']:
            for i, screenshot_link in enumerate(current_entry['morning']['morning_screenshots']):
                if screenshot_link:
                    st.markdown(f"**Morning Screenshot {i+1}:**")
                    display_image_full_size(screenshot_link, f"Morning Screenshot {i+1}")
    
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
            if st.session_state.github_connected:
                st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
            save_local_data(data)
            st.rerun()
        
        if st.button("➕ Add Rule"):
            current_entry['rules'].append("New rule - click to edit")
            # Save immediately
            if st.session_state.github_connected:
                st.session_state.github_storage.save_journal_entry(date_key, current_entry, data)
            save_local_data(data)
            st.rerun()
    
    # Save morning data
    if st.button("💾 Save Morning Prep", type="primary"):
        # Handle screenshot upload
        morning_screenshots = current_entry['morning'].get('morning_screenshots', [])
        if morning_screenshot:
            if st.session_state.github_connected:
                # Upload to GitHub
                file_data = morning_screenshot.getvalue()
                screenshot_url = st.session_state.github_storage.upload_screenshot(
                    file_data, f"morning_{morning_screenshot.name}", date_key
                )
                if screenshot_url:
                    morning_screenshots.append(screenshot_url)
                    st.success(f"✅ Screenshot uploaded to GitHub!")
            else:
                # Save locally
                screenshot_path = save_uploaded_file_local(morning_screenshot, date_key, "morning")
                if screenshot_path:
                    morning_screenshots.append(screenshot_path)
        
        current_entry['morning'] = {
            'sleep_quality': sleep_quality,
            'emotional_state': emotional_state,
            'post_night_shift': post_night_shift,
            'checked_news': checked_news,
            'triggers_present': triggers_present,
            'grateful_for': grateful_for,
            'daily_goal': daily_goal,
            'trading_process': trading_process,
            'morning_screenshots': morning_screenshots
        }
        
        # Save to GitHub and local
        if st.session_state.github_connected:
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Morning prep saved to GitHub!")
            else:
                st.warning("⚠️ Saved locally (GitHub error)")
                save_local_data(data)
        else:
            save_local_data(data)
            st.success("💾 Morning prep saved locally!")

# ======== TRADING REVIEW PAGE ========
elif page == "📈 Trading Review":
    st.markdown('<div class="section-header">📈 Post-Trading Review</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance Metrics")
        
        pnl = st.number_input(
            "P&L for the Day ($)",
            value=current_entry['trading'].get('pnl', 0.0),
            format="%.2f"
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
        
        # Screenshot upload for trading
        st.subheader("📸 Trading Screenshots")
        trading_screenshot = st.file_uploader(
            "Upload entry/exit screenshots, charts, or P&L",
            type=['png', 'jpg', 'jpeg'],
            key="trading_screenshot",
            help="Upload full-size screenshots - they'll be displayed at full resolution"
        )
        
        # Display existing trading screenshots at full size
        if 'trading_screenshots' in current_entry['trading']:
            for i, screenshot_link in enumerate(current_entry['trading']['trading_screenshots']):
                if screenshot_link:
                    st.markdown(f"**Trading Screenshot {i+1}:**")
                    display_image_full_size(screenshot_link, f"Trading Screenshot {i+1}")
    
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
        # Handle screenshot upload
        trading_screenshots = current_entry['trading'].get('trading_screenshots', [])
        if trading_screenshot:
            if st.session_state.github_connected:
                # Upload to GitHub
                file_data = trading_screenshot.getvalue()
                screenshot_url = st.session_state.github_storage.upload_screenshot(
                    file_data, f"trading_{trading_screenshot.name}", date_key
                )
                if screenshot_url:
                    trading_screenshots.append(screenshot_url)
                    st.success(f"✅ Screenshot uploaded to GitHub!")
            else:
                # Save locally
                screenshot_path = save_uploaded_file_local(trading_screenshot, date_key, "trading")
                if screenshot_path:
                    trading_screenshots.append(screenshot_path)
        
        current_entry['trading'] = {
            'pnl': pnl,
            'process_grade': process_grade,
            'grade_reasoning': grade_reasoning,
            'general_comments': general_comments,
            'screenshot_notes': screenshot_notes,
            'rule_compliance': rule_compliance,
            'what_could_improve': what_could_improve,
            'tomorrow_focus': tomorrow_focus,
            'trading_screenshots': trading_screenshots
        }
        
        # Save to GitHub and local
        if st.session_state.github_connected:
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Trading review saved to GitHub!")
            else:
                st.warning("⚠️ Saved locally (GitHub error)")
                save_local_data(data)
        else:
            save_local_data(data)
            st.success("💾 Trading review saved locally!")

# ======== EVENING RECAP PAGE ========
elif page == "🌙 Evening Recap":
    st.markdown('<div class="section-header">🌙 Evening Life Recap</div>', unsafe_allow_html=True)
    
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
        if st.session_state.github_connected:
            if st.session_state.github_storage.save_journal_entry(date_key, current_entry, data):
                st.success("✅ Evening recap saved to GitHub!")
            else:
                st.warning("⚠️ Saved locally (GitHub error)")
                save_local_data(data)
        else:
            save_local_data(data)
            st.success("💾 Evening recap saved locally!")

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
    
    # Calendar body with weekly totals
    for week in cal:
        week_cols = st.columns(8)
        week_pnl = 0
        
        for i, day in enumerate(week):
            if day == 0:
                # Empty day
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
                        border_color = "#00ff00" if compliance_rate >= 0.8 else "#ff0000"
                    else:
                        compliance_color = "⚪"
                        border_color = "#666"
                    
                    # Display day with P&L and compliance - clickable
                    pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "gray"
                    
                    # Create clickable day button
                    button_key = f"cal_day_{day_key}"
                    if week_cols[i].button(
                        f"{day} {compliance_color}\n${pnl:.2f}",
                        key=button_key,
                        help=f"Click to view {day_date.strftime('%B %d, %Y')}",
                        use_container_width=True
                    ):
                        st.session_state.current_date = day_date
                        st.session_state.page = "📈 Trading Review"
                        st.rerun()
                else:
                    # Empty day - still clickable
                    empty_button_key = f"cal_empty_{day}_{first_day.month}_{first_day.year}"
                    if week_cols[i].button(
                        f"{day}\n---",
                        key=empty_button_key,
                        help=f"Click to add entry for {day_date.strftime('%B %d, %Y')}",
                        use_container_width=True
                    ):
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
        st.markdown("💡 **Click any day to view/edit entry**")

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
            
            # Detailed entries with ALL journal questions
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
                            if 'post_night_shift' in morning:
                                st.write(f"**Post Night Shift:** {'Yes' if morning['post_night_shift'] else 'No'}")
                            if 'checked_news' in morning:
                                st.write(f"**Checked News:** {'Yes' if morning['checked_news'] else 'No'}")
                        
                        with col2:
                            if 'daily_goal' in morning and morning['daily_goal']:
                                st.write(f"**Daily Goal:** {morning['daily_goal']}")
                            if 'trading_process' in morning and morning['trading_process']:
                                st.write(f"**Trading Process:** {morning['trading_process']}")
                        
                        if 'triggers_present' in morning and morning['triggers_present']:
                            st.write(f"**Triggers/Concerns:** {morning['triggers_present']}")
                        if 'grateful_for' in morning and morning['grateful_for']:
                            st.write(f"**Grateful For:** {morning['grateful_for']}")
                        
                        # Morning Screenshots at full size
                        if 'morning_screenshots' in morning and morning['morning_screenshots']:
                            st.write("**Morning Screenshots:**")
                            for j, screenshot_link in enumerate(morning['morning_screenshots']):
                                if screenshot_link:
                                    display_image_full_size(screenshot_link, f"Morning Screenshot {j+1}")
                    
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
                            if 'rule_compliance' in trading:
                                compliance = trading['rule_compliance']
                                if compliance:
                                    compliance_rate = sum(compliance.values()) / len(compliance) * 100
                                    st.write(f"**Rule Compliance:** {compliance_rate:.1f}%")
                        
                        with col2:
                            if 'grade_reasoning' in trading and trading['grade_reasoning']:
                                st.write(f"**Grade Reasoning:** {trading['grade_reasoning']}")
                            if 'general_comments' in trading and trading['general_comments']:
                                st.write(f"**General Comments:** {trading['general_comments']}")
                        
                        if 'screenshot_notes' in trading and trading['screenshot_notes']:
                            st.write(f"**Screenshot/Entry Notes:** {trading['screenshot_notes']}")
                        if 'what_could_improve' in trading and trading['what_could_improve']:
                            st.write(f"**Could Improve:** {trading['what_could_improve']}")
                        if 'tomorrow_focus' in trading and trading['tomorrow_focus']:
                            st.write(f"**Tomorrow Focus:** {trading['tomorrow_focus']}")
                        
                        # Trading Screenshots at full size
                        if 'trading_screenshots' in trading and trading['trading_screenshots']:
                            st.write("**Trading Screenshots:**")
                            for j, screenshot_link in enumerate(trading['trading_screenshots']):
                                if screenshot_link:
                                    display_image_full_size(screenshot_link, f"Trading Screenshot {j+1}")
                    
                    # Evening Section
                    if 'evening' in entry and entry['evening']:
                        st.markdown("### 🌙 Evening Recap")
                        evening = entry['evening']
                        
                        if 'personal_recap' in evening and evening['personal_recap']:
                            st.write(f"**Personal Recap:** {evening['personal_recap']}")
                        if 'family_highlights' in evening and evening['family_highlights']:
                            st.write(f"**Family Highlights:** {evening['family_highlights']}")
                        if 'personal_wins' in evening and evening['personal_wins']:
                            st.write(f"**Personal Wins:** {evening['personal_wins']}")
                        if 'tomorrow_intentions' in evening and evening['tomorrow_intentions']:
                            st.write(f"**Tomorrow Intentions:** {evening['tomorrow_intentions']}")
                    
                    # Rules for this day
                    if 'rules' in entry and entry['rules']:
                        st.markdown("### 📋 Trading Rules")
                        for i, rule in enumerate(entry['rules']):
                            if rule.strip():
                                compliance_status = "✅" if entry.get('trading', {}).get('rule_compliance', {}).get(f"rule_{i}", False) else "❌"
                                st.write(f"{compliance_status} {rule}")
        else:
            st.info("No trading data found for the selected date range.")

# Sidebar stats
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
    
    # Calculate compliance rate
    compliance_days = 0
    total_trading_days = 0
    
    for entry in period_data.values():
        rule_compliance = entry.get('trading', {}).get('rule_compliance', {})
        if rule_compliance:  # Only count days with trading data
            total_trading_days += 1
            compliance_rate = sum(rule_compliance.values()) / len(rule_compliance)
            if compliance_rate >= 0.8:
                compliance_days += 1
    
    overall_compliance = (compliance_days / total_trading_days * 100) if total_trading_days > 0 else 0
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
    st.metric("Rules", f"{compliance_5:.0f}%")

st.sidebar.markdown("**📊 Last 30 Days**")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("P&L", f"${pnl_30:.2f}")
with col2:
    st.metric("Rules", f"{compliance_30:.0f}%")

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
        if st.session_state.github_connected:
            for date_key, entry in imported_data.items():
                st.session_state.github_storage.save_journal_entry(date_key, entry, data)
        save_local_data(data)
        
        st.sidebar.success("Data imported successfully!")
        st.rerun()
    except:
        st.sidebar.error("Error importing data")

# Show setup instructions if not connected
if not st.session_state.github_connected:
    st.markdown("---")
    st.markdown("""
    ## 🚀 **Complete GitHub Setup Guide**
    
    ### **🎯 Why GitHub? (100% Free!)**
    - ✅ **No costs** - completely free for public repos
    - ✅ **Unlimited storage** for text data and images
    - ✅ **Access anywhere** - works with Streamlit Cloud
    - ✅ **Version history** - never lose data
    - ✅ **No API limits** - unlimited usage
    
    ### **📋 Step-by-Step Setup:**
    
    **1. Create GitHub Repository**
    - Go to [GitHub.com](https://github.com) and sign in
    - Click "New Repository" 
    - Name: `trading-journal`
    - Set to **Public** (required for free)
    - Click "Create repository"
    
    **2. Get Personal Access Token**
    - Go to GitHub Settings → Developer settings
    - Personal access tokens → Tokens (classic)
    - Click "Generate new token (classic)"
    - Give it a name: "Trading Journal"
    - Select scopes: **✅ repo** (full control)
    - Click "Generate token"
    - **Copy the token** (you won't see it again!)
    
    **3. Connect Above**
    - Paste your token, username, and repo name
    - Click "🔗 Connect to GitHub"
    
    ### **📸 Full-Size Screenshots Fixed!**
    - Images now display at **full resolution**
    - **GitHub stores** your screenshots permanently
    - **Click to expand** for detailed viewing
    - **Professional presentation** of your trading data
    
    ### **🎉 After Setup You Get:**
    - **Automatic saving** to GitHub on every entry
    - **Professional repository** with all your trading data
    - **Screenshot gallery** organized by date
    - **Access from any device** via Streamlit Cloud
    - **Permanent backup** with version history
    
    *Once connected, your trading journal will be professional-grade and accessible anywhere!*
    """)
