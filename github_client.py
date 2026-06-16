"""
GitHub API client for managing issues
"""
import requests
from typing import Dict, Any, List


class GitHubClient:
    """Client for interacting with GitHub API"""
    
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_open_issues(self) -> List[Dict[str, Any]]:
        """Get all open issues from the repository"""
        endpoint = f"{self.api_url}/issues"
        params = {"state": "open", "sort": "created", "direction": "asc"}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def add_comment(self, issue_number: int, body: str) -> Dict[str, Any]:
        """Add a comment to an issue"""
        endpoint = f"{self.api_url}/issues/{issue_number}/comments"
        payload = {"body": body}
        response = requests.post(endpoint, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def close_issue(self, issue_number: int) -> Dict[str, Any]:
        """Close an issue"""
        endpoint = f"{self.api_url}/issues/{issue_number}"
        payload = {"state": "closed"}
        response = requests.patch(endpoint, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
