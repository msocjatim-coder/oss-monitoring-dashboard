import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "your-supabase-url")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-key")

# App Configuration
APP_TITLE = "OSS Telkom Monitoring Dashboard"
APP_ICON = "📊"
APP_LAYOUT = "wide"
THEME_COLOR = "#6366f1"  # Indigo modern