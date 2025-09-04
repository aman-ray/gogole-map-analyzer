"""Unit tests for logging functionality."""

import unittest
import tempfile
import os
import logging
from pathlib import Path
from datetime import datetime
from tradescout.logging_config import TradescoutLogger, setup_logging, get_logger, info, debug, warning, error


class TestLoggingConfig(unittest.TestCase):
    """Test the logging configuration module."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        # Clear any existing logger instances
        TradescoutLogger._instance = None
        TradescoutLogger._initialized = False
        # Clear logging handlers
        logger = logging.getLogger('tradescout')
        logger.handlers.clear()
        
    def test_singleton_logger(self):
        """Test that TradescoutLogger is a singleton."""
        logger1 = TradescoutLogger()
        logger2 = TradescoutLogger()
        self.assertIs(logger1, logger2)
    
    def test_log_directory_creation(self):
        """Test that log directory is created."""
        log_dir = os.path.join(self.test_dir, "test_logs")
        setup_logging(log_dir=log_dir)
        
        self.assertTrue(os.path.exists(log_dir))
        self.assertTrue(os.path.isdir(log_dir))
    
    def test_log_file_creation(self):
        """Test that log file is created with correct naming."""
        log_dir = os.path.join(self.test_dir, "test_logs")
        setup_logging(log_dir=log_dir)
        
        # Check if log file exists
        today = datetime.now().strftime('%Y-%m-%d')
        expected_log_file = os.path.join(log_dir, f"tradescout_{today}.log")
        
        # Log something to ensure file is created
        logger = get_logger()
        logger.info("Test message")
        
        self.assertTrue(os.path.exists(expected_log_file))
    
    def test_log_levels(self):
        """Test different log levels."""
        log_dir = os.path.join(self.test_dir, "test_logs")
        setup_logging(log_level="DEBUG", log_dir=log_dir)
        
        # Test convenience functions
        debug("Debug message")
        info("Info message")
        warning("Warning message")
        error("Error message")
        
        # Read log file
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f"tradescout_{today}.log")
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn("DEBUG", log_content)
        self.assertIn("INFO", log_content)
        self.assertIn("WARNING", log_content)
        self.assertIn("ERROR", log_content)
        self.assertIn("Debug message", log_content)
        self.assertIn("Info message", log_content)
        self.assertIn("Warning message", log_content)
        self.assertIn("Error message", log_content)
    
    def test_logger_with_name(self):
        """Test getting logger with specific name."""
        setup_logging(log_dir=self.test_dir)
        
        logger = get_logger('test_module')
        self.assertEqual(logger.name, 'tradescout.test_module')
    
    def test_log_and_print_functionality(self):
        """Test the log_and_print function."""
        log_dir = os.path.join(self.test_dir, "test_logs")
        setup_logging(log_dir=log_dir)
        
        # Test with print_msg=False (should not print to console but should log)
        info("Test message", print_msg=False)
        
        # Read log file to verify message was logged
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f"tradescout_{today}.log")
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn("Test message", log_content)
        self.assertIn("INFO", log_content)
    
    def test_file_rotation_setup(self):
        """Test that file rotation is properly configured."""
        log_dir = os.path.join(self.test_dir, "test_logs")
        setup_logging(log_dir=log_dir)
        
        logger = get_logger()
        
        # Check that TimedRotatingFileHandler is configured
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.TimedRotatingFileHandler)]
        self.assertEqual(len(file_handlers), 1)
        
        file_handler = file_handlers[0]
        self.assertEqual(file_handler.when, 'MIDNIGHT')
        self.assertEqual(file_handler.interval, 86400)  # 1 day in seconds
        self.assertEqual(file_handler.backupCount, 30)
    
    def test_console_handler_configuration(self):
        """Test that console handler is properly configured."""
        setup_logging(log_dir=self.test_dir)
        
        logger = get_logger()
        
        # Check that StreamHandler is configured for warnings and errors
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.TimedRotatingFileHandler)]
        self.assertGreaterEqual(len(stream_handlers), 1)
        
        console_handler = stream_handlers[0]
        self.assertEqual(console_handler.level, logging.WARNING)


def run_logging_tests():
    """Run all logging tests."""
    print("🧪 Running Logging Tests")
    print("=" * 40)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLoggingConfig)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All logging tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False


if __name__ == "__main__":
    run_logging_tests()