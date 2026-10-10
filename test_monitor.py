import os
import unittest
import threading
import time

import config
import privacy
import monitors

class TestSystemMonitor(unittest.TestCase):
    """
    Automated Unit Tests for System Activity Monitor.
    Verifies configuration, privacy filtering, thread shutdown, and data retention.
    """

    def test_config_defaults(self):
        """Test 1: Verify privacy-by-design defaults in config."""
        # Audio MUST be disabled by default for privacy
        self.assertFalse(config.ENABLE_AUDIO, "Audio should be disabled by default for privacy.")
        # Check reasonable interval limits
        self.assertGreater(config.SCREENSHOT_INTERVAL, 0, "Screenshot interval must be positive.")
        self.assertGreater(config.CLIPBOARD_INTERVAL, 0, "Clipboard interval must be positive.")
        # Check base directory is valid
        self.assertTrue(os.path.isdir(config.BASE_DIR), "BASE_DIR should point to a valid directory.")

    def test_privacy_card_masking(self):
        """Test 2: Verify that credit card numbers are masked."""
        sample_text = "Transaction details: Card 4111-2222-3333-4444 approved."
        sanitized = privacy.mask_sensitive_text(sample_text)
        self.assertNotIn("4111-2222-3333-4444", sanitized)
        self.assertIn("[REDACTED_CARD_NUMBER]", sanitized)

    def test_privacy_password_masking(self):
        """Test 3: Verify that password entries are masked."""
        sample_text = "Logging into database with password: SecretMasterKey123!"
        sanitized = privacy.mask_sensitive_text(sample_text)
        self.assertNotIn("SecretMasterKey123!", sanitized)
        self.assertIn("[REDACTED_PASSWORD]", sanitized)

    def test_privacy_non_sensitive_text_preserved(self):
        """Test 4: Verify normal text is not altered by privacy masking."""
        normal_text = "Python multithreading tutorial for exam preparation."
        sanitized = privacy.mask_sensitive_text(normal_text)
        self.assertEqual(normal_text, sanitized)

    def test_thread_event_immediate_shutdown(self):
        """Test 5: Verify that threading.Event.wait() unblocks immediately upon stop signal."""
        stop_event = threading.Event()
        start_time = time.time()

        # In a background thread, trigger stop_event after 0.2 seconds
        def trigger_stop():
            time.sleep(0.2)
            stop_event.set()

        t = threading.Thread(target=trigger_stop)
        t.start()

        # stop_event.wait(5.0) should NOT wait 5 seconds; it should wake up around 0.2s
        woke_up_early = stop_event.wait(timeout=5.0)
        elapsed = time.time() - start_time
        t.join()

        self.assertTrue(woke_up_early, "stop_event.wait() should return True when signaled.")
        self.assertLess(elapsed, 1.5, f"Thread should unblock immediately, took {elapsed:.2f}s instead.")

    def test_data_purge_cleans_directory(self):
        """Test 6: Verify that privacy.purge_collected_data() deletes files safely."""
        config.init_directories()
        # Create a dummy test file
        test_file = os.path.join(config.LOG_DIR, "test_dummy_log.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("temporary test data")

        self.assertTrue(os.path.exists(test_file), "Dummy test file should exist before purge.")

        # Run purge
        privacy.purge_collected_data()

        # Verify test file was deleted
        self.assertFalse(os.path.exists(test_file), "Dummy file should be deleted by purge.")

if __name__ == "__main__":
    unittest.main()
