import sys
import threading
import time

import config
import monitors
import privacy
import logger_setup

def main():
    # Handle data purge command line argument: python main.py --purge
    if len(sys.argv) > 1 and sys.argv[1] == "--purge":
        privacy.purge_collected_data()
        return

    # 1. Require explicit user consent
    if not privacy.request_user_consent():
        sys.exit(0)

    # 2. Initialize output directories
    config.init_directories()

    # 3. Setup application logger
    logger = logger_setup.get_logger()
    logger.info("Initializing System Activity Monitor...")
    logger.info(f"Target output directory: {config.OUTPUT_DIR}")

    # 4. Create stop event for coordinated thread shutdown
    stop_event = threading.Event()

    # 5. Define monitor threads
    threads = [
        threading.Thread(target=monitors.run_screenshot_monitor, args=(stop_event,), name="ScreenshotThread"),
        threading.Thread(target=monitors.run_clipboard_monitor,  args=(stop_event,), name="ClipboardThread"),
        threading.Thread(target=monitors.run_keyboard_monitor,   args=(stop_event,), name="KeyboardThread"),
    ]

    if config.ENABLE_AUDIO:
        threads.append(
            threading.Thread(target=monitors.run_audio_monitor, args=(stop_event,), name="AudioThread")
        )

    logger.info("Starting background monitor threads...")
    for t in threads:
        t.start()

    print("\n" + "=" * 60)
    print("STATUS: Monitoring ACTIVE (Press CTRL+C anytime to Stop)")
    print("=" * 60 + "\n")

    # 6. Wait for shutdown signal (CTRL+C)
    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received (CTRL+C). Initiating coordinated stop...")
    finally:
        # Signal all threads to exit
        stop_event.set()

        # Join threads with timeout
        for t in threads:
            t.join(timeout=3)
            logger.info(f"Thread '{t.name}' terminated successfully.")

        logger.info("System Activity Monitor stopped cleanly. All files saved.")
        print("\n[OK] Application stopped. Check output/logs/system_monitor.log for detailed event history.")
        print("Tip: Run 'python main.py --purge' to wipe test data anytime.\n")

if __name__ == "__main__":
    main()
