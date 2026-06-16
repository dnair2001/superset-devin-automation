"""
Issue processor that maps GitHub issues to Devin remediation strategies
"""
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class RemediationPlan:
    """Plan for remediating a specific issue"""
    instructions: str
    expected_outcome: str


class IssueProcessor:
    """Processes GitHub issues and generates remediation plans"""
    
    def __init__(self):
        self.issue_handlers = {
            "dependency-upgrade": self._handle_dependency_upgrade,
            "deprecated-code": self._handle_deprecated_code,
            "license-compliance": self._handle_license_compliance
        }
    
    def categorize_issue(self, issue: Dict[str, Any]) -> str:
        """Categorize an issue to determine the appropriate handler"""
        title = issue.get("title", "").lower()
        
        if "upgrade" in title and any(dep in title for dep in ["flask", "deck.gl", "npm"]):
            return "dependency-upgrade"
        if "deprecated" in title or "remove" in title:
            if "slacknotification" in title.lower():
                return "deprecated-code"
        if "gpl" in title or "license" in title:
            return "license-compliance"
        return "general"
    
    def create_remediation_plan(self, issue: Dict[str, Any]) -> RemediationPlan:
        """Create a remediation plan for a given issue"""
        category = self.categorize_issue(issue)
        handler = self.issue_handlers.get(category, self._handle_general)
        return handler(issue)
    
    def _handle_dependency_upgrade(self, issue: Dict[str, Any]) -> RemediationPlan:
        """Handle dependency upgrade issues"""
        title = issue.get("title", "")
        
        if "flask" in title.lower():
            return RemediationPlan(
                instructions="""Upgrade Flask from 3.1.2 to 3.1.3:
1. Open pyproject.toml and verify the Flask version constraint allows 3.1.3
2. Run: uv pip compile pyproject.toml requirements/base.in -o requirements/base.txt
3. Run: uv pip compile requirements/development.in -c requirements/base-constraint.txt -o requirements/development.txt
4. Run basic tests: pytest tests/unit_tests/app/ -v
5. Commit the changes with message: "Upgrade Flask to 3.1.3"
6. Push the changes""",
                expected_outcome="Flask upgraded successfully, all tests pass"
            )
        
        elif "deck.gl" in title.lower():
            return RemediationPlan(
                instructions="""Upgrade @deck.gl packages from 9.2.5 to 9.3.4:
1. Open package.json and update all @deck.gl versions from "~9.2.5" to "~9.3.4"
2. Update all @luma.gl versions from "~9.2.5" to "~9.3.4"
3. Run: npm install
4. Run: npm run lint
5. Run: npm run test -- --testPathPattern=deck.gl
6. Commit the changes with message: "Upgrade @deck.gl to 9.3.4"
7. Push the changes""",
                expected_outcome="@deck.gl packages upgraded successfully, linting and tests pass"
            )
        
        return self._handle_general(issue)
    
    def _handle_deprecated_code(self, issue: Dict[str, Any]) -> RemediationPlan:
        """Handle deprecated code removal issues"""
        title = issue.get("title", "")
        
        if "slacknotification" in title.lower():
            return RemediationPlan(
                instructions="""Remove the deprecated SlackNotification class:
1. Open superset/reports/notifications/slack.py
2. Remove the SlackNotification class (approximately lines 56-70)
3. Search the codebase for any usages of SlackNotification using grep
4. Remove any unused imports
5. Run tests: pytest tests/unit_tests/reports/ -v
6. Commit the changes with message: "Remove deprecated SlackNotification class"
7. Push the changes""",
                expected_outcome="SlackNotification class removed, all tests pass"
            )
        
        return self._handle_general(issue)
    
    def _handle_license_compliance(self, issue: Dict[str, Any]) -> RemediationPlan:
        """Handle license compliance issues"""
        return RemediationPlan(
            instructions="""Remove GPL-licensed dependencies (paramiko and pyxlsb):
1. Research MIT/Apache-licensed alternatives for paramiko (SSH library)
2. Research MIT/Apache-licensed alternatives for pyxlsb (Excel binary reader)
3. For paramiko replacement:
   - Find compatible SSH library (e.g., ssh2-python)
   - Update code in superset/connectors/ to use the alternative
   - Update pyproject.toml to remove paramiko and add the alternative
4. For pyxlsb replacement:
   - Find compatible Excel binary reader
   - Update code to use the alternative
   - Update pyproject.toml to remove pyxlsb and add the alternative
5. Regenerate requirements files: uv pip compile pyproject.toml requirements/base.in -o requirements/base.txt
6. Run tests to ensure functionality is preserved
7. Commit the changes with message: "Remove GPL-licensed dependencies for Apache 2.0 compliance"
8. Push the changes""",
            expected_outcome="GPL dependencies removed, replaced with Apache 2.0 compatible alternatives, tests pass"
        )
    
    def _handle_general(self, issue: Dict[str, Any]) -> RemediationPlan:
        """Handle general issues"""
        title = issue.get("title", "")
        body = issue.get("body", "")
        return RemediationPlan(
            instructions=f"""Address the issue: {title}

Issue description:
{body}

Please:
1. Analyze the issue and understand what needs to be done
2. Make the necessary code changes
3. Run relevant tests
4. Commit the changes with a descriptive message
5. Push the changes""",
            expected_outcome="Issue resolved successfully"
        )
