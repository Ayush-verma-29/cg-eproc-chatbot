# backend/app/core/session.py
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.core.config import settings

class SessionManager:
    """Manages user sessions with role persistence"""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, role: str = None) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "role": role,
            "history": []
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Check if session expired
            if datetime.now() - session["last_activity"] > timedelta(seconds=settings.SESSION_TIMEOUT_SECONDS):
                del self.sessions[session_id]
                return None
            session["last_activity"] = datetime.now()
            return session
        return None
    
    def set_role(self, session_id: str, role: str) -> bool:
        """Set role for a session"""
        if session_id in self.sessions:
            self.sessions[session_id]["role"] = role
            return True
        return False
    
    def get_role(self, session_id: str) -> Optional[str]:
        """Get role from session"""
        session = self.get_session(session_id)
        return session["role"] if session else None
    
    def add_to_history(self, session_id: str, question: str, answer: str):
        """Add conversation to history (keeps last 5 turns)"""
        if session_id in self.sessions:
            history = self.sessions[session_id]["history"]
            history.append({
                "question": question,
                "answer": answer[:1500],  # keep more context for follow-up understanding
                "timestamp": datetime.now().isoformat()
            })
            # Keep only last 5 turns to prevent memory bloat
            if len(history) > 5:
                self.sessions[session_id]["history"] = history[-5:]
    
    def clear_session(self, session_id: str):
        """Clear a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

# Global instance
session_manager = SessionManager()