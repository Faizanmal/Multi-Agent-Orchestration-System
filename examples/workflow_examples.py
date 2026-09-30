"""
Example script demonstrating the Multi-Agent Workflow System
This script shows how to use workflows to solve real-world problems
"""

import time
from typing import Any

import requests

# Configuration
API_BASE_URL = "http://localhost:8000/api/agents/api"


class WorkflowClient:
    """Client for interacting with the workflow API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
    
    def list_templates(self, category: str | None = None) -> dict[str, Any]:
        """List all available workflow templates"""
        url = f"{self.base_url}/workflows/templates/"
        params = {'category': category} if category else {}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_template_detail(self, template_id: str) -> dict[str, Any]:
        """Get detailed information about a workflow template"""
        url = f"{self.base_url}/workflows/{template_id}/template_detail/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def execute_workflow(
        self, 
        workflow_id: str, 
        input_data: dict[str, Any],
        session_id: str | None = None
    ) -> dict[str, Any]:
        """Execute a workflow synchronously"""
        url = f"{self.base_url}/workflows/execute/"
        payload = {
            'workflow_id': workflow_id,
            'input_data': input_data,
            'session_id': session_id
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def execute_async(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
        session_id: str | None = None
    ) -> dict[str, Any]:
        """Execute a workflow asynchronously"""
        url = f"{self.base_url}/workflows/execute_async/"
        payload = {
            'workflow_id': workflow_id,
            'input_data': input_data,
            'session_id': session_id
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_status(self, execution_id: str) -> dict[str, Any]:
        """Get status of a workflow execution"""
        url = f"{self.base_url}/workflows/{execution_id}/status/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def quick_start(self, use_case: str, input_text: str) -> dict[str, Any]:
        """Execute a quick start workflow"""
        url = f"{self.base_url}/workflows/quick_start/"
        payload = {
            'use_case': use_case,
            'input': input_text
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def example_1_data_analysis():
    """Example: Automated Data Analysis"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Automated Data Analysis")
    print("="*60)
    
    client = WorkflowClient()
    
    # Execute data analysis workflow
    print("\n📊 Analyzing sales data...")
    result = client.execute_workflow(
        workflow_id='data_analysis_pipeline',
        input_data={
            'data_source': 'sales_data_2024.csv',
            'analysis_type': 'descriptive',
            'output_format': 'report'
        }
    )
    
    print(f"✅ Workflow completed in {result['execution_time']:.2f}s")
    print(f"📈 Steps completed: {result['steps_completed']}/{result['total_steps']}")
    print(f"📋 Status: {result['status']}")
    
    # Display step details
    print("\n📝 Execution Steps:")
    for step in result['step_details']:
        status_icon = "✅" if step['status'] == 'completed' else "❌"
        print(f"  {status_icon} {step['name']} ({step['execution_time']:.2f}s)")
    
    return result


def example_2_customer_support():
    """Example: Automated Customer Support"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Customer Support Automation")
    print("="*60)
    
    client = WorkflowClient()
    
    # Handle support ticket
    print("\n🎫 Processing customer support ticket...")
    result = client.execute_workflow(
        workflow_id='customer_support_ticket',
        input_data={
            'ticket_id': 'TICK-12345',
            'customer_message': 'I cannot login to my account. I keep getting an error message.',
            'customer_id': 'CUST-789',
            'priority': 'high'
        }
    )
    
    print(f"✅ Ticket processed in {result['execution_time']:.2f}s")
    print(f"📊 Steps completed: {result['steps_completed']}/{result['total_steps']}")
    
    # Check if escalation is needed
    if 'step_6_escalation_check' in result['results']:
        escalation = result['results']['step_6_escalation_check']
        print(f"\n🔔 Escalation needed: {escalation.get('escalation_decision', 'Unknown')}")
    
    return result


def example_3_code_review():
    """Example: Automated Code Review"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Automated Code Review")
    print("="*60)
    
    client = WorkflowClient()
    
    # Execute code review
    print("\n🔍 Running code review...")
    result = client.execute_workflow(
        workflow_id='code_review_process',
        input_data={
            'repository': 'https://github.com/username/project',
            'branch': 'feature/new-feature',
            'files_changed': ['src/main.py', 'tests/test_main.py'],
            'pr_description': 'Added new authentication feature'
        }
    )
    
    print(f"✅ Review completed in {result['execution_time']:.2f}s")
    print(f"📊 Steps: {result['steps_completed']}/{result['total_steps']}")
    
    return result


