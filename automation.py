"""
Main automation orchestrator that ties together GitHub, Devin, and observability
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
    def __init__(self, github_token=None, github_repo=None, devin_api_key=None, devin_org_id=None, devin_github_secret_id=None, demo_mode=False, max_concurrent_sessions=3):
        load_dotenv()
        
        self.demo_mode = demo_mode
        self.max_concurrent_sessions = max_concurrent_sessions
        
        # Initialize clients with provided parameters or environment variables
        if not demo_mode:
            self.devin_client = DevinClient(
                api_key=devin_api_key or os.getenv("DEVIN_API_KEY"),
                org_id=devin_org_id or os.getenv("DEVIN_ORG_ID"),
                api_url=os.getenv("DEVIN_API_URL", "https://api.devin.ai")
            )
        
        self.github_client = GitHubClient(
            token=github_token or os.getenv("GITHUB_TOKEN"),
            repo=github_repo or os.getenv("GITHUB_REPO")
        )
        
        self.issue_processor = IssueProcessor()
        self.repo_url = f"https://github.com/{github_repo or os.getenv('GITHUB_REPO')}.git"
        self.devin_github_secret_id = devin_github_secret_id or os.getenv("DEVIN_GITHUB_SECRET_ID")
    
    def process_single_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single issue - designed for concurrent execution"""
        logger.info(f"Processing issue #{issue['number']}: {issue['title']}")
        
        try:
            # Create remediation plan
            plan = self.issue_processor.create_remediation_plan(issue)
            
            if self.demo_mode:
                # Mock Devin session for demo
                import time
                logger.info(f"[DEMO MODE] Simulating Devin session for issue #{issue['number']}")
                time.sleep(2)  # Simulate processing time
                
                session_id = f"demo-session-{issue['number']}"
                final_session = DevinSession(
                    session_id=session_id,
                    status="running",
                    status_detail="waiting_for_user",  # Use waiting_for_user for v3 API consistency
                    created_at=datetime.utcnow().isoformat(),
                    logs=["Analyzing issue...", "Making code changes...", "Running tests...", "Committing changes..."]
                )
                logger.info(f"[DEMO MODE] Completed mock session {session_id}")
            else:
                # Create real Devin session with GitHub secret
                secret_ids = [self.devin_github_secret_id] if self.devin_github_secret_id else None
                
                session = self.devin_client.create_session(
                    repo_url=self.repo_url,
                    prompt=plan.instructions,
                    secret_ids=secret_ids
                )
                
                logger.info(f"Created Devin session {session.session_id} for issue #{issue['number']} with GitHub authentication")
                
                # Wait for completion
                final_session = self.devin_client.wait_for_completion(
                    session.session_id,
                    timeout_seconds=1200  # 20 minutes for real work
                )
            
            # Record results
            session_result = {
                "issue_number": issue['number'],
                "issue_title": issue['title'],
                "session_id": session.session_id,
                "status": final_session.status_detail,  # Use status_detail for v3 API
                "logs": final_session.logs[-5:]
            }
            
            if final_session.is_successful():
                logger.info(f"Successfully completed issue #{issue['number']}")
                
                # Remove devin-in-progress label
                try:
                    self.github_client.remove_label(issue['number'], 'devin-in-progress')
                except:
                    pass  # Label may not exist
                
                if final_session.is_waiting_for_user():
                    # PR is created and waiting for human review - don't close issue
                    self.github_client.add_comment(
                        issue_number=issue['number'],
                        body=f"🔄 PR is ready to remediate this issue. Waiting for human review on PR.\n\nSession: {session.session_id}\nStatus: {final_session.status_detail}"
                    )
                    # Add devin-success label
                    try:
                        self.github_client.add_label(issue['number'], 'devin-success')
                    except:
                        pass
                    session_result["success"] = True
                    session_result["waiting_for_review"] = True
                else:
                    # Task is fully complete - close the issue
                    self.github_client.add_comment(
                        issue_number=issue['number'],
                        body=f"✅ Automatically remediated by Devin\n\nSession: {session.session_id}\nStatus: {final_session.status_detail}"
                    )
                    
                    # Add devin-success label
                    try:
                        self.github_client.add_label(issue['number'], 'devin-success')
                    except:
                        pass
                    
                    # Close the issue
                    self.github_client.close_issue(issue['number'])
                    
                    session_result["success"] = True
            else:
                logger.error(f"Failed to complete issue #{issue['number']}: {final_session.status}")
                
                # Remove devin-in-progress label
                try:
                    self.github_client.remove_label(issue['number'], 'devin-in-progress')
                except:
                    pass  # Label may not exist
                
                # Add failure comment
                self.github_client.add_comment(
                    issue_number=issue['number'],
                    body=f"❌ Remediation failed\n\nSession: {session.session_id}\nStatus: {final_session.status_detail}\n\nLogs:\n" + "\n".join(final_session.logs[-10:])
                )
                
                # Add devin-failed label
                try:
                    self.github_client.add_label(issue['number'], 'devin-failed')
                except:
                    pass
                
                session_result["success"] = False
            
            return session_result
        
        except Exception as e:
            logger.error(f"Error processing issue #{issue['number']}: {str(e)}")
            
            self.github_client.add_comment(
                issue_number=issue['number'],
                body=f"❌ Error during remediation: {str(e)}"
            )
            
            return {
                "issue_number": issue['number'],
                "issue_title": issue['title'],
                "success": False,
                "error": str(e)
            }

    def run_once(self) -> Dict[str, Any]:
        """Run a single iteration of the automation with concurrent processing"""
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
            
            # Filter out assigned issues
            unassigned_issues = [issue for issue in issues if not issue.get("assignee")]
            results["issues_skipped"] = len(issues) - len(unassigned_issues)
            
            logger.info(f"Processing {len(unassigned_issues)} unassigned issues concurrently (max {self.max_concurrent_sessions} at once)")
            
            # Process issues concurrently
            with ThreadPoolExecutor(max_workers=self.max_concurrent_sessions) as executor:
                # Submit all issues for processing
                future_to_issue = {
                    executor.submit(self.process_single_issue, issue): issue
                    for issue in unassigned_issues
                }
                
                results["issues_processed"] = len(unassigned_issues)
                
                # Collect results as they complete
                for future in as_completed(future_to_issue):
                    issue = future_to_issue[future]
                    try:
                        session_result = future.result()
                        results["session_details"].append(session_result)
                        
                        if session_result.get("success"):
                            results["issues_successful"] += 1
                        else:
                            results["issues_failed"] += 1
                    except Exception as e:
                        logger.error(f"Exception processing issue #{issue['number']}: {str(e)}")
                        results["issues_failed"] += 1
        
        except Exception as e:
            logger.error(f"Error in automation iteration: {str(e)}")
            results["error"] = str(e)
        
        logger.info(f"Iteration complete: {results}")
        return results


