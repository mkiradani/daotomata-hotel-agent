#!/usr/bin/env python3
"""
Main script for running comprehensive AI evaluation tests on the hotel agent.

This script provides a command-line interface for running various types of tests:
- Tool functionality tests
- Conversation simulations with AI evaluation
- Secondary analysis of evaluation results

Usage:
    python -m tests.ai_evaluation.main --help
    python -m tests.ai_evaluation.main --run-all
    python -m tests.ai_evaluation.main --tools-only
    python -m tests.ai_evaluation.main --conversations-only
    python -m tests.ai_evaluation.main --scenarios basic_info_inquiry availability_check
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Ensure we can import from project root
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from openai import AsyncOpenAI

from .config import TEST_SCENARIOS, TEST_HOTELS
from .simulator import ConversationSimulator
from .evaluator import AIEvaluator
from .secondary_evaluator import AdvancedSecondaryEvaluator
from .tool_tests import HotelToolTester
from .logger import ConversationLogger


class AIEvaluationRunner:
    """Main runner for AI evaluation tests."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the evaluation runner.
        
        Args:
            openai_api_key: Optional OpenAI API key. If not provided, will use environment variable.
        """
        self.openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else AsyncOpenAI()
        self.logger = ConversationLogger()
        
        # Initialize components
        self.tool_tester = HotelToolTester()
        self.conversation_simulator = ConversationSimulator(self.openai_client)
        self.ai_evaluator = AIEvaluator(self.openai_client)
        self.secondary_evaluator = AdvancedSecondaryEvaluator(self.openai_client)
    
    async def run_tool_tests(
        self,
        hotel_ids: Optional[List[str]] = None,
        export_results: bool = True
    ) -> str:
        """Run comprehensive tool functionality tests.
        
        Args:
            hotel_ids: Optional list of hotel IDs to test
            export_results: Whether to export results to JSON
            
        Returns:
            Path to exported results file if exported, otherwise empty string
        """
        self.logger.log_info("Starting tool functionality tests")
        
        # Run tool tests
        test_results = await self.tool_tester.test_all_tools(hotel_ids)
        
        # Analyze results
        analysis = self.tool_tester.analyze_tool_results()
        
        # Log summary
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results if r.success])
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        self.logger.log_info(
            f"Tool tests completed: {successful_tests}/{total_tests} successful ({success_rate:.1%})"
        )
        
        # Export results
        export_path = ""
        if export_results:
            export_path = self.tool_tester.export_results_to_json()
            self.logger.log_info(f"Tool test results exported to: {export_path}")
        
        return export_path
    
    async def run_conversation_tests(
        self,
        scenario_ids: Optional[List[str]] = None,
        hotel_ids: Optional[List[str]] = None,
        include_secondary_analysis: bool = True
    ) -> tuple[str, Optional[str]]:
        """Run conversation simulation and evaluation tests.
        
        Args:
            scenario_ids: Optional list of scenario IDs to test
            hotel_ids: Optional list of hotel IDs to test
            include_secondary_analysis: Whether to perform secondary analysis
            
        Returns:
            Tuple of (primary_results_path, secondary_analysis_path)
        """
        self.logger.log_info("Starting conversation simulation and evaluation tests")
        
        # Run conversation simulations
        simulation_results = await self.conversation_simulator.run_all_scenarios(
            hotel_filter=hotel_ids,
            scenario_filter=scenario_ids
        )
        
        if not simulation_results:
            self.logger.log_error("No conversation simulations completed successfully")
            return "", None
        
        self.logger.log_info(f"Completed {len(simulation_results)} conversation simulations")
        
        # Run AI evaluations
        scenarios_map = {s.scenario_id: s for s in TEST_SCENARIOS}
        evaluations = await self.ai_evaluator.evaluate_multiple_conversations(
            simulation_results, list(scenarios_map.values())
        )
        
        if not evaluations:
            self.logger.log_error("No evaluations completed successfully")
            return "", None
        
        self.logger.log_info(f"Completed {len(evaluations)} conversation evaluations")
        
        # Log evaluation results to the conversation logger
        for evaluation in evaluations:
            dimension_scores = {score.dimension: score.score for score in evaluation.scores}
            
            self.logger.log_evaluation(
                conversation_id=evaluation.conversation_id,
                scenario_id=evaluation.scenario_id,
                hotel_id=evaluation.hotel_id,
                overall_score=evaluation.overall_score,
                passed=evaluation.passed,
                dimension_scores=dimension_scores,
                tools_expected=evaluation.expected_tools_used,
                tools_used=evaluation.actual_tools_used,
                missing_tools=evaluation.missing_tools,
                evaluation_summary=evaluation.summary,
                recommendations=evaluation.recommendations
            )
        
        # Generate session summary
        summary = self.logger.generate_session_summary({
            "total_simulations": len(simulation_results),
            "total_evaluations": len(evaluations),
            "scenarios_tested": list(set(e.scenario_id for e in evaluations)),
            "hotels_tested": list(set(e.hotel_id for e in evaluations))
        })
        
        # Export to CSV
        csv_path = self.logger.export_to_csv()
        
        self.logger.log_info(f"Primary evaluation results exported to CSV: {csv_path}")
        
        # Perform secondary analysis if requested
        secondary_report_path = None
        if include_secondary_analysis:
            self.logger.log_info("Starting secondary analysis")
            
            secondary_analysis = await self.secondary_evaluator.perform_comprehensive_analysis(
                evaluations, simulation_results, self.logger
            )
            
            secondary_report_path = await self.secondary_evaluator.export_analysis_report(
                secondary_analysis
            )
            
            self.logger.log_info(
                f"Secondary analysis completed - Score: {secondary_analysis.system_performance_score:.3f}, "
                f"Confidence: {secondary_analysis.confidence_score:.3f}"
            )
            self.logger.log_info(f"Secondary analysis report exported to: {secondary_report_path}")
        
        return csv_path, secondary_report_path
    
    async def run_comprehensive_evaluation(
        self,
        scenario_ids: Optional[List[str]] = None,
        hotel_ids: Optional[List[str]] = None
    ) -> dict:
        """Run comprehensive evaluation including tools, conversations, and secondary analysis.
        
        Args:
            scenario_ids: Optional list of scenario IDs to test
            hotel_ids: Optional list of hotel IDs to test
            
        Returns:
            Dictionary with all result file paths
        """
        self.logger.log_info("Starting comprehensive AI evaluation suite")
        
        results = {
            "started_at": datetime.now().isoformat(),
            "tool_results_path": "",
            "conversation_results_path": "",
            "secondary_analysis_path": "",
            "session_summary": {}
        }
        
        try:
            # Run tool tests
            self.logger.log_info("Phase 1: Tool functionality testing")
            tool_results_path = await self.run_tool_tests(hotel_ids, export_results=True)
            results["tool_results_path"] = tool_results_path
            
            # Run conversation tests with secondary analysis
            self.logger.log_info("Phase 2: Conversation simulation and evaluation")
            conversation_path, secondary_path = await self.run_conversation_tests(
                scenario_ids, hotel_ids, include_secondary_analysis=True
            )
            results["conversation_results_path"] = conversation_path
            results["secondary_analysis_path"] = secondary_path
            
            # Generate final session summary
            session_summary = self.logger.generate_session_summary({
                "evaluation_type": "comprehensive",
                "phases_completed": ["tool_tests", "conversations", "secondary_analysis"],
                "total_duration": (datetime.now() - datetime.fromisoformat(results["started_at"])).total_seconds()
            })
            results["session_summary"] = session_summary
            
            self.logger.log_info("Comprehensive evaluation completed successfully")
            
            # Print summary to console
            self._print_evaluation_summary(results, session_summary)
            
        except Exception as e:
            self.logger.log_error(f"Comprehensive evaluation failed: {str(e)}")
            results["error"] = str(e)
        
        results["completed_at"] = datetime.now().isoformat()
        
        return results
    
    def _print_evaluation_summary(self, results: dict, session_summary: dict):
        """Print evaluation summary to console."""
        
        print("\n" + "="*80)
        print("🤖 AI EVALUATION SUITE - RESULTS SUMMARY")
        print("="*80)
        
        print(f"\n📊 OVERALL STATISTICS:")
        stats = session_summary.get("statistics", {})
        print(f"   • Total Conversations: {stats.get('total_conversations', 0)}")
        print(f"   • Total Evaluations: {stats.get('total_evaluations', 0)}")
        print(f"   • Pass Rate: {stats.get('pass_rate', 0):.1%}")
        print(f"   • Average Score: {stats.get('average_score', 0):.3f}")
        print(f"   • Tool Coverage: {stats.get('tool_coverage', 0):.1%}")
        
        print(f"\n🎯 DIMENSION SCORES:")
        dimension_scores = session_summary.get("dimension_scores", {})
        for dimension, score in dimension_scores.items():
            print(f"   • {dimension.title()}: {score:.3f}")
        
        print(f"\n🔧 TOOL USAGE:")
        tool_usage = session_summary.get("tool_usage", {})
        print(f"   • Expected Tools: {len(tool_usage.get('expected_tools', []))}")
        print(f"   • Used Tools: {len(tool_usage.get('used_tools', []))}")
        print(f"   • Coverage Rate: {tool_usage.get('coverage_rate', 0):.1%}")
        
        print(f"\n⚠️  TOP ISSUES:")
        top_issues = session_summary.get("top_issues", [])[:3]
        for i, issue_data in enumerate(top_issues, 1):
            if isinstance(issue_data, dict):
                issue = issue_data.get("issue", "Unknown issue")
                freq = issue_data.get("frequency", 0)
                print(f"   {i}. {issue} (frequency: {freq})")
            else:
                print(f"   {i}. {issue_data}")
        
        print(f"\n📁 OUTPUT FILES:")
        if results.get("tool_results_path"):
            print(f"   • Tool Tests: {results['tool_results_path']}")
        if results.get("conversation_results_path"):
            print(f"   • Conversations: {results['conversation_results_path']}")
        if results.get("secondary_analysis_path"):
            print(f"   • Secondary Analysis: {results['secondary_analysis_path']}")
        
        print(f"\n💡 NEXT STEPS:")
        print("   1. Review detailed results in the exported files")
        print("   2. Focus on improving tools with low success rates")
        print("   3. Address common failure patterns identified")
        print("   4. Optimize conversation flows based on AI feedback")
        
        print("\n" + "="*80)


async def main():
    """Main entry point for the AI evaluation suite."""
    
    parser = argparse.ArgumentParser(
        description="Comprehensive AI Evaluation Suite for Hotel Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --run-all                           # Run complete evaluation suite
  %(prog)s --tools-only                       # Run only tool tests
  %(prog)s --conversations-only               # Run only conversation tests
  %(prog)s --scenarios basic_info_inquiry availability_check   # Test specific scenarios
  %(prog)s --hotels hotel_madrid_luxury       # Test specific hotel
  %(prog)s --no-secondary                     # Skip secondary analysis
        """
    )
    
    # Main action groups
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--run-all", 
        action="store_true",
        help="Run comprehensive evaluation (tools + conversations + secondary analysis)"
    )
    action_group.add_argument(
        "--tools-only", 
        action="store_true",
        help="Run only tool functionality tests"
    )
    action_group.add_argument(
        "--conversations-only", 
        action="store_true",
        help="Run only conversation simulation and evaluation tests"
    )
    
    # Filtering options
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=[s.scenario_id for s in TEST_SCENARIOS],
        help="Specific scenarios to test"
    )
    parser.add_argument(
        "--hotels",
        nargs="+",
        choices=[h.id for h in TEST_HOTELS],
        help="Specific hotels to test"
    )
    
    # Analysis options
    parser.add_argument(
        "--no-secondary",
        action="store_true",
        help="Skip secondary analysis (applies to --run-all and --conversations-only)"
    )
    
    # Output options
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip exporting results to files"
    )
    
    # API configuration
    parser.add_argument(
        "--openai-api-key",
        help="OpenAI API key (if not set as environment variable)"
    )
    
    # Verbosity
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    try:
        runner = AIEvaluationRunner(openai_api_key=args.openai_api_key)
    except Exception as e:
        print(f"❌ Error initializing AI Evaluation Runner: {e}")
        print("💡 Make sure your OpenAI API key is set correctly.")
        sys.exit(1)
    
    # Run requested tests
    try:
        if args.run_all:
            print("🚀 Starting comprehensive AI evaluation suite...")
            results = await runner.run_comprehensive_evaluation(
                scenario_ids=args.scenarios,
                hotel_ids=args.hotels
            )
            
            if "error" in results:
                print(f"❌ Evaluation failed: {results['error']}")
                sys.exit(1)
            else:
                print("✅ Comprehensive evaluation completed successfully!")
        
        elif args.tools_only:
            print("🔧 Starting tool functionality tests...")
            results_path = await runner.run_tool_tests(
                hotel_ids=args.hotels,
                export_results=not args.no_export
            )
            
            if results_path:
                print(f"✅ Tool tests completed! Results: {results_path}")
            else:
                print("✅ Tool tests completed!")
        
        elif args.conversations_only:
            print("💬 Starting conversation simulation and evaluation tests...")
            conversation_path, secondary_path = await runner.run_conversation_tests(
                scenario_ids=args.scenarios,
                hotel_ids=args.hotels,
                include_secondary_analysis=not args.no_secondary
            )
            
            print(f"✅ Conversation tests completed!")
            if conversation_path:
                print(f"   📊 Primary results: {conversation_path}")
            if secondary_path:
                print(f"   🔍 Secondary analysis: {secondary_path}")
    
    except KeyboardInterrupt:
        print("\n⏹️  Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Ensure event loop is properly handled
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)