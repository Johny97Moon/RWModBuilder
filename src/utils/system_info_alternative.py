#!/usr/bin/env python3
"""
Альтернатива psutil для системної інформації
Використовує тільки стандартні модулі Python
"""

import os
import sys
import platform
import subprocess
import shutil
import time
import threading
from typing import Dict, Optional, List, Tuple
from pathlib import Path


class SystemInfoAlternative:
    """Альтернатива psutil для системної інформації"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.cache = {}
        self.cache_timeout = 5  # секунд
    
    def get_memory_info(self) -> Dict:
        """Отримання інформації про пам'ять"""
        cache_key = "memory_info"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        memory_info = {
            "total": 0,
            "available": 0,
            "used": 0,
            "percent": 0,
            "unit": "bytes"
        }
        
        try:
            if self.platform == "windows":
                memory_info = self._get_windows_memory()
            elif self.platform == "linux":
                memory_info = self._get_linux_memory()
            elif self.platform == "darwin":  # macOS
                memory_info = self._get_macos_memory()
            else:
                memory_info = self._get_generic_memory()
                
        except Exception as e:
            print(f"Помилка отримання інформації про пам'ять: {e}")
        
        self._cache_data(cache_key, memory_info)
        return memory_info
    
    def get_disk_usage(self, path: str = ".") -> Dict:
        """Використання пам'яті диска"""
        try:
            # Використання shutil.disk_usage (Python 3.3+)
            total, used, free = shutil.disk_usage(path)
            
            return {
                "total": total,
                "used": used,
                "free": free,
                "percent": (used / total * 100) if total > 0 else 0,
                "path": os.path.abspath(path),
                "unit": "bytes"
            }
            
        except Exception as e:
            print(f"Помилка отримання інформації про диск: {e}")
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "percent": 0,
                "path": path,
                "unit": "bytes"
            }
    
    def get_cpu_info(self) -> Dict:
        """Інформація про процесор"""
        cache_key = "cpu_info"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        cpu_info = {
            "processor": platform.processor() or "Unknown",
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
            "cpu_count": os.cpu_count() or 1,
            "cpu_usage": self._get_cpu_usage(),
            "frequency": self._get_cpu_frequency()
        }
        
        self._cache_data(cache_key, cpu_info)
        return cpu_info
    
    def get_system_info(self) -> Dict:
        """Загальна системна інформація"""
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "hostname": platform.node(),
            "username": os.getlogin() if hasattr(os, 'getlogin') else "Unknown"
        }
    
    def get_process_info(self) -> Dict:
        """Інформація про поточний процес"""
        try:
            import psutil
            process = psutil.Process()
            return {
                "pid": process.pid,
                "name": process.name(),
                "memory_info": process.memory_info()._asdict(),
                "cpu_percent": process.cpu_percent(),
                "status": process.status(),
                "create_time": process.create_time()
            }
        except ImportError:
            # Fallback без psutil
            return {
                "pid": os.getpid(),
                "name": sys.argv[0] if sys.argv else "python",
                "memory_info": self._get_process_memory(),
                "cpu_percent": 0,  # Недоступно без psutil
                "status": "running",
                "create_time": time.time()
            }
    
    def _get_windows_memory(self) -> Dict:
        """Отримання інформації про пам'ять в Windows"""
        try:
            # Використання wmic команди
            result = subprocess.run(
                ['wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory', '/value'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                total_kb = 0
                free_kb = 0
                
                for line in lines:
                    if 'TotalVisibleMemorySize=' in line:
                        total_kb = int(line.split('=')[1]) if line.split('=')[1] else 0
                    elif 'FreePhysicalMemory=' in line:
                        free_kb = int(line.split('=')[1]) if line.split('=')[1] else 0
                
                total_bytes = total_kb * 1024
                free_bytes = free_kb * 1024
                used_bytes = total_bytes - free_bytes
                
                return {
                    "total": total_bytes,
                    "available": free_bytes,
                    "used": used_bytes,
                    "percent": (used_bytes / total_bytes * 100) if total_bytes > 0 else 0,
                    "unit": "bytes"
                }
        except Exception:
            pass
        
        return self._get_generic_memory()
    
    def _get_linux_memory(self) -> Dict:
        """Отримання інформації про пам'ять в Linux"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # Парсинг /proc/meminfo
            lines = meminfo.split('\n')
            mem_data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    # Витягування числового значення (в kB)
                    value_match = value.strip().split()
                    if value_match:
                        mem_data[key.strip()] = int(value_match[0])
            
            total_kb = mem_data.get('MemTotal', 0)
            available_kb = mem_data.get('MemAvailable', mem_data.get('MemFree', 0))
            
            total_bytes = total_kb * 1024
            available_bytes = available_kb * 1024
            used_bytes = total_bytes - available_bytes
            
            return {
                "total": total_bytes,
                "available": available_bytes,
                "used": used_bytes,
                "percent": (used_bytes / total_bytes * 100) if total_bytes > 0 else 0,
                "unit": "bytes"
            }
            
        except Exception:
            pass
        
        return self._get_generic_memory()
    
    def _get_macos_memory(self) -> Dict:
        """Отримання інформації про пам'ять в macOS"""
        try:
            # Використання vm_stat команди
            result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                page_size = 4096  # Типовий розмір сторінки
                
                # Пошук розміру сторінки
                for line in lines:
                    if 'page size of' in line:
                        page_size = int(line.split()[-2])
                        break
                
                # Парсинг статистики
                stats = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        value = value.strip().rstrip('.')
                        if value.isdigit():
                            stats[key.strip()] = int(value)
                
                free_pages = stats.get('Pages free', 0)
                inactive_pages = stats.get('Pages inactive', 0)
                wired_pages = stats.get('Pages wired down', 0)
                active_pages = stats.get('Pages active', 0)
                
                total_bytes = (free_pages + inactive_pages + wired_pages + active_pages) * page_size
                available_bytes = (free_pages + inactive_pages) * page_size
                used_bytes = total_bytes - available_bytes
                
                return {
                    "total": total_bytes,
                    "available": available_bytes,
                    "used": used_bytes,
                    "percent": (used_bytes / total_bytes * 100) if total_bytes > 0 else 0,
                    "unit": "bytes"
                }
                
        except Exception:
            pass
        
        return self._get_generic_memory()
    
    def _get_generic_memory(self) -> Dict:
        """Загальний метод отримання інформації про пам'ять"""
        # Базова інформація без точних даних
        return {
            "total": 0,
            "available": 0,
            "used": 0,
            "percent": 0,
            "unit": "bytes",
            "note": "Точна інформація недоступна без psutil"
        }
    
    def _get_cpu_usage(self) -> float:
        """Отримання використання CPU"""
        try:
            if self.platform == "windows":
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'loadpercentage', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'LoadPercentage=' in line:
                            return float(line.split('=')[1])
            
            elif self.platform == "linux":
                # Читання /proc/loadavg
                with open('/proc/loadavg', 'r') as f:
                    load_avg = f.read().split()[0]
                    return float(load_avg) * 100 / os.cpu_count()
            
        except Exception:
            pass
        
        return 0.0
    
    def _get_cpu_frequency(self) -> Dict:
        """Отримання частоти CPU"""
        try:
            if self.platform == "linux":
                # Читання /proc/cpuinfo
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'cpu MHz' in line:
                            freq_mhz = float(line.split(':')[1].strip())
                            return {
                                "current": freq_mhz,
                                "unit": "MHz"
                            }
        except Exception:
            pass
        
        return {"current": 0, "unit": "MHz"}
    
    def _get_process_memory(self) -> Dict:
        """Отримання інформації про пам'ять процесу"""
        try:
            if self.platform == "windows":
                result = subprocess.run(
                    ['tasklist', '/fi', f'PID eq {os.getpid()}', '/fo', 'csv'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        # Парсинг CSV виводу
                        data = lines[1].split(',')
                        if len(data) > 4:
                            memory_str = data[4].strip('"').replace(',', '').replace(' K', '')
                            if memory_str.isdigit():
                                return {"rss": int(memory_str) * 1024}  # Конвертація з KB в байти
            
        except Exception:
            pass
        
        return {"rss": 0}
    
    def _is_cache_valid(self, key: str) -> bool:
        """Перевірка валідності кешу"""
        if key not in self.cache:
            return False
        
        return time.time() - self.cache[key]["timestamp"] < self.cache_timeout
    
    def _cache_data(self, key: str, data: Dict):
        """Кешування даних"""
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    def format_bytes(self, bytes_value: int) -> str:
        """Форматування байтів в читабельний вигляд"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def get_comprehensive_info(self) -> Dict:
        """Отримання всієї доступної системної інформації"""
        return {
            "system": self.get_system_info(),
            "memory": self.get_memory_info(),
            "cpu": self.get_cpu_info(),
            "disk": self.get_disk_usage(),
            "process": self.get_process_info(),
            "python": {
                "version": sys.version,
                "executable": sys.executable,
                "path": sys.path[:3]  # Перші 3 шляхи
            }
        }


# Функції для зворотної сумісності з psutil
def virtual_memory():
    """Емуляція psutil.virtual_memory()"""
    info = SystemInfoAlternative()
    memory = info.get_memory_info()
    
    class MemoryInfo:
        def __init__(self, data):
            self.total = data.get("total", 0)
            self.available = data.get("available", 0)
            self.used = data.get("used", 0)
            self.percent = data.get("percent", 0)
    
    return MemoryInfo(memory)


def disk_usage(path):
    """Емуляція psutil.disk_usage()"""
    info = SystemInfoAlternative()
    return info.get_disk_usage(path)


def cpu_percent():
    """Емуляція psutil.cpu_percent()"""
    info = SystemInfoAlternative()
    cpu_info = info.get_cpu_info()
    return cpu_info.get("cpu_usage", 0)


def cpu_count():
    """Емуляція psutil.cpu_count()"""
    return os.cpu_count()


# Тестування модуля
if __name__ == "__main__":
    print("🖥️ Тест System Info Alternative")
    
    info = SystemInfoAlternative()
    
    # Тест системної інформації
    system_info = info.get_system_info()
    print(f"\n💻 Система: {system_info['system']} {system_info['release']}")
    print(f"🐍 Python: {system_info['python_version']}")
    print(f"🏠 Користувач: {system_info['username']}")
    
    # Тест пам'яті
    memory_info = info.get_memory_info()
    if memory_info["total"] > 0:
        print(f"\n💾 Пам'ять:")
        print(f"  Загалом: {info.format_bytes(memory_info['total'])}")
        print(f"  Використано: {info.format_bytes(memory_info['used'])} ({memory_info['percent']:.1f}%)")
        print(f"  Доступно: {info.format_bytes(memory_info['available'])}")
    else:
        print("\n💾 Пам'ять: Інформація недоступна (встановіть psutil для точних даних)")
    
    # Тест CPU
    cpu_info = info.get_cpu_info()
    print(f"\n🔧 CPU:")
    print(f"  Процесор: {cpu_info['processor']}")
    print(f"  Ядер: {cpu_info['cpu_count']}")
    print(f"  Архітектура: {cpu_info['architecture']}")
    if cpu_info['cpu_usage'] > 0:
        print(f"  Використання: {cpu_info['cpu_usage']:.1f}%")
    
    # Тест диска
    disk_info = info.get_disk_usage(".")
    print(f"\n💿 Диск (поточна папка):")
    print(f"  Загалом: {info.format_bytes(disk_info['total'])}")
    print(f"  Використано: {info.format_bytes(disk_info['used'])} ({disk_info['percent']:.1f}%)")
    print(f"  Вільно: {info.format_bytes(disk_info['free'])}")
    
    print("\n✅ System Info Alternative готовий до використання!")
