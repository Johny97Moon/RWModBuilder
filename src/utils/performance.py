"""
Система профілювання та оптимізації продуктивності
Спрощена версія для CustomTkinter без PyQt6 та psutil залежностей
"""

import time
import functools
import threading
import os
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict, deque

# Спроба імпорту psutil з fallback
try:
    import psutil  # type: ignore
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

# Спроба імпорту logger з fallback
LOGGER_AVAILABLE = False

# Fallback logger
class FallbackLogger:
    def get_logger(self):
        return self
    def debug(self, msg): print(f"DEBUG: {msg}")
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def critical(self, msg): print(f"CRITICAL: {msg}")

try:
    from utils.simple_logger import get_logger_instance  # type: ignore
    LOGGER_AVAILABLE = True
except ImportError:
    def get_logger_instance():
        return FallbackLogger()


class PerformanceProfiler:
    """Профайлер продуктивності для відстеження викликів методів"""

    def __init__(self):
        self.call_times = defaultdict(list)
        self.call_counts = defaultdict(int)
        self.memory_usage = deque(maxlen=100)
        self.enabled = True
        self.logger = get_logger_instance().get_logger()

    def profile_method(self, func: Callable) -> Callable:
        """Декоратор для профілювання методів"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)

            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                end_memory = self.get_memory_usage()

                execution_time = end_time - start_time
                memory_delta = end_memory - start_memory

                method_name = f"{func.__module__}.{func.__qualname__}"
                self.call_times[method_name].append(execution_time)
                self.call_counts[method_name] += 1

                # Логуємо повільні виклики
                if execution_time > 0.1:  # Більше 100мс
                    self.logger.warning(
                        f"Повільний виклик: {method_name} - {execution_time:.3f}s"
                    )

                # Логуємо великі витрати пам'яті
                if memory_delta > 10:  # Більше 10MB
                    self.logger.warning(
                        f"Великі витрати пам'яті: {method_name} - {memory_delta:.1f}MB"
                    )

        return wrapper

    def get_memory_usage(self) -> float:
        """Отримання поточного використання пам'яті в MB"""
        if not PSUTIL_AVAILABLE or psutil is None:
            return 0.0
        try:
            process = psutil.Process(os.getpid())  # type: ignore
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Отримання статистики профілювання"""
        stats = {}

        for method_name, times in self.call_times.items():
            if times:
                stats[method_name] = {
                    'calls': self.call_counts[method_name],
                    'total_time': sum(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }

        return stats

    def get_top_methods(self, limit: int = 10, sort_by: str = 'total_time') -> List[Dict]:
        """Отримання топ методів за вказаним критерієм"""
        stats = self.get_stats()

        sorted_methods = sorted(
            stats.items(),
            key=lambda x: x[1].get(sort_by, 0),
            reverse=True
        )

        return [
            {
                'method': method,
                **data
            }
            for method, data in sorted_methods[:limit]
        ]

    def reset_stats(self):
        """Скидання статистики"""
        self.call_times.clear()
        self.call_counts.clear()
        self.memory_usage.clear()

    def enable(self):
        """Увімкнення профілювання"""
        self.enabled = True

    def disable(self):
        """Вимкнення профілювання"""
        self.enabled = False


class MemoryMonitor:
    """Монітор використання пам'яті (спрощена версія без PyQt6)"""

    def __init__(self, warning_threshold: float = 500, critical_threshold: float = 1000):
        self.warning_threshold = warning_threshold  # MB
        self.critical_threshold = critical_threshold  # MB
        self.logger = get_logger_instance().get_logger()

        # Callback функції замість сигналів
        self.memory_warning_callback = None
        self.memory_critical_callback = None

        self.last_warning_time = 0
        self.last_critical_time = 0
        self.monitoring = False
        self.monitor_thread = None

    def set_warning_callback(self, callback: Callable[[float], None]):
        """Встановити callback для попереджень про пам'ять"""
        self.memory_warning_callback = callback

    def set_critical_callback(self, callback: Callable[[float], None]):
        """Встановити callback для критичних попереджень про пам'ять"""
        self.memory_critical_callback = callback

    def start_monitoring(self):
        """Запустити моніторинг пам'яті"""
        if self.monitoring:
            return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Зупинити моніторинг пам'яті"""
        self.monitoring = False

    def _monitor_loop(self):
        """Основний цикл моніторингу"""
        while self.monitoring:
            self.check_memory()
            time.sleep(5)  # Перевірка кожні 5 секунд

    def check_memory(self):
        """Перевірка використання пам'яті"""
        if not PSUTIL_AVAILABLE or psutil is None:
            return

        try:
            process = psutil.Process(os.getpid())  # type: ignore
            memory_mb = process.memory_info().rss / 1024 / 1024

            current_time = time.time()

            # Критичний рівень
            if memory_mb > self.critical_threshold:
                if current_time - self.last_critical_time > 60:  # Не частіше ніж раз на хвилину
                    self.logger.critical(f"Критичне використання пам'яті: {memory_mb:.1f}MB")
                    if self.memory_critical_callback:
                        self.memory_critical_callback(memory_mb)
                    self.last_critical_time = current_time

            # Попередження
            elif memory_mb > self.warning_threshold:
                if current_time - self.last_warning_time > 300:  # Не частіше ніж раз на 5 хвилин
                    self.logger.warning(f"Високе використання пам'яті: {memory_mb:.1f}MB")
                    if self.memory_warning_callback:
                        self.memory_warning_callback(memory_mb)
                    self.last_warning_time = current_time

        except Exception as e:
            self.logger.error(f"Помилка моніторингу пам'яті: {e}")

    def get_memory_info(self) -> Dict[str, float]:
        """Отримання детальної інформації про пам'ять"""
        if not PSUTIL_AVAILABLE or psutil is None:
            return {}

        try:
            process = psutil.Process(os.getpid())  # type: ignore
            memory_info = process.memory_info()

            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Фізична пам'ять
                'vms_mb': memory_info.vms / 1024 / 1024,  # Віртуальна пам'ять
                'percent': process.memory_percent(),       # Відсоток від системної пам'яті
                'available_mb': psutil.virtual_memory().available / 1024 / 1024  # type: ignore
            }
        except Exception as e:
            self.logger.error(f"Помилка отримання інформації про пам'ять: {e}")
            return {}


