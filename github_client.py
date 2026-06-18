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
        """Get all open issues from the repository (excluding pull requests)"""
        endpoint = f"{self.api_url}/issues"
        params = {"state": "open", "sort": "created", "direction": "asc"}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        # Filter out pull requests (GitHub API returns both issues and PRs)
        issues = response.json()
        return [issue for issue in issues if "pull_request" not in issue]
    
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
    
    def add_label(self, issue_number: int, label: str) -> Dict[str, Any]:
        """Add a label to an issue"""
        endpoint = f"{self.api_url}/issues/{issue_number}/labels"
        payload = {"labels": [label]}
        response = requests.post(endpoint, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def remove_label(self, issue_number: int, label: str) -> Dict[str, Any]:
        """Remove a label from an issue"""
        endpoint = f"{self.api_url}/issues/{issue_number}/labels/{label}"
        response = requests.delete(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def set_labels(self, issue_number: int, labels: List[str]) -> Dict[str, Any]:
        """Set the labels for an issue (replaces all existing labels)"""
        endpoint = f"{self.api_url}/issues/{issue_number}"
        payload = {"labels": labels}
        response = requests.patch(endpoint, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
