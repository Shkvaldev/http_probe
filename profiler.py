import asyncio
from typing import Dict, Any

class Profiler:
    """Entity for storing tests data and report generation"""
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.records = {}

    async def add_record(self, url: str, record: Dict[str, Any]) -> None:
        """Adding new record on test request to a URL"""
        async with self._lock:
            if url not in self.records:
                self.records[url] = []
            self.records[url].append(record)

    async def generate_report(self) -> Dict[str, Dict[str, Any]]:
        async with self._lock:
            result = {}
            for url, records in self.records.items():
                success_count = 0
                failed_count = 0
                errors_count = 0

                elapsed_times = []
                
                for record in records:
                    if record["is_success"]:
                        success_count += 1
                    elif record["is_failed"]:
                        failed_count += 1
                    else:
                        errors_count += 1
                    
                    elapsed_times.append(record["elapsed_time"])
                
                if elapsed_times:
                    result[url] = {
                        "success": success_count,
                        "failed": failed_count,
                        "errors": errors_count,
                        "min": min(elapsed_times),
                        "max": max(elapsed_times),
                        "avg": sum(elapsed_times) / len(elapsed_times)
                    }
                else:
                    result[url] = {
                        "success": 0,
                        "failed": 0,
                        "errors": 0,
                        "min": 0,
                        "max": 0,
                        "avg": 0
                    }
            return result