class CacheManager:
    """Менеджер кешування для оптимізації продуктивності"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
        self.logger = get_logger_instance().get_logger()

    def get(self, key: str) -> Any:
        """Отримання значення з кешу"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """Збереження значення в кеш"""
        # Очищуємо кеш якщо він переповнений
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[key] = value
        self.access_times[key] = time.time()

    def _evict_oldest(self):
        """Видалення найстарішого елемента з кешу"""
        if not self.access_times:
            return

        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]

    def clear(self):
        """Очищення кешу"""
        self.cache.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Отримання статистики кешу"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'usage_percent': (len(self.cache) / self.max_size) * 100
        }


class LazyLoader:
    """Ледаче завантаження ресурсів"""

    def __init__(self):
        self.loaded_resources = {}
        self.loading_functions = {}
        self.logger = get_logger_instance().get_logger()

    def register_loader(self, resource_name: str, loader_func: Callable):
        """Реєстрація функції завантаження ресурсу"""
        self.loading_functions[resource_name] = loader_func

    def get_resource(self, resource_name: str) -> Any:
        """Отримання ресурсу з ледачим завантаженням"""
        if resource_name in self.loaded_resources:
            return self.loaded_resources[resource_name]

        if resource_name in self.loading_functions:
            try:
                start_time = time.perf_counter()
                resource = self.loading_functions[resource_name]()
                load_time = time.perf_counter() - start_time

                self.loaded_resources[resource_name] = resource
                self.logger.debug(f"Завантажено ресурс '{resource_name}' за {load_time:.3f}s")

                return resource
            except Exception as e:
                self.logger.error(f"Помилка завантаження ресурсу '{resource_name}': {e}")
                return None

        self.logger.warning(f"Ресурс '{resource_name}' не зареєстровано")
        return None

    def preload_resource(self, resource_name: str):
        """Попереднє завантаження ресурсу"""
        self.get_resource(resource_name)

    def unload_resource(self, resource_name: str):
        """Вивантаження ресурсу з пам'яті"""
        if resource_name in self.loaded_resources:
            del self.loaded_resources[resource_name]
            self.logger.debug(f"Вивантажено ресурс '{resource_name}'")


class ThreadPool:
    """Пул потоків для асинхронних операцій"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.workers = []
        self.task_queue = deque()
        self.running = False
        self.logger = get_logger_instance().get_logger()

    def start(self):
        """Запуск пулу потоків"""
        if self.running:
            return

        self.running = True
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)

        self.logger.debug(f"Запущено пул потоків з {self.max_workers} воркерами")

    def stop(self):
        """Зупинка пулу потоків"""
        self.running = False
        self.logger.debug("Зупинка пулу потоків")

    def submit_task(self, func: Callable, *args, **kwargs):
        """Додавання задачі до черги"""
        task = (func, args, kwargs)
        self.task_queue.append(task)

    def _worker_loop(self):
        """Основний цикл воркера"""
        while self.running:
            try:
                if self.task_queue:
                    func, args, kwargs = self.task_queue.popleft()
                    func(*args, **kwargs)
                else:
                    time.sleep(0.1)  # Невелика затримка якщо немає задач
            except Exception as e:
                self.logger.error(f"Помилка виконання задачі в пулі потоків: {e}")


# Глобальні екземпляри
_profiler = PerformanceProfiler()
_cache_manager = CacheManager()
_lazy_loader = LazyLoader()
_thread_pool = ThreadPool()


def get_profiler() -> PerformanceProfiler:
    """Отримання глобального профайлера"""
    return _profiler


def get_cache_manager() -> CacheManager:
    """Отримання глобального менеджера кешу"""
    return _cache_manager


def get_lazy_loader() -> LazyLoader:
    """Отримання глобального ледачого завантажувача"""
    return _lazy_loader


def get_thread_pool() -> ThreadPool:
    """Отримання глобального пулу потоків"""
    return _thread_pool


# Декоратори для зручності використання
def profile(func: Callable) -> Callable:
    """Декоратор для профілювання методу"""
    return _profiler.profile_method(func)


def cached(cache_key_func: Optional[Callable] = None):
    """Декоратор для кешування результатів функції"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Генеруємо ключ кешу
            if cache_key_func is not None:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"

            # Перевіряємо кеш
            cached_result = _cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Виконуємо функцію та кешуємо результат
            result = func(*args, **kwargs)
            _cache_manager.set(cache_key, result)
            return result

        return wrapper
    return decorator


def async_task(func: Callable) -> Callable:
    """Декоратор для виконання функції в пулі потоків"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        _thread_pool.submit_task(func, *args, **kwargs)
    return wrapper
