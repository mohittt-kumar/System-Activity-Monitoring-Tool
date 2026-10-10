import os
import re
import shutil
import config

# =====================================================================
# 1. EXPLICIT CONSENT PROMPT
# =====================================================================
def request_user_consent():
    """
    Displays a clear, transparent consent disclaimer.
    Requires the user to type 'y' or 'yes' before any monitoring starts.
    If consent is denied, exits the application cleanly.
    """
    print("\n" + "=" * 60)
    print("                 USER CONSENT & PRIVACY NOTICE               ")
    print("=" * 60)
    print("This application is a System Activity Monitor designed for:")
    print("  * Computer-based exam proctoring")
    print("  * Personal workstation productivity logging")
    print("  * Authorized system audit trails")
    print("\nWhen active, it will record:")
    print("  * Periodic screenshots of your display")
    print("  * Keystrokes typed on your keyboard")
    print("  * Text copied to your clipboard")
    if config.ENABLE_AUDIO:
        print("  * Short audio clips from your microphone")
    print("\nAll data is stored LOCALLY in the 'output/' directory.")
    print("No data is uploaded or transmitted over the internet.")
    print("=" * 60)

    choice = input("Do you explicitly consent to start monitoring? (y/N): ").strip().lower()

    if choice in ["y", "yes"]:
        print("[OK] Consent granted by user. Initializing monitors...\n")
        return True
    else:
        print("[X] Consent was NOT granted. Application will not start.")
        return False


# =====================================================================
# 2. SENSITIVE DATA MASKING (PRIVACY-BY-DESIGN)
# =====================================================================
def mask_sensitive_text(text):
    """
    Scans text for sensitive patterns and masks them before saving to disk.
    Masks:
      * Credit Card Numbers (13-16 consecutive digits)
      * Common password markers (e.g., 'password: 1234' -> 'password: [REDACTED]')
    """
    if not text:
        return text

    # 1. Mask potential Credit Card / 16-digit card numbers
    card_pattern = r"\b(?:\d{4}[ -]?){3}\d{4}\b"
    text = re.sub(card_pattern, "[REDACTED_CARD_NUMBER]", text)

    # 2. Mask passwords entered in common formats like 'password = secret' or 'pwd: 12345'
    password_pattern = r"(?i)\b(password|passwd|pwd|secret|api_key|token)\s*[:=]\s*\S+"
    text = re.sub(password_pattern, r"\1: [REDACTED_PASSWORD]", text)

    return text


# =====================================================================
# 3. DATA PURGE UTILITY (RIGHT TO ERASURE / GDPR COMPLIANCE)
# =====================================================================
def purge_collected_data():
    """
    Deletes all files inside output directories to respect user privacy
    and give the user full control to clear their test data.
    """
    print("\n[!] Purging all collected monitoring data...")
    count = 0

    target_dirs = [
        config.SCREENSHOT_DIR,
        config.LOG_DIR,
        config.CLIPBOARD_DIR,
        config.RECORDING_DIR
    ]

    for directory in target_dirs:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        count += 1
                except Exception as e:
                    print(f"Could not remove {filename}: {e}")

    print(f"[OK] Data purge complete. Removed {count} collected file(s).")
