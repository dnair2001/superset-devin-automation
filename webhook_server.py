#!/usr/bin/env python3
"""
Webhook server for GitHub label-triggered Devin automation.
Receives GitHub webhook events and triggers automation when 'devin-remediate' label is added.
"""

import os
import hmac
import hashlib
import json
import logging
from flask import Flask, request, jsonify
from automation import Automation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# GitHub webhook secret for signature verification
WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', '')

def verify_webhook_signature(payload, signature):
    """Verify GitHub webhook signature."""
    if not WEBHOOK_SECRET:
        logger.warning("No webhook secret configured, skipping signature verification")
        return True
    
    hash_algorithm, github_signature = signature.split('=', 1)
    if hash_algorithm != 'sha256':
        return False
    
    mac = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256)
    expected_signature = mac.hexdigest()
    
    return hmac.compare_digest(expected_signature, github_signature)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle GitHub webhook events."""
    # Verify webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    if signature and not verify_webhook_signature(request.data, signature):
        logger.error("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse webhook payload
    try:
        payload = request.json
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    
    # Check event type
    event_type = request.headers.get('X-GitHub-Event')
    logger.info(f"Received webhook event: {event_type}")
    
    if event_type == 'issues':
        return handle_issues_event(payload)
    elif event_type == 'ping':
        return jsonify({'message': 'pong'}), 200
    else:
        logger.info(f"Ignoring event type: {event_type}")
        return jsonify({'message': 'Event ignored'}), 200

def handle_issues_event(payload):
    """Handle issues labeled events."""
    action = payload.get('action')
    issue = payload.get('issue', {})
    labels = [label.get('name') for label in issue.get('labels', [])]
    changes = payload.get('changes', {})
    label_changes = changes.get('labels', {})
    
    logger.info(f"Issue action: {action}, labels: {labels}")
    logger.info(f"Label changes: {label_changes}")
    
    # Check if 'devin-remediate' label was added (only trigger on addition, not presence)
    if action == 'labeled':
        # Check the changes structure to see if devin-remediate was just added
        added_labels = label_changes.get('added', [])
        logger.info(f"Added labels from changes: {added_labels}")
        
        # Only trigger if devin-remediate was just added (not if it's already present)
        if 'devin-remediate' in added_labels:
            logger.info(f"devin-remediate label added to issue #{issue['number']}")
            return trigger_automation(issue)
        else:
            logger.info(f"devin-remediate not in added labels, skipping trigger")
    
    return jsonify({'message': 'Label not triggered'}), 200

def trigger_automation(issue):
    """Trigger automation for the labeled issue."""
    try:
        # Initialize automation
        automation = Automation(
            github_token=os.getenv('GITHUB_TOKEN'),
            github_repo=os.getenv('GITHUB_REPO'),
            devin_api_key=os.getenv('DEVIN_API_KEY'),
            devin_org_id=os.getenv('DEVIN_ORG_ID'),
            devin_github_secret_id=os.getenv('DEVIN_GITHUB_SECRET_ID'),
            demo_mode=os.getenv('DEMO_MODE', 'false').lower() == 'true'
        )
        
        # Add 'devin-in-progress' label
        automation.github_client.add_label(
            issue_number=issue['number'],
            label='devin-in-progress'
        )
        
        # Process the single issue
        result = automation.process_single_issue(issue)
        
        logger.info(f"Automation completed for issue #{issue['number']}: {result}")
        
        return jsonify({'message': 'Automation triggered', 'result': result}), 200
        
    except Exception as e:
        logger.error(f"Failed to trigger automation: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
