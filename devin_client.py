"""
Devin API client for managing autonomous coding sessions
"""
import requests
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DevinSession:
    """Represents a Devin autonomous coding session"""
    session_id: str
    status: str
    created_at: str
    logs: list[str]
    
    def is_complete(self) -> bool:
        return self.status in ["completed", "failed", "cancelled"]
    
    def is_successful(self) -> bool:
        return self.status == "completed"


class DevinClient:
    """Client for interacting with the Devin API"""
    
    def __init__(self, api_key: str, api_url: str = "https://api.devin.ai"):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_session(
        self, 
        repo_url: str, 
        instructions: str,
        branch: str = "main"
    ) -> DevinSession:
        """Create a new Devin coding session"""
        endpoint = f"{self.api_url}/v1/sessions"
        payload = {
            "repository": repo_url,
            "instructions": instructions,
            "branch": branch,
            "auto_commit": True
        }
        response = requests.post(endpoint, json=payload, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return DevinSession(
            session_id=data["id"],
            status=data["status"],
            created_at=data["created_at"],
            logs=data.get("logs", [])
        )
    
    def get_session(self, session_id: str) -> DevinSession:
        """Get the status of an existing session"""
        endpoint = f"{self.api_url}/v1/sessions/{session_id}"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return DevinSession(
            session_id=data["id"],
            status=data["status"],
            created_at=data["created_at"],
            logs=data.get("logs", [])
        )
    
    def wait_for_completion(
        self, 
        session_id: str, 
        timeout_seconds: int = 1800,
        poll_interval_seconds: int = 10
    ) -> DevinSession:
        """Wait for a session to complete"""
        import time
        elapsed = 0
        while elapsed < timeout_seconds:
            session = self.get_session(session_id)
            if session.is_complete():
                return session
            time.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds
        raise TimeoutError(f"Session {session_id} did not complete within {timeout_seconds} seconds")
