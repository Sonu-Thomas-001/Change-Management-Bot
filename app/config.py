import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change_this_to_a_random_secret_key")
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    
    # ServiceNow Config
    SERVICENOW_INSTANCE = os.environ.get("SERVICENOW_INSTANCE")
    SERVICENOW_USER = os.environ.get("SERVICENOW_USER")
    SERVICENOW_PASSWORD = os.environ.get("SERVICENOW_PASSWORD")
    
    # File Paths
    LOG_FILE = "query_logs.csv"
    FEEDBACK_FILE = "feedback_logs.csv"
    CALENDAR_FILE = "change_calendar.csv"
    ESCALATION_FILE = "escalation_logs.csv"
    
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
