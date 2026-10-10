import os

# =====================================================================
# 1. BASE DIRECTORY (PORTABLE RELATIVE PATH)
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# All captured data and logs will be organized inside 'output'
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")
LOG_DIR        = os.path.join(OUTPUT_DIR, "logs")
CLIPBOARD_DIR  = os.path.join(OUTPUT_DIR, "clipboard")
RECORDING_DIR  = os.path.join(OUTPUT_DIR, "recordings")

# File paths
KEYLOG_FILE      = os.path.join(LOG_DIR, "keystrokes.txt")
CLIPBOARD_FILE   = os.path.join(CLIPBOARD_DIR, "clipboard_history.txt")
APP_LOG_FILE     = os.path.join(LOG_DIR, "system_monitor.log")


# =====================================================================
# 2. LOGGING CONFIGURATION
# =====================================================================
# 1 Megabyte max per log file, keeping 3 rotated backups
MAX_LOG_BYTES    = 1 * 1024 * 1024  
LOG_BACKUP_COUNT = 3


# =====================================================================
# 3. MONITORING INTERVALS & SETTINGS
# =====================================================================
SCREENSHOT_INTERVAL = 10      # Take a screenshot every 10 seconds
CLIPBOARD_INTERVAL  = 5       # Check clipboard every 5 seconds

# Privacy-by-design: Audio is disabled by default
ENABLE_AUDIO        = False   # Set to True only if explicitly needed
AUDIO_DURATION      = 5       # Record audio clips of 5 seconds
AUDIO_SAMPLE_RATE   = 44100   # Standard CD quality audio sampling rate
AUDIO_CHANNELS      = 1       # Mono channel


# =====================================================================
# 4. DIRECTORY INITIALIZATION FUNCTION
# =====================================================================
def init_directories():
    """Creates all output directories if they do not exist."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(CLIPBOARD_DIR, exist_ok=True)
    if ENABLE_AUDIO:
        os.makedirs(RECORDING_DIR, exist_ok=True)
