# backend/app/services/analytics_service.py
import os
import json
import uuid
import re
import threading
from datetime import datetime
from collections import Counter
from pathlib import Path
from app.core.config import settings

class AnalyticsService:
    def __init__(self):
        self.file_path = settings.DATA_DIR / "analytics.json"
        self.lock = threading.Lock()
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        with self.lock:
            if not self.file_path.exists():
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)

    def _read_logs(self) -> list:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading analytics logs: {e}")
            return []

    def _write_logs(self, logs: list):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing analytics logs: {e}")

    def log_query(self, query: str, role: str, response_time_seconds: float, log_id: str = None, session_id: str = None, response_text: str = None) -> str:
        """Log a new user query and return its unique ID"""
        if not log_id:
            log_id = str(uuid.uuid4())
        new_entry = {
            "id": log_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response_text,
            "role": role,
            "response_time_seconds": round(response_time_seconds, 3),
            "feedback": "neutral"  # neutral by default until rated
        }
        
        # Avoid logging the secret code itself
        if query.strip().upper() == "I WANT TO KNOW...":
            return log_id

        with self.lock:
            logs = self._read_logs()
            logs.insert(0, new_entry)  # Prepend so recent entries are first
            self._write_logs(logs)
            
        return log_id

    def submit_feedback(self, log_id: str, feedback: str) -> bool:
        """Update feedback rating for an existing query log entry"""
        if feedback not in ["satisfied", "unsatisfied", "neutral"]:
            return False
            
        with self.lock:
            logs = self._read_logs()
            updated = False
            for entry in logs:
                if entry.get("id") == log_id:
                    entry["feedback"] = feedback
                    updated = True
                    break
            if updated:
                self._write_logs(logs)
            return updated

    def get_disliked_queries(self) -> list:
        """Return all query logs where user feedback was unsatisfied (disliked)"""
        with self.lock:
            logs = self._read_logs()
        return [entry for entry in logs if entry.get("feedback") == "unsatisfied"]

    def get_metrics(self) -> dict:
        """Retrieve aggregated metrics for the admin dashboard"""
        with self.lock:
            logs = self._read_logs()
            
        total_queries = len(logs)
        
        # Averages & feedback counts
        avg_response_time = 0.0
        satisfied_count = 0
        unsatisfied_count = 0
        rated_count = 0
        
        words = []
        stop_words = {
            "what", "is", "the", "are", "on", "for", "in", "of", "to", "a", "an", "and", "by", "how",
            "kya", "hai", "ko", "ke", "liye", "kese", "kaise", "kab", "kon", "kya", "nhi", "nahi",
            "क्या", "है", "को", "के", "लिए", "कैसे", "कब", "कौन", "नहीं", "का", "की", "में", "पर"
        }
        
        for entry in logs:
            avg_response_time += entry.get("response_time_seconds", 0.0)
            fb = entry.get("feedback", "neutral")
            if fb == "satisfied":
                satisfied_count += 1
                rated_count += 1
            elif fb == "unsatisfied":
                unsatisfied_count += 1
                rated_count += 1
                
            # Extract words for frequency mapping
            query_text = entry.get("query", "").lower()
            cleaned_words = re.findall(r'\b[a-zA-Z\u0900-\u097f]{3,}\b', query_text)
            for w in cleaned_words:
                if w not in stop_words:
                    words.append(w)
                    
        avg_response_time = round(avg_response_time / total_queries, 2) if total_queries > 0 else 0.0
        satisfaction_rate = round((satisfied_count / rated_count) * 100, 1) if rated_count > 0 else 100.0
        
        # Get 5 most common words
        common_words = [item[0] for item in Counter(words).most_common(5)]
        
        return {
            "total_queries": total_queries,
            "avg_response_time": avg_response_time,
            "satisfaction_rate": satisfaction_rate,
            "satisfied_count": satisfied_count,
            "unsatisfied_count": unsatisfied_count,
            "rated_count": rated_count,
            "most_asked_topics": common_words,
            "queries": logs[:50]  # Limit to 50 most recent for UI performance
        }

analytics_service = AnalyticsService()
