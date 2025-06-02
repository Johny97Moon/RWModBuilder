"""
Спрощена система логування для CustomTkinter версії
Без PyQt6 залежностей
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
import threading


class SimpleLogger:
    """Спрощений logger без PyQt залежностей"""
    
    def __init__(self, name: str = "RimWorldModBuilder"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Видаляємо існуючі handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Налаштування обробників логування"""
        # Консольний handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Файловий handler
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_filename = f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = os.path.join(log_dir, log_filename)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Форматування
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def get_logger(self):
        """Отримати logger"""
        return self.logger
    
    def debug(self, message: str):
        """Debug повідомлення"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Info повідомлення"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Warning повідомлення"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Error повідомлення"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Critical повідомлення"""
        self.logger.critical(message)


# Глобальний екземпляр logger
_logger_instance: Optional[SimpleLogger] = None
_logger_lock = threading.Lock()


def get_logger_instance() -> SimpleLogger:
    """Отримати глобальний екземпляр logger"""
    global _logger_instance
    
    if _logger_instance is None:
        with _logger_lock:
            if _logger_instance is None:
                _logger_instance = SimpleLogger()
    
    return _logger_instance


# Заглушки для сумісності з старим кодом
class LogViewerDialog:
    def __init__(self, parent=None, log_content: str = ""):
        _ = parent  # Заглушка для unused parameter
        print(f"Log: {log_content}")

class StatusBarLogger:
    def __init__(self, status_bar=None):
        _ = status_bar  # Заглушка для unused parameter
        self.logger = get_logger_instance().get_logger()

    def log_to_status(self, message: str, level: str = "info"):
        getattr(self.logger, level, self.logger.info)(message)
