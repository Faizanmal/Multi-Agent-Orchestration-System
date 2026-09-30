# backend/agents/services/workflow_templates.py
"""
Real-world workflow templates for common business and development tasks.
These templates define multi-agent coordination for solving actual problems.
"""

from enum import Enum


class WorkflowCategory(Enum):
    """Categories of workflows available"""
    DATA_ANALYSIS = "data_analysis"
    CUSTOMER_SUPPORT = "customer_support"
    CONTENT_CREATION = "content_creation"
    CODE_DEVELOPMENT = "code_development"
    RESEARCH = "research"
    TESTING = "testing"
    AUTOMATION = "automation"
    DOCUMENTATION = "documentation"


class WorkflowTemplates:
    """Predefined templates for real-world agent workflows"""
    
    @staticmethod
    def get_all_templates() -> dict[str, dict]:
        """Get all available workflow templates"""
        return {
            'data_analysis_pipeline': WorkflowTemplates.data_analysis_pipeline(),
            'customer_support_ticket': WorkflowTemplates.customer_support_ticket(),
            'content_creation_workflow': WorkflowTemplates.content_creation_workflow(),
            'code_review_process': WorkflowTemplates.code_review_process(),
            'bug_investigation': WorkflowTemplates.bug_investigation(),
            'research_and_summarize': WorkflowTemplates.research_and_summarize(),
            'document_generation': WorkflowTemplates.document_generation(),
            'automated_testing': WorkflowTemplates.automated_testing(),
            'data_quality_check': WorkflowTemplates.data_quality_check(),
            'onboarding_automation': WorkflowTemplates.onboarding_automation(),
        }
    
    @staticmethod
    def data_analysis_pipeline() -> dict:
        """
        Multi-agent workflow for comprehensive data analysis.
        Agents: Vision (for charts/graphs), Reasoning (for analysis), Action (for processing)
        """
        return {
            'id': 'data_analysis_pipeline',
            'name': 'Data Analysis Pipeline',
            'description': 'Automated data analysis with visualization and insights',
            'category': WorkflowCategory.DATA_ANALYSIS.value,
            'input_schema': {
                'data_source': 'string',  # File path or URL
                'analysis_type': 'string',  # 'descriptive', 'predictive', 'diagnostic'
                'output_format': 'string',  # 'report', 'dashboard', 'presentation'
            },
            'steps': [
                {
                    'id': 'step_1_data_ingestion',
                    'name': 'Data Ingestion',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'load_and_validate_data',
                        'capabilities_required': ['data_processing', 'file_handling'],
                        'timeout': 300,
                    },
                    'dependencies': [],
                    'outputs': ['raw_data', 'data_schema', 'validation_report'],
                },
                {
                    'id': 'step_2_data_cleaning',
                    'name': 'Data Cleaning and Preprocessing',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'clean_and_preprocess',
                        'operations': ['handle_missing', 'remove_duplicates', 'normalize'],
                        'capabilities_required': ['data_processing'],
                    },
                    'dependencies': ['step_1_data_ingestion'],
                    'outputs': ['cleaned_data', 'preprocessing_log'],
                },
                {
                    'id': 'step_3_exploratory_analysis',
                    'name': 'Exploratory Data Analysis',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'perform_eda',
                        'analysis_types': ['statistics', 'distributions', 'correlations'],
                        'capabilities_required': ['statistical_analysis', 'reasoning'],
                    },
                    'dependencies': ['step_2_data_cleaning'],
                    'outputs': ['statistics', 'insights', 'anomalies'],
                },
                {
                    'id': 'step_4_visualization',
                    'name': 'Create Visualizations',
                    'type': 'agent_task',
                    'agent_type': 'vision',
                    'config': {
                        'task': 'create_visualizations',
                        'chart_types': ['distribution', 'correlation', 'trends'],
                        'capabilities_required': ['visualization', 'image_generation'],
                    },
                    'dependencies': ['step_3_exploratory_analysis'],
                    'outputs': ['charts', 'graphs', 'visual_insights'],
                },
                {
                    'id': 'step_5_insight_generation',
                    'name': 'Generate Insights and Recommendations',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'generate_insights',
                        'focus': ['patterns', 'trends', 'recommendations'],
                        'capabilities_required': ['reasoning', 'strategic_thinking'],
                    },
                    'dependencies': ['step_3_exploratory_analysis', 'step_4_visualization'],
                    'outputs': ['key_insights', 'recommendations', 'action_items'],
                },
                {
                    'id': 'step_6_report_generation',
                    'name': 'Generate Final Report',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'compile_report',
                        'sections': ['executive_summary', 'findings', 'visualizations', 'recommendations'],
                        'capabilities_required': ['document_generation', 'synthesis'],
                    },
                    'dependencies': ['step_4_visualization', 'step_5_insight_generation'],
                    'outputs': ['final_report', 'presentation'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 3,
                'fallback_strategy': 'partial_results',
            },
            'success_criteria': {
                'minimum_steps_completed': 4,
                'required_outputs': ['cleaned_data', 'insights', 'final_report'],
            },
        }
    
    @staticmethod
    def customer_support_ticket() -> dict:
        """
        Multi-agent workflow for handling customer support tickets.
        Agents: Reasoning (understand issue), Memory (check history), Action (resolve)
        """
        return {
            'id': 'customer_support_ticket',
            'name': 'Customer Support Automation',
            'description': 'Automated ticket triage, investigation, and resolution',
            'category': WorkflowCategory.CUSTOMER_SUPPORT.value,
            'input_schema': {
                'ticket_id': 'string',
                'customer_message': 'string',
                'customer_id': 'string',
                'priority': 'string',  # 'low', 'medium', 'high', 'critical'
            },
            'steps': [
                {
                    'id': 'step_1_ticket_analysis',
                    'name': 'Analyze Ticket Content',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'analyze_support_ticket',
                        'extract': ['issue_type', 'sentiment', 'urgency', 'key_topics'],
                        'capabilities_required': ['nlp', 'reasoning', 'sentiment_analysis'],
                    },
                    'dependencies': [],
                    'outputs': ['issue_classification', 'sentiment_score', 'extracted_entities'],
                },
                {
                    'id': 'step_2_history_lookup',
                    'name': 'Check Customer History',
                    'type': 'agent_task',
                    'agent_type': 'memory',
                    'config': {
                        'task': 'retrieve_customer_context',
                        'search_scope': ['previous_tickets', 'interactions', 'preferences'],
                        'capabilities_required': ['memory_retrieval', 'context_building'],
                    },
                    'dependencies': ['step_1_ticket_analysis'],
                    'outputs': ['customer_history', 'previous_issues', 'interaction_context'],
                },
                {
                    'id': 'step_3_knowledge_search',
                    'name': 'Search Knowledge Base',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'search_knowledge_base',
                        'search_types': ['solutions', 'faqs', 'documentation'],
                        'capabilities_required': ['search', 'information_retrieval'],
                    },
                    'dependencies': ['step_1_ticket_analysis'],
                    'outputs': ['relevant_solutions', 'documentation_links', 'similar_cases'],
                },
                {
                    'id': 'step_4_solution_generation',
                    'name': 'Generate Solution',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'formulate_solution',
                        'consider': ['best_practices', 'customer_context', 'company_policies'],
                        'capabilities_required': ['reasoning', 'problem_solving'],
                    },
                    'dependencies': ['step_2_history_lookup', 'step_3_knowledge_search'],
                    'outputs': ['proposed_solution', 'alternative_solutions', 'estimated_resolution_time'],
                },
                {
                    'id': 'step_5_response_crafting',
                    'name': 'Craft Customer Response',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'generate_response',
                        'tone': 'professional_empathetic',
                        'include': ['solution', 'steps', 'alternatives', 'follow_up'],
                        'capabilities_required': ['writing', 'communication'],
                    },
                    'dependencies': ['step_4_solution_generation'],
                    'outputs': ['customer_response', 'internal_notes'],
                },
                {
                    'id': 'step_6_escalation_check',
                    'name': 'Check if Escalation Needed',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'evaluate_escalation',
                        'criteria': ['complexity', 'priority', 'confidence_level'],
                        'capabilities_required': ['decision_making'],
                    },
                    'dependencies': ['step_4_solution_generation'],
                    'outputs': ['escalation_decision', 'escalation_reason', 'suggested_handler'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 2,
                'fallback_strategy': 'escalate_to_human',
            },
            'success_criteria': {
                'minimum_steps_completed': 5,
                'required_outputs': ['customer_response', 'escalation_decision'],
            },
        }
    
    @staticmethod
    def code_review_process() -> dict:
        """
        Multi-agent workflow for automated code review.
        Agents: Action (run tests), Reasoning (analyze code), Orchestrator (summarize)
        """
        return {
            'id': 'code_review_process',
            'name': 'Automated Code Review',
            'description': 'Comprehensive code review with testing and recommendations',
            'category': WorkflowCategory.CODE_DEVELOPMENT.value,
            'input_schema': {
                'repository': 'string',
                'branch': 'string',
                'files_changed': 'array',
                'pr_description': 'string',
            },
            'steps': [
                {
                    'id': 'step_1_code_analysis',
                    'name': 'Analyze Code Changes',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'analyze_code_changes',
                        'checks': ['syntax', 'style', 'complexity', 'patterns'],
                        'capabilities_required': ['code_analysis', 'pattern_recognition'],
                    },
                    'dependencies': [],
                    'outputs': ['code_issues', 'complexity_metrics', 'style_violations'],
                },
                {
                    'id': 'step_2_security_scan',
                    'name': 'Security Vulnerability Scan',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'security_scan',
                        'scan_types': ['vulnerabilities', 'secrets', 'dependencies'],
                        'capabilities_required': ['security_analysis', 'scanning'],
                    },
                    'dependencies': [],
                    'outputs': ['security_issues', 'vulnerability_report', 'risk_score'],
                },
                {
                    'id': 'step_3_test_execution',
                    'name': 'Run Automated Tests',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'run_tests',
                        'test_types': ['unit', 'integration', 'coverage'],
                        'capabilities_required': ['test_execution', 'environment_setup'],
                    },
                    'dependencies': [],
                    'outputs': ['test_results', 'coverage_report', 'failed_tests'],
                },
                {
                    'id': 'step_4_best_practices',
                    'name': 'Check Best Practices',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'evaluate_best_practices',
                        'criteria': ['design_patterns', 'performance', 'maintainability'],
                        'capabilities_required': ['reasoning', 'code_expertise'],
                    },
                    'dependencies': ['step_1_code_analysis'],
                    'outputs': ['best_practice_violations', 'improvement_suggestions'],
                },
                {
                    'id': 'step_5_documentation_check',
                    'name': 'Verify Documentation',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'check_documentation',
                        'check_for': ['comments', 'docstrings', 'readme_updates'],
                        'capabilities_required': ['documentation_analysis'],
                    },
                    'dependencies': ['step_1_code_analysis'],
                    'outputs': ['documentation_gaps', 'documentation_quality'],
                },
                {
                    'id': 'step_6_review_summary',
                    'name': 'Generate Review Summary',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'compile_review',
                        'sections': ['summary', 'critical_issues', 'suggestions', 'approval_status'],
                        'capabilities_required': ['synthesis', 'decision_making'],
                    },
                    'dependencies': ['step_1_code_analysis', 'step_2_security_scan', 
                                   'step_3_test_execution', 'step_4_best_practices', 
                                   'step_5_documentation_check'],
                    'outputs': ['review_summary', 'approval_decision', 'action_items'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 2,
                'fallback_strategy': 'partial_results',
            },
            'success_criteria': {
                'minimum_steps_completed': 5,
                'required_outputs': ['review_summary', 'approval_decision'],
            },
        }
    
    @staticmethod
    def content_creation_workflow() -> dict:
        """
        Multi-agent workflow for content creation.
        Agents: Reasoning (ideation), Action (research), Orchestrator (writing), Vision (graphics)
        """
        return {
            'id': 'content_creation_workflow',
            'name': 'Content Creation Pipeline',
            'description': 'End-to-end content creation with research and visuals',
            'category': WorkflowCategory.CONTENT_CREATION.value,
            'input_schema': {
                'topic': 'string',
                'content_type': 'string',  # 'blog', 'article', 'social', 'documentation'
                'target_audience': 'string',
                'length': 'string',  # 'short', 'medium', 'long'
                'tone': 'string',  # 'professional', 'casual', 'technical'
            },
            'steps': [
                {
                    'id': 'step_1_topic_research',
                    'name': 'Research Topic',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'research_topic',
                        'sources': ['web', 'knowledge_base', 'trends'],
                        'capabilities_required': ['research', 'information_gathering'],
                    },
                    'dependencies': [],
                    'outputs': ['research_findings', 'key_points', 'references'],
                },
                {
                    'id': 'step_2_outline_generation',
                    'name': 'Create Content Outline',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'generate_outline',
                        'structure': ['introduction', 'main_points', 'conclusion'],
                        'capabilities_required': ['reasoning', 'structure_planning'],
                    },
                    'dependencies': ['step_1_topic_research'],
                    'outputs': ['content_outline', 'section_breakdown'],
                },
                {
                    'id': 'step_3_content_writing',
                    'name': 'Write Content',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'write_content',
                        'style_guide': True,
                        'capabilities_required': ['writing', 'creativity'],
                    },
                    'dependencies': ['step_2_outline_generation'],
                    'outputs': ['draft_content', 'word_count'],
                },
                {
                    'id': 'step_4_fact_checking',
                    'name': 'Fact Check and Verify',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'verify_facts',
                        'check_claims': True,
                        'capabilities_required': ['reasoning', 'fact_checking'],
                    },
                    'dependencies': ['step_3_content_writing'],
                    'outputs': ['verification_report', 'corrections_needed'],
                },
                {
                    'id': 'step_5_visual_creation',
                    'name': 'Create Supporting Visuals',
                    'type': 'agent_task',
                    'agent_type': 'vision',
                    'config': {
                        'task': 'generate_visuals',
                        'visual_types': ['featured_image', 'diagrams', 'infographics'],
                        'capabilities_required': ['image_generation', 'design'],
                    },
                    'dependencies': ['step_2_outline_generation'],
                    'outputs': ['images', 'graphics', 'visual_assets'],
                },
                {
                    'id': 'step_6_seo_optimization',
                    'name': 'SEO Optimization',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'optimize_seo',
                        'optimize_for': ['keywords', 'meta_description', 'readability'],
                        'capabilities_required': ['seo', 'optimization'],
                    },
                    'dependencies': ['step_3_content_writing'],
                    'outputs': ['seo_score', 'optimization_suggestions', 'meta_tags'],
                },
                {
                    'id': 'step_7_final_polish',
                    'name': 'Final Review and Polish',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'finalize_content',
                        'checks': ['grammar', 'flow', 'consistency', 'formatting'],
                        'capabilities_required': ['editing', 'quality_assurance'],
                    },
                    'dependencies': ['step_4_fact_checking', 'step_6_seo_optimization'],
                    'outputs': ['final_content', 'publishing_package'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 2,
                'fallback_strategy': 'partial_results',
            },
            'success_criteria': {
                'minimum_steps_completed': 6,
                'required_outputs': ['final_content', 'visual_assets'],
            },
        }
    
    @staticmethod
    def bug_investigation() -> dict:
        """
        Multi-agent workflow for investigating and fixing bugs.
        """
        return {
            'id': 'bug_investigation',
            'name': 'Bug Investigation and Resolution',
            'description': 'Systematic bug investigation with root cause analysis',
            'category': WorkflowCategory.CODE_DEVELOPMENT.value,
            'input_schema': {
                'bug_description': 'string',
                'error_logs': 'string',
                'steps_to_reproduce': 'array',
                'affected_systems': 'array',
            },
            'steps': [
                {
                    'id': 'step_1_log_analysis',
                    'name': 'Analyze Error Logs',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'analyze_logs',
                        'extract': ['error_patterns', 'stack_traces', 'timestamps'],
                        'capabilities_required': ['log_analysis', 'pattern_recognition'],
                    },
                    'dependencies': [],
                    'outputs': ['error_patterns', 'potential_causes', 'affected_components'],
                },
                {
                    'id': 'step_2_reproduce_bug',
                    'name': 'Reproduce Bug',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'reproduce_bug',
                        'environment': 'isolated',
                        'capabilities_required': ['testing', 'environment_setup'],
                    },
                    'dependencies': ['step_1_log_analysis'],
                    'outputs': ['reproduction_success', 'reproduction_steps', 'failure_conditions'],
                },
                {
                    'id': 'step_3_root_cause_analysis',
                    'name': 'Root Cause Analysis',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'root_cause_analysis',
                        'methods': ['five_whys', 'fault_tree', 'timeline_analysis'],
                        'capabilities_required': ['reasoning', 'debugging', 'system_analysis'],
                    },
                    'dependencies': ['step_1_log_analysis', 'step_2_reproduce_bug'],
                    'outputs': ['root_cause', 'contributing_factors', 'impact_assessment'],
                },
                {
                    'id': 'step_4_solution_design',
                    'name': 'Design Solution',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'design_fix',
                        'considerations': ['correctness', 'performance', 'side_effects'],
                        'capabilities_required': ['reasoning', 'architecture', 'problem_solving'],
                    },
                    'dependencies': ['step_3_root_cause_analysis'],
                    'outputs': ['fix_design', 'implementation_plan', 'test_strategy'],
                },
                {
                    'id': 'step_5_implement_fix',
                    'name': 'Implement Fix',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'implement_fix',
                        'include': ['code_changes', 'tests', 'documentation'],
                        'capabilities_required': ['coding', 'testing'],
                    },
                    'dependencies': ['step_4_solution_design'],
                    'outputs': ['code_changes', 'test_cases', 'implementation_notes'],
                },
                {
                    'id': 'step_6_verification',
                    'name': 'Verify Fix',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'verify_fix',
                        'tests': ['regression', 'integration', 'edge_cases'],
                        'capabilities_required': ['testing', 'validation'],
                    },
                    'dependencies': ['step_5_implement_fix'],
                    'outputs': ['verification_results', 'test_coverage', 'regression_check'],
                },
                {
                    'id': 'step_7_documentation',
                    'name': 'Document Resolution',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'document_resolution',
                        'include': ['root_cause', 'fix', 'prevention', 'lessons_learned'],
                        'capabilities_required': ['documentation', 'communication'],
                    },
                    'dependencies': ['step_6_verification'],
                    'outputs': ['resolution_document', 'knowledge_base_entry'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 3,
                'fallback_strategy': 'escalate_to_senior',
            },
            'success_criteria': {
                'minimum_steps_completed': 6,
                'required_outputs': ['fix_design', 'verification_results', 'resolution_document'],
            },
        }
    
    @staticmethod
    def research_and_summarize() -> dict:
        """Research a topic and create comprehensive summary"""
        return {
            'id': 'research_and_summarize',
            'name': 'Research and Summarization',
            'description': 'Deep research with synthesis and summarization',
            'category': WorkflowCategory.RESEARCH.value,
            'input_schema': {
                'research_query': 'string',
                'depth': 'string',  # 'shallow', 'moderate', 'deep'
                'sources': 'array',
                'output_format': 'string',
            },
            'steps': [
                {
                    'id': 'step_1_query_expansion',
                    'name': 'Expand Research Query',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'expand_query',
                        'generate': ['sub_topics', 'related_terms', 'research_questions'],
                        'capabilities_required': ['reasoning', 'knowledge'],
                    },
                    'dependencies': [],
                    'outputs': ['expanded_queries', 'research_plan'],
                },
                {
                    'id': 'step_2_information_gathering',
                    'name': 'Gather Information',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'gather_information',
                        'sources': ['web', 'databases', 'documents'],
                        'capabilities_required': ['research', 'web_scraping', 'data_extraction'],
                    },
                    'dependencies': ['step_1_query_expansion'],
                    'outputs': ['raw_information', 'sources_list', 'credibility_scores'],
                },
                {
                    'id': 'step_3_information_filtering',
                    'name': 'Filter and Rank Information',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'filter_information',
                        'criteria': ['relevance', 'credibility', 'recency'],
                        'capabilities_required': ['reasoning', 'critical_thinking'],
                    },
                    'dependencies': ['step_2_information_gathering'],
                    'outputs': ['filtered_information', 'ranked_sources'],
                },
                {
                    'id': 'step_4_synthesis',
                    'name': 'Synthesize Findings',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'synthesize_information',
                        'methods': ['thematic_analysis', 'comparison', 'integration'],
                        'capabilities_required': ['reasoning', 'synthesis', 'critical_thinking'],
                    },
                    'dependencies': ['step_3_information_filtering'],
                    'outputs': ['synthesized_findings', 'key_themes', 'insights'],
                },
                {
                    'id': 'step_5_summary_generation',
                    'name': 'Generate Summary',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'generate_summary',
                        'formats': ['executive_summary', 'detailed_report', 'bullet_points'],
                        'capabilities_required': ['writing', 'summarization'],
                    },
                    'dependencies': ['step_4_synthesis'],
                    'outputs': ['summary', 'report', 'references'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 2,
                'fallback_strategy': 'partial_results',
            },
            'success_criteria': {
                'minimum_steps_completed': 4,
                'required_outputs': ['summary', 'references'],
            },
        }
    
    @staticmethod
    def document_generation() -> dict:
        """Generate technical or business documentation"""
        return {
            'id': 'document_generation',
            'name': 'Document Generation',
            'description': 'Automated creation of comprehensive documentation',
            'category': WorkflowCategory.DOCUMENTATION.value,
            'input_schema': {
                'document_type': 'string',  # 'api_docs', 'user_guide', 'technical_spec'
                'source_materials': 'array',
                'template': 'string',
                'target_audience': 'string',
            },
            'steps': [
                {
                    'id': 'step_1_content_extraction',
                    'name': 'Extract Source Content',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'extract_content',
                        'sources': ['code', 'comments', 'specs', 'notes'],
                        'capabilities_required': ['code_analysis', 'parsing'],
                    },
                    'dependencies': [],
                    'outputs': ['extracted_content', 'content_inventory'],
                },
                {
                    'id': 'step_2_structure_planning',
                    'name': 'Plan Document Structure',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'plan_structure',
                        'consider': ['audience', 'purpose', 'conventions'],
                        'capabilities_required': ['reasoning', 'documentation_expertise'],
                    },
                    'dependencies': ['step_1_content_extraction'],
                    'outputs': ['document_outline', 'section_plan'],
                },
                {
                    'id': 'step_3_content_generation',
                    'name': 'Generate Content',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'write_documentation',
                        'style': 'clear_and_concise',
                        'capabilities_required': ['writing', 'technical_writing'],
                    },
                    'dependencies': ['step_2_structure_planning'],
                    'outputs': ['draft_documentation', 'examples'],
                },
                {
                    'id': 'step_4_diagram_generation',
                    'name': 'Create Diagrams',
                    'type': 'agent_task',
                    'agent_type': 'vision',
                    'config': {
                        'task': 'create_diagrams',
                        'types': ['flowcharts', 'architecture', 'sequences'],
                        'capabilities_required': ['diagram_generation', 'visualization'],
                    },
                    'dependencies': ['step_2_structure_planning'],
                    'outputs': ['diagrams', 'visual_aids'],
                },
                {
                    'id': 'step_5_review_and_polish',
                    'name': 'Review and Polish',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'review_documentation',
                        'checks': ['accuracy', 'completeness', 'clarity', 'consistency'],
                        'capabilities_required': ['reasoning', 'quality_assurance'],
                    },
                    'dependencies': ['step_3_content_generation', 'step_4_diagram_generation'],
                    'outputs': ['review_feedback', 'improvements'],
                },
                {
                    'id': 'step_6_finalization',
                    'name': 'Finalize Documentation',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'finalize_documentation',
                        'output_formats': ['html', 'pdf', 'markdown'],
                        'capabilities_required': ['formatting', 'publishing'],
                    },
                    'dependencies': ['step_5_review_and_polish'],
                    'outputs': ['final_documentation', 'publication_package'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 2,
                'fallback_strategy': 'partial_results',
            },
            'success_criteria': {
                'minimum_steps_completed': 5,
                'required_outputs': ['final_documentation'],
            },
        }
    
    @staticmethod
    def automated_testing() -> dict:
        """Comprehensive automated testing workflow"""
        return {
            'id': 'automated_testing',
            'name': 'Automated Testing Suite',
            'description': 'Comprehensive testing with analysis and reporting',
            'category': WorkflowCategory.TESTING.value,
            'input_schema': {
                'test_target': 'string',
                'test_types': 'array',
                'coverage_goal': 'number',
            },
            'steps': [
                {
                    'id': 'step_1_test_planning',
                    'name': 'Plan Test Strategy',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'plan_tests',
                        'analyze': ['requirements', 'risks', 'priorities'],
                        'capabilities_required': ['reasoning', 'test_planning'],
                    },
                    'dependencies': [],
                    'outputs': ['test_plan', 'test_scenarios'],
                },
                {
                    'id': 'step_2_unit_tests',
                    'name': 'Execute Unit Tests',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'run_unit_tests',
                        'parallel': True,
                        'capabilities_required': ['testing', 'test_execution'],
                    },
                    'dependencies': ['step_1_test_planning'],
                    'outputs': ['unit_test_results', 'unit_coverage'],
                },
                {
                    'id': 'step_3_integration_tests',
                    'name': 'Execute Integration Tests',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'run_integration_tests',
                        'setup_dependencies': True,
                        'capabilities_required': ['testing', 'integration_testing'],
                    },
                    'dependencies': ['step_1_test_planning'],
                    'outputs': ['integration_test_results', 'integration_coverage'],
                },
                {
                    'id': 'step_4_performance_tests',
                    'name': 'Execute Performance Tests',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'run_performance_tests',
                        'metrics': ['latency', 'throughput', 'resource_usage'],
                        'capabilities_required': ['performance_testing', 'monitoring'],
                    },
                    'dependencies': ['step_1_test_planning'],
                    'outputs': ['performance_results', 'bottlenecks'],
                },
                {
                    'id': 'step_5_results_analysis',
                    'name': 'Analyze Test Results',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'analyze_results',
                        'identify': ['failures', 'patterns', 'regressions'],
                        'capabilities_required': ['reasoning', 'data_analysis'],
                    },
                    'dependencies': ['step_2_unit_tests', 'step_3_integration_tests', 'step_4_performance_tests'],
                    'outputs': ['analysis_report', 'failure_analysis', 'trends'],
                },
                {
                    'id': 'step_6_report_generation',
                    'name': 'Generate Test Report',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'generate_test_report',
                        'include': ['summary', 'metrics', 'recommendations'],
                        'capabilities_required': ['reporting', 'visualization'],
                    },
                    'dependencies': ['step_5_results_analysis'],
                    'outputs': ['test_report', 'dashboard'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': False,
                'max_retries': 1,
                'fallback_strategy': 'continue_other_steps',
            },
            'success_criteria': {
                'minimum_steps_completed': 5,
                'required_outputs': ['test_report'],
            },
        }
    
    @staticmethod
    def data_quality_check() -> dict:
        """Data quality assessment and remediation workflow"""
        return {
            'id': 'data_quality_check',
            'name': 'Data Quality Assessment',
            'description': 'Comprehensive data quality checking and improvement',
            'category': WorkflowCategory.DATA_ANALYSIS.value,
            'input_schema': {
                'data_source': 'string',
                'quality_dimensions': 'array',  # accuracy, completeness, consistency, timeliness
                'remediation_level': 'string',  # 'report_only', 'suggest', 'auto_fix'
            },
            'steps': [
                {
                    'id': 'step_1_data_profiling',
                    'name': 'Profile Data',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'profile_data',
                        'metrics': ['completeness', 'uniqueness', 'distributions'],
                        'capabilities_required': ['data_analysis', 'profiling'],
                    },
                    'dependencies': [],
                    'outputs': ['data_profile', 'statistics', 'metadata'],
                },
                {
                    'id': 'step_2_quality_checks',
                    'name': 'Run Quality Checks',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'check_quality',
                        'dimensions': ['accuracy', 'completeness', 'consistency', 'validity'],
                        'capabilities_required': ['data_analysis', 'quality_assessment'],
                    },
                    'dependencies': ['step_1_data_profiling'],
                    'outputs': ['quality_issues', 'severity_scores', 'issue_categories'],
                },
                {
                    'id': 'step_3_anomaly_detection',
                    'name': 'Detect Anomalies',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'detect_anomalies',
                        'methods': ['statistical', 'pattern_based', 'ml_based'],
                        'capabilities_required': ['anomaly_detection', 'statistical_analysis'],
                    },
                    'dependencies': ['step_1_data_profiling'],
                    'outputs': ['anomalies', 'anomaly_scores', 'explanations'],
                },
                {
                    'id': 'step_4_root_cause_analysis',
                    'name': 'Analyze Root Causes',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'analyze_root_causes',
                        'investigate': ['data_sources', 'transformations', 'business_rules'],
                        'capabilities_required': ['reasoning', 'root_cause_analysis'],
                    },
                    'dependencies': ['step_2_quality_checks', 'step_3_anomaly_detection'],
                    'outputs': ['root_causes', 'impact_assessment'],
                },
                {
                    'id': 'step_5_remediation_plan',
                    'name': 'Create Remediation Plan',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'create_remediation_plan',
                        'prioritize': True,
                        'capabilities_required': ['reasoning', 'planning'],
                    },
                    'dependencies': ['step_4_root_cause_analysis'],
                    'outputs': ['remediation_plan', 'prioritized_actions'],
                },
                {
                    'id': 'step_6_quality_report',
                    'name': 'Generate Quality Report',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'generate_quality_report',
                        'include': ['summary', 'issues', 'metrics', 'recommendations'],
                        'capabilities_required': ['reporting', 'visualization'],
                    },
                    'dependencies': ['step_5_remediation_plan'],
                    'outputs': ['quality_report', 'dashboard', 'action_items'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 2,
                'fallback_strategy': 'partial_results',
            },
            'success_criteria': {
                'minimum_steps_completed': 5,
                'required_outputs': ['quality_report', 'remediation_plan'],
            },
        }
    
    @staticmethod
    def onboarding_automation() -> dict:
        """Automated employee onboarding workflow"""
        return {
            'id': 'onboarding_automation',
            'name': 'Employee Onboarding Automation',
            'description': 'Automated onboarding process for new employees',
            'category': WorkflowCategory.AUTOMATION.value,
            'input_schema': {
                'employee_info': 'object',
                'department': 'string',
                'role': 'string',
                'start_date': 'string',
            },
            'steps': [
                {
                    'id': 'step_1_account_setup',
                    'name': 'Setup Accounts and Access',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'setup_accounts',
                        'systems': ['email', 'tools', 'permissions'],
                        'capabilities_required': ['automation', 'system_integration'],
                    },
                    'dependencies': [],
                    'outputs': ['accounts_created', 'credentials', 'access_list'],
                },
                {
                    'id': 'step_2_welcome_package',
                    'name': 'Prepare Welcome Package',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'prepare_welcome_package',
                        'include': ['handbook', 'resources', 'schedule'],
                        'capabilities_required': ['content_generation', 'personalization'],
                    },
                    'dependencies': [],
                    'outputs': ['welcome_package', 'personalized_materials'],
                },
                {
                    'id': 'step_3_training_plan',
                    'name': 'Create Training Plan',
                    'type': 'agent_task',
                    'agent_type': 'reasoning',
                    'config': {
                        'task': 'create_training_plan',
                        'customize_for': ['role', 'experience', 'department'],
                        'capabilities_required': ['planning', 'personalization'],
                    },
                    'dependencies': [],
                    'outputs': ['training_plan', 'milestones', 'resources'],
                },
                {
                    'id': 'step_4_team_introduction',
                    'name': 'Coordinate Team Introductions',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'schedule_introductions',
                        'schedule': ['one_on_ones', 'team_meetings', 'buddy_system'],
                        'capabilities_required': ['scheduling', 'coordination'],
                    },
                    'dependencies': [],
                    'outputs': ['meeting_schedule', 'introductions_planned'],
                },
                {
                    'id': 'step_5_equipment_setup',
                    'name': 'Setup Equipment and Workspace',
                    'type': 'agent_task',
                    'agent_type': 'action',
                    'config': {
                        'task': 'setup_equipment',
                        'items': ['hardware', 'software', 'workspace'],
                        'capabilities_required': ['automation', 'logistics'],
                    },
                    'dependencies': [],
                    'outputs': ['equipment_list', 'setup_status'],
                },
                {
                    'id': 'step_6_checklist_creation',
                    'name': 'Create Onboarding Checklist',
                    'type': 'agent_task',
                    'agent_type': 'orchestrator',
                    'config': {
                        'task': 'create_checklist',
                        'timeline': 'first_90_days',
                        'capabilities_required': ['planning', 'organization'],
                    },
                    'dependencies': ['step_1_account_setup', 'step_3_training_plan', 
                                   'step_4_team_introduction', 'step_5_equipment_setup'],
                    'outputs': ['onboarding_checklist', 'timeline', 'tracking_system'],
                },
            ],
            'error_handling': {
                'retry_failed_steps': True,
                'max_retries': 3,
                'fallback_strategy': 'notify_hr',
            },
            'success_criteria': {
                'minimum_steps_completed': 5,
                'required_outputs': ['onboarding_checklist', 'accounts_created'],
            },
        }


# Export all templates
def get_template(template_id: str) -> dict | None:
    """Get a specific template by ID"""
    templates = WorkflowTemplates.get_all_templates()
    return templates.get(template_id)


def list_templates_by_category(category: WorkflowCategory) -> list[dict]:
    """List all templates in a category"""
    templates = WorkflowTemplates.get_all_templates()
    return [
        template for template in templates.values()
        if template.get('category') == category.value
    ]