def example_4_content_creation():
    """Example: Automated Content Creation"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Content Creation Pipeline")
    print("="*60)
    
    client = WorkflowClient()
    
    # Create content
    print("\n✍️  Creating content...")
    result = client.execute_workflow(
        workflow_id='content_creation_workflow',
        input_data={
            'topic': 'The Impact of AI on Modern Business',
            'content_type': 'blog',
            'target_audience': 'business_professionals',
            'length': 'medium',
            'tone': 'professional'
        }
    )
    
    print(f"✅ Content created in {result['execution_time']:.2f}s")
    print(f"📝 Steps completed: {result['steps_completed']}/{result['total_steps']}")
    
    return result


def example_5_quick_start():
    """Example: Quick Start Workflows"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Quick Start Workflows")
    print("="*60)
    
    client = WorkflowClient()
    
    # Example 5.1: Quick research
    print("\n🔬 Quick Research...")
    result = client.quick_start(
        use_case='research',
        input_text='What are the latest trends in artificial intelligence?'
    )
    print(f"✅ Research completed: {result['result']['workflow_name']}")
    
    # Example 5.2: Quick data analysis
    print("\n📊 Quick Data Analysis...")
    result = client.quick_start(
        use_case='analyze_data',
        input_text='monthly_sales.csv'
    )
    print(f"✅ Analysis completed: {result['result']['workflow_name']}")
    
    return result


def example_6_bug_investigation():
    """Example: Bug Investigation and Fix"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Bug Investigation")
    print("="*60)
    
    client = WorkflowClient()
    
    # Investigate bug
    print("\n🐛 Investigating bug...")
    result = client.execute_workflow(
        workflow_id='bug_investigation',
        input_data={
            'bug_description': 'Application crashes when user tries to save large files',
            'error_logs': 'MemoryError: Out of memory at line 245',
            'steps_to_reproduce': [
                'Open application',
                'Load file > 100MB',
                'Click Save button'
            ],
            'affected_systems': ['file_handler', 'storage']
        }
    )
    
    print(f"✅ Investigation completed in {result['execution_time']:.2f}s")
    print(f"🔧 Steps: {result['steps_completed']}/{result['total_steps']}")
    
    # Show root cause if found
    if 'step_3_root_cause_analysis' in result['results']:
        root_cause = result['results']['step_3_root_cause_analysis']
        print(f"\n🎯 Root Cause: {root_cause.get('root_cause', 'Not determined')}")
    
    return result


def example_7_list_templates():
    """Example: List and Explore Templates"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Exploring Available Templates")
    print("="*60)
    
    client = WorkflowClient()
    
    # List all templates
    print("\n📚 Available Workflow Templates:")
    templates = client.list_templates()
    
    for template in templates['templates']:
        print(f"\n  📋 {template['name']}")
        print(f"     ID: {template['id']}")
        print(f"     Category: {template['category']}")
        print(f"     Steps: {template['step_count']}")
        print(f"     Description: {template['description']}")
    
    # Get detailed info for one template
    print("\n" + "-"*60)
    print("📖 Detailed Template Information:")
    detail = client.get_template_detail('data_analysis_pipeline')
    
    print(f"\nTemplate: {detail['name']}")
    print("Steps in workflow:")
    for step in detail['steps']:
        print(f"  {step['id']}: {step['name']}")
        print(f"    - Agent Type: {step['agent_type']}")
        print(f"    - Dependencies: {', '.join(step['dependencies']) or 'None'}")
    
    return templates


def run_all_examples():
    """Run all examples"""
    print("\n" + "="*60)
    print("MULTI-AGENT WORKFLOW SYSTEM - EXAMPLES")
    print("="*60)
    print("\nThis script demonstrates various real-world workflows")
    print("Make sure the backend server is running on http://localhost:8000")
    print("\nPress Ctrl+C to stop at any time")
    print("="*60)
    
    try:
        # List available templates
        example_7_list_templates()
        
        # Run workflow examples
        print("\n\n🚀 Starting workflow examples...\n")
        
        # Example 1: Data Analysis
        example_1_data_analysis()
        time.sleep(2)
        
        # Example 2: Customer Support
        example_2_customer_support()
        time.sleep(2)
        
        # Example 3: Code Review
        example_3_code_review()
        time.sleep(2)
        
        # Example 4: Content Creation
        example_4_content_creation()
        time.sleep(2)
        
        # Example 5: Quick Start
        example_5_quick_start()
        time.sleep(2)
        
        # Example 6: Bug Investigation
        example_6_bug_investigation()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n\n❌ Error: Cannot connect to backend server")
        print("Please make sure the server is running on http://localhost:8000")
    except Exception as e:  # noqa: BLE001
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # You can run individual examples or all of them
    
    # Run all examples
    run_all_examples()
    
    # Or run individual examples:
    # example_1_data_analysis()
    # example_2_customer_support()
    # example_3_code_review()
    # example_4_content_creation()
    # example_5_quick_start()
    # example_6_bug_investigation()
    # example_7_list_templates()
