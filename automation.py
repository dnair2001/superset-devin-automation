"""
Main automation orchestrator that ties together GitHub, Devin, and observability
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

from devin_client import DevinClient, DevinSession
from issue_processor import IssueProcessor, RemediationPlan
from github_client import GitHubClient


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutomationOrchestrator:
    """Main orchestrator for the Devin automation system"""
    
    def __init__(self):
        load_dotenv()
        
        # Initialize clients
        self.devin_client = DevinClient(
            api_key=os.getenv("DEVIN_API_KEY"),
            api_url=os.getenv("DEVIN_API_URL", "https://api.devin.ai")
        )
        
        self.github_client = GitHubClient(
            token=os.getenv("GITHUB_TOKEN"),
            repo=os.getenv("GITHUB_REPO")
        )
        
        self.issue_processor = IssueProcessor()
        self.repo_url = f"https://github.com/{os.getenv('GITHUB_REPO')}.git"
    
    def run_once(self) -> Dict[str, Any]:
        """Run a single iteration of the automation"""
        logger.info("Starting automation iteration")
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "issues_processed": 0,
            "issues_successful": 0,
            "issues_failed": 0,
            "issues_skipped": 0,
            "session_details": []
        }
        
        try:
            # Get open issues
            issues = self.github_client.get_open_issues()
            logger.info(f"Found {len(issues)} open issues")
            
            for issue in issues:
                # Skip if assigned
                if issue.get("assignee"):
                    results["issues_skipped"] += 1
                    logger.info(f"Skipping issue #{issue['number']}: {issue['title']}")
                    continue
                
                results["issues_processed"] += 1
                logger.info(f"Processing issue #{issue['number']}: {issue['title']}")
                
                try:
                    # Create remediation plan
                    plan = self.issue_processor.create_remediation_plan(issue)
                    
                    # Create Devin session
                    session = self.devin_client.create_session(
                        repo_url=self.repo_url,
                        instructions=plan.instructions
                    )
                    
                    logger.info(f"Created Devin session {session.session_id} for issue #{issue['number']}")
                    
                    # Wait for completion
                    final_session = self.devin_client.wait_for_completion(
                        session.session_id,
                        timeout_seconds=1800
                    )
                    
                    # Record results
                    session_result = {
                        "issue_number": issue['number'],
                        "issue_title": issue['title'],
                        "session_id": session.session_id,
                        "status": final_session.status,
                        "logs": final_session.logs[-5:]
                    }
                    results["session_details"].append(session_result)
                    
                    if final_session.is_successful():
                        results["issues_successful"] += 1
                        logger.info(f"Successfully completed issue #{issue['number']}")
                        
                        # Add success comment
                        self.github_client.add_comment(
                            issue_number=issue['number'],
                            body=f"✅ Automatically remediated by Devin\n\nSession: {session.session_id}\nStatus: {final_session.status}"
                        )
                        
                        # Close the issue
                        self.github_client.close_issue(issue['number'])
                    else:
                        results["issues_failed"] += 1
                        logger.error(f"Failed to complete issue #{issue['number']}: {final_session.status}")
                        
                        # Add failure comment
                        self.github_client.add_comment(
                            issue_number=issue['number'],
                            body=f"❌ Remediation failed\n\nSession: {session.session_id}\nStatus: {final_session.status}\n\nLogs:\n" + "\n".join(final_session.logs[-10:])
                        )
                
                except Exception as e:
                    results["issues_failed"] += 1
                    logger.error(f"Error processing issue #{issue['number']}: {str(e)}")
                    
                    self.github_client.add_comment(
                        issue_number=issue['number'],
                        body=f"❌ Error during remediation: {str(e)}"
                    )
        
        except Exception as e:
            logger.error(f"Error in automation iteration: {str(e)}")
            results["error"] = str(e)
        
        logger.info(f"Iteration complete: {results}")
        return results


def main():
    """Main entry point"""
    orchestrator = AutomationOrchestrator()
    
    # Run single iteration for demo
    logger.info("Running single iteration for demo")
    results = orchestrator.run_once()
    
    # Print summary
    print("\n" + "="*50)
    print("AUTOMATION SUMMARY")
    print("="*50)
    print(f"Issues Processed: {results['issues_processed']}")
    print(f"Successful: {results['issues_successful']}")
    print(f"Failed: {results['issues_failed']}")
    print(f"Skipped: {results['issues_skipped']}")
    
    if results.get("session_details"):
        print("\nSession Details:")
        for session in results["session_details"]:
            print(f"  Issue #{session['issue_number']}: {session['status']}")
    
    print("="*50)


if __name__ == "__main__":
    main()