class Automation:
    """Wrapper class for backward compatibility and webhook usage"""
    
    def __init__(self, github_token=None, github_repo=None, devin_api_key=None, devin_org_id=None, devin_github_secret_id=None, demo_mode=False, max_concurrent_sessions=3):
        self.orchestrator = AutomationOrchestrator(
            github_token=github_token,
            github_repo=github_repo,
            devin_api_key=devin_api_key,
            devin_org_id=devin_org_id,
            devin_github_secret_id=devin_github_secret_id,
            demo_mode=demo_mode,
            max_concurrent_sessions=max_concurrent_sessions
        )
    
    @property
    def github_client(self):
        return self.orchestrator.github_client
    
    @property
    def devin_client(self):
        return self.orchestrator.devin_client
    
    def process_single_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single issue - designed for webhook triggers"""
        return self.orchestrator.process_single_issue(issue)


def main():
    """Main entry point"""
    import sys
    
    # Check for demo mode flag
    demo_mode = "--demo" in sys.argv or "-d" in sys.argv
    
    # Check for concurrent sessions flag
    max_concurrent = 3  # default
    if "--concurrent" in sys.argv:
        try:
            idx = sys.argv.index("--concurrent")
            if idx + 1 < len(sys.argv):
                max_concurrent = int(sys.argv[idx + 1])
        except (ValueError, IndexError):
            pass
    
    orchestrator = AutomationOrchestrator(demo_mode=demo_mode, max_concurrent_sessions=max_concurrent)
    
    if demo_mode:
        logger.info("Running in DEMO MODE - Devin sessions will be mocked")
    
    logger.info(f"Running with max {max_concurrent} concurrent sessions")
    
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
            status = session.get('status', 'unknown')
            print(f"  Issue #{session['issue_number']}: {status}")
    
    print("="*50)


if __name__ == "__main__":
    main()
