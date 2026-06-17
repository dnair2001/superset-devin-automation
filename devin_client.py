"""
Devin API client for managing autonomous coding sessions
"""
import requests
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DevinSession:
    """Represents a Devin autonomous coding session"""
    session_id: str
    status: str
    status_detail: str = ""
    created_at: str = ""
    logs: list[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []
    
    def is_complete(self) -> bool:
        # For v3 API, check status_detail for completion
        # According to v3 docs, status can be "running" while status_detail is "finished"
        return self.status_detail in ["finished", "failed", "cancelled"]
    
    def is_successful(self) -> bool:
        # For v3 API, success is determined by status_detail being "finished"
        return self.status_detail == "finished"


class DevinClient:
    """Client for interacting with the Devin API v3"""
    
    def __init__(self, api_key: str, org_id: str, api_url: str = "https://api.devin.ai"):
        self.api_key = api_key
        self.org_id = org_id
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_session(
        self, 
        repo_url: str, 
        prompt: str,
        branch: str = "main",
        secret_ids: list = None
    ) -> DevinSession:
        """Create a new Devin coding session"""
        endpoint = f"{self.api_url}/v3/organizations/{self.org_id}/sessions"
        payload = {
            "prompt": prompt,
            "repos": [repo_url],
            "branch": branch
        }
        if secret_ids:
            payload["secret_ids"] = secret_ids
        
        response = requests.post(endpoint, json=payload, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return DevinSession(
            session_id=data["session_id"],
            status=data["status"],
            created_at=str(data["created_at"]),
            logs=[]
        )
    
    def get_session(self, session_id: str) -> DevinSession:
        """Get the status of an existing session"""
        endpoint = f"{self.api_url}/v3/organizations/{self.org_id}/sessions/{session_id}"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return DevinSession(
            session_id=data["session_id"],
            status=data["status"],
            status_detail=data.get("status_detail", ""),
            created_at=str(data["created_at"]),
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
        import logging
        logger = logging.getLogger(__name__)
        
        elapsed = 0
        while elapsed < timeout_seconds:
            session = self.get_session(session_id)
            logger.info(f"Session {session_id} status: {session.status}, detail: {session.status_detail} (elapsed: {elapsed}s)")
            
            if session.is_complete():
                logger.info(f"Session {session_id} detected as complete - status: {session.status}, detail: {session.status_detail}")
                return session
            
            time.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds
        
        raise TimeoutError(f"Session {session_id} did not complete within {timeout_seconds} seconds")
