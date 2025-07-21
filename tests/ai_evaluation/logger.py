"""Comprehensive logging system for AI evaluation tests."""

import json
import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict

from pydantic import BaseModel


@dataclass
class ConversationLogEntry:
    """Single conversation message log entry."""
    
    conversation_id: str
    timestamp: str
    role: str  # 'user' or 'assistant'
    content: str
    turn_number: int
    tools_used: List[str] = None
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tools_used is None:
            self.tools_used = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EvaluationLogEntry:
    """AI evaluation log entry."""
    
    conversation_id: str
    scenario_id: str
    hotel_id: str
    timestamp: str
    overall_score: float
    passed: bool
    dimension_scores: Dict[str, float]
    tools_expected: List[str]
    tools_used: List[str]
    missing_tools: List[str]
    evaluation_summary: str
    recommendations: List[str]
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ConversationLogger:
    """Comprehensive logging system for conversations and evaluations."""
    
    def __init__(self, log_dir: str = "logs/ai_evaluation"):
        """Initialize the conversation logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session ID for this run
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize storage
        self.conversation_logs: List[ConversationLogEntry] = []
        self.evaluation_logs: List[EvaluationLogEntry] = []
        
        # File paths for this session
        self.conversation_file = self.log_dir / f"conversations_{self.session_id}.jsonl"
        self.evaluation_file = self.log_dir / f"evaluations_{self.session_id}.jsonl"
        self.summary_file = self.log_dir / f"summary_{self.session_id}.json"
        self.csv_file = self.log_dir / f"results_{self.session_id}.csv"
        
        self.logger.info(f"Initialized conversation logger - Session: {self.session_id}")
    
    def _setup_logging(self):
        """Setup Python logging for the logger itself."""
        
        # Create logger
        self.logger = logging.getLogger(f"ai_evaluation_{self.session_id}")
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create file handler
        log_file = self.log_dir / f"system_{self.session_id}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_conversation(
        self,
        conversation_id: str,
        role: str,
        content: str,
        turn_number: int,
        tools_used: Optional[List[str]] = None,
        processing_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a conversation message.
        
        Args:
            conversation_id: Unique conversation identifier
            role: 'user' or 'assistant'
            content: Message content
            turn_number: Turn number in the conversation
            tools_used: List of tools used in this turn
            processing_time: Time taken to process the message
            metadata: Additional metadata
        """
        
        log_entry = ConversationLogEntry(
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            turn_number=turn_number,
            tools_used=tools_used or [],
            processing_time=processing_time,
            metadata=metadata or {}
        )
        
        self.conversation_logs.append(log_entry)
        
        # Write to file immediately for persistence
        self._write_conversation_entry(log_entry)
        
        self.logger.info(
            f"Logged conversation message: {conversation_id} - "
            f"{role} (turn {turn_number}) - "
            f"tools: {', '.join(tools_used) if tools_used else 'none'}"
        )
    
    def log_evaluation(
        self,
        conversation_id: str,
        scenario_id: str,
        hotel_id: str,
        overall_score: float,
        passed: bool,
        dimension_scores: Dict[str, float],
        tools_expected: List[str],
        tools_used: List[str],
        missing_tools: List[str],
        evaluation_summary: str,
        recommendations: List[str],
        execution_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an evaluation result.
        
        Args:
            conversation_id: Conversation that was evaluated
            scenario_id: Scenario identifier
            hotel_id: Hotel identifier
            overall_score: Overall evaluation score
            passed: Whether the evaluation passed
            dimension_scores: Scores for each evaluation dimension
            tools_expected: Tools that were expected to be used
            tools_used: Tools that were actually used
            missing_tools: Tools that were expected but not used
            evaluation_summary: Summary of the evaluation
            recommendations: Recommendations for improvement
            execution_time: Time taken for evaluation
            metadata: Additional metadata
        """
        
        log_entry = EvaluationLogEntry(
            conversation_id=conversation_id,
            scenario_id=scenario_id,
            hotel_id=hotel_id,
            timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            passed=passed,
            dimension_scores=dimension_scores,
            tools_expected=tools_expected,
            tools_used=tools_used,
            missing_tools=missing_tools,
            evaluation_summary=evaluation_summary,
            recommendations=recommendations,
            execution_time=execution_time,
            metadata=metadata or {}
        )
        
        self.evaluation_logs.append(log_entry)
        
        # Write to file immediately for persistence
        self._write_evaluation_entry(log_entry)
        
        self.logger.info(
            f"Logged evaluation: {conversation_id} - "
            f"Score: {overall_score:.3f} ({'PASSED' if passed else 'FAILED'}) - "
            f"Tools: {len(tools_used)}/{len(tools_expected)}"
        )
    
    def _write_conversation_entry(self, entry: ConversationLogEntry):
        """Write a conversation entry to JSONL file."""
        
        with open(self.conversation_file, 'a', encoding='utf-8') as f:
            json.dump(asdict(entry), f, ensure_ascii=False)
            f.write('\n')
    
    def _write_evaluation_entry(self, entry: EvaluationLogEntry):
        """Write an evaluation entry to JSONL file."""
        
        with open(self.evaluation_file, 'a', encoding='utf-8') as f:
            json.dump(asdict(entry), f, ensure_ascii=False)
            f.write('\n')
    
    def log_info(self, message: str, **kwargs):
        """Log an info message."""
        extra_info = f" - {kwargs}" if kwargs else ""
        self.logger.info(f"{message}{extra_info}")
    
    def log_error(self, message: str, conversation_id: Optional[str] = None, **kwargs):
        """Log an error message."""
        extra_info = f" - Conversation: {conversation_id}" if conversation_id else ""
        extra_info += f" - {kwargs}" if kwargs else ""
        self.logger.error(f"{message}{extra_info}")
    
    def log_warning(self, message: str, **kwargs):
        """Log a warning message."""
        extra_info = f" - {kwargs}" if kwargs else ""
        self.logger.warning(f"{message}{extra_info}")
    
    def generate_session_summary(self, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a comprehensive summary of the session.
        
        Args:
            additional_data: Additional data to include in summary
            
        Returns:
            Session summary dictionary
        """
        
        # Calculate basic statistics
        total_conversations = len(set(log.conversation_id for log in self.conversation_logs))
        total_evaluations = len(self.evaluation_logs)
        
        # Evaluation statistics
        passed_evaluations = sum(1 for log in self.evaluation_logs if log.passed)
        pass_rate = passed_evaluations / total_evaluations if total_evaluations > 0 else 0
        
        # Score statistics
        scores = [log.overall_score for log in self.evaluation_logs]
        avg_score = sum(scores) / len(scores) if scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0
        
        # Tool usage statistics
        all_expected_tools = set()
        all_used_tools = set()
        
        for log in self.evaluation_logs:
            all_expected_tools.update(log.tools_expected)
            all_used_tools.update(log.tools_used)
        
        tool_coverage = len(all_used_tools.intersection(all_expected_tools)) / len(all_expected_tools) if all_expected_tools else 0
        
        # Dimension statistics
        dimension_stats = {}
        for log in self.evaluation_logs:
            for dimension, score in log.dimension_scores.items():
                if dimension not in dimension_stats:
                    dimension_stats[dimension] = []
                dimension_stats[dimension].append(score)
        
        # Calculate averages for dimensions
        dimension_averages = {
            dimension: sum(scores) / len(scores)
            for dimension, scores in dimension_stats.items()
        }
        
        # Most common issues (from recommendations)
        all_recommendations = []
        for log in self.evaluation_logs:
            all_recommendations.extend(log.recommendations)
        
        # Count recommendation frequencies
        recommendation_counts = {}
        for rec in all_recommendations:
            # Simplify recommendation for counting
            simple_rec = rec.lower()[:50]  # First 50 chars
            recommendation_counts[simple_rec] = recommendation_counts.get(simple_rec, 0) + 1
        
        top_issues = sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_conversations": total_conversations,
                "total_evaluations": total_evaluations,
                "pass_rate": pass_rate,
                "average_score": avg_score,
                "min_score": min_score,
                "max_score": max_score,
                "tool_coverage": tool_coverage
            },
            "dimension_scores": dimension_averages,
            "tool_usage": {
                "expected_tools": list(all_expected_tools),
                "used_tools": list(all_used_tools),
                "coverage_rate": tool_coverage
            },
            "top_issues": [{"issue": issue, "frequency": freq} for issue, freq in top_issues],
            "files": {
                "conversations": str(self.conversation_file),
                "evaluations": str(self.evaluation_file),
                "summary": str(self.summary_file),
                "csv": str(self.csv_file)
            }
        }
        
        if additional_data:
            summary.update(additional_data)
        
        # Write summary to file
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(
            f"Generated session summary: {total_conversations} conversations, "
            f"{total_evaluations} evaluations, {pass_rate:.1%} pass rate"
        )
        
        return summary
    
    def export_to_csv(self) -> str:
        """Export evaluation results to CSV format.
        
        Returns:
            Path to the generated CSV file
        """
        
        if not self.evaluation_logs:
            self.logger.warning("No evaluation logs to export")
            return str(self.csv_file)
        
        # Prepare CSV data
        fieldnames = [
            'conversation_id', 'scenario_id', 'hotel_id', 'timestamp',
            'overall_score', 'passed', 'execution_time',
            'tools_expected_count', 'tools_used_count', 'missing_tools_count',
            'evaluation_summary'
        ]
        
        # Add dimension score columns
        if self.evaluation_logs:
            first_log = self.evaluation_logs[0]
            dimension_columns = [f'score_{dim}' for dim in first_log.dimension_scores.keys()]
            fieldnames.extend(dimension_columns)
        
        fieldnames.extend(['recommendations', 'tools_expected', 'tools_used', 'missing_tools'])
        
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in self.evaluation_logs:
                row = {
                    'conversation_id': log.conversation_id,
                    'scenario_id': log.scenario_id,
                    'hotel_id': log.hotel_id,
                    'timestamp': log.timestamp,
                    'overall_score': log.overall_score,
                    'passed': log.passed,
                    'execution_time': log.execution_time,
                    'tools_expected_count': len(log.tools_expected),
                    'tools_used_count': len(log.tools_used),
                    'missing_tools_count': len(log.missing_tools),
                    'evaluation_summary': log.evaluation_summary,
                    'recommendations': '; '.join(log.recommendations),
                    'tools_expected': ', '.join(log.tools_expected),
                    'tools_used': ', '.join(log.tools_used),
                    'missing_tools': ', '.join(log.missing_tools)
                }
                
                # Add dimension scores
                for dimension, score in log.dimension_scores.items():
                    row[f'score_{dimension}'] = score
                
                writer.writerow(row)
        
        self.logger.info(f"Exported {len(self.evaluation_logs)} evaluations to CSV: {self.csv_file}")
        
        return str(self.csv_file)
    
    def get_conversation_by_id(self, conversation_id: str) -> List[ConversationLogEntry]:
        """Get all log entries for a specific conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            List of log entries for the conversation
        """
        return [log for log in self.conversation_logs if log.conversation_id == conversation_id]
    
    def get_evaluations_by_scenario(self, scenario_id: str) -> List[EvaluationLogEntry]:
        """Get all evaluations for a specific scenario.
        
        Args:
            scenario_id: Scenario identifier
            
        Returns:
            List of evaluation logs for the scenario
        """
        return [log for log in self.evaluation_logs if log.scenario_id == scenario_id]
    
    def get_evaluations_by_hotel(self, hotel_id: str) -> List[EvaluationLogEntry]:
        """Get all evaluations for a specific hotel.
        
        Args:
            hotel_id: Hotel identifier
            
        Returns:
            List of evaluation logs for the hotel
        """
        return [log for log in self.evaluation_logs if log.hotel_id == hotel_id]
    
    def load_from_files(self, conversation_file: str, evaluation_file: str):
        """Load existing logs from files.
        
        Args:
            conversation_file: Path to conversation JSONL file
            evaluation_file: Path to evaluation JSONL file
        """
        
        # Load conversation logs
        if os.path.exists(conversation_file):
            with open(conversation_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    entry = ConversationLogEntry(**data)
                    self.conversation_logs.append(entry)
            
            self.logger.info(f"Loaded {len(self.conversation_logs)} conversation entries from {conversation_file}")
        
        # Load evaluation logs
        if os.path.exists(evaluation_file):
            with open(evaluation_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    entry = EvaluationLogEntry(**data)
                    self.evaluation_logs.append(entry)
            
            self.logger.info(f"Loaded {len(self.evaluation_logs)} evaluation entries from {evaluation_file}")


class LogAnalyzer:
    """Analyzer for processing and analyzing conversation logs."""
    
    def __init__(self, logger: ConversationLogger):
        """Initialize the log analyzer.
        
        Args:
            logger: ConversationLogger instance with data to analyze
        """
        self.logger = logger
    
    def analyze_conversation_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in conversations."""
        
        conversations = {}
        
        # Group messages by conversation
        for log in self.logger.conversation_logs:
            if log.conversation_id not in conversations:
                conversations[log.conversation_id] = []
            conversations[log.conversation_id].append(log)
        
        # Analyze patterns
        patterns = {
            "average_turns": sum(len(msgs) for msgs in conversations.values()) / len(conversations) if conversations else 0,
            "average_response_time": 0,
            "most_used_tools": {},
            "conversation_lengths": [len(msgs) for msgs in conversations.values()]
        }
        
        # Calculate response times
        response_times = []
        tool_usage = {}
        
        for msgs in conversations.values():
            for msg in msgs:
                if msg.processing_time:
                    response_times.append(msg.processing_time)
                
                for tool in msg.tools_used:
                    tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        if response_times:
            patterns["average_response_time"] = sum(response_times) / len(response_times)
        
        patterns["most_used_tools"] = sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return patterns
    
    def analyze_evaluation_trends(self) -> Dict[str, Any]:
        """Analyze trends in evaluations."""
        
        if not self.logger.evaluation_logs:
            return {}
        
        # Group by scenario and hotel
        scenario_scores = {}
        hotel_scores = {}
        
        for log in self.logger.evaluation_logs:
            # Scenario analysis
            if log.scenario_id not in scenario_scores:
                scenario_scores[log.scenario_id] = []
            scenario_scores[log.scenario_id].append(log.overall_score)
            
            # Hotel analysis
            if log.hotel_id not in hotel_scores:
                hotel_scores[log.hotel_id] = []
            hotel_scores[log.hotel_id].append(log.overall_score)
        
        # Calculate averages
        scenario_averages = {
            scenario: sum(scores) / len(scores)
            for scenario, scores in scenario_scores.items()
        }
        
        hotel_averages = {
            hotel: sum(scores) / len(scores)
            for hotel, scores in hotel_scores.items()
        }
        
        return {
            "scenario_performance": scenario_averages,
            "hotel_performance": hotel_averages,
            "best_scenario": max(scenario_averages.items(), key=lambda x: x[1]) if scenario_averages else None,
            "worst_scenario": min(scenario_averages.items(), key=lambda x: x[1]) if scenario_averages else None,
            "best_hotel": max(hotel_averages.items(), key=lambda x: x[1]) if hotel_averages else None,
            "worst_hotel": min(hotel_averages.items(), key=lambda x: x[1]) if hotel_averages else None
        }
    
    def generate_improvement_report(self) -> Dict[str, Any]:
        """Generate a comprehensive improvement report."""
        
        conversation_patterns = self.analyze_conversation_patterns()
        evaluation_trends = self.analyze_evaluation_trends()
        
        # Find common failure patterns
        failed_evaluations = [log for log in self.logger.evaluation_logs if not log.passed]
        
        failure_analysis = {
            "total_failures": len(failed_evaluations),
            "failure_rate": len(failed_evaluations) / len(self.logger.evaluation_logs) if self.logger.evaluation_logs else 0,
            "common_missing_tools": [],
            "low_scoring_dimensions": []
        }
        
        if failed_evaluations:
            # Analyze missing tools
            missing_tools_count = {}
            for log in failed_evaluations:
                for tool in log.missing_tools:
                    missing_tools_count[tool] = missing_tools_count.get(tool, 0) + 1
            
            failure_analysis["common_missing_tools"] = sorted(
                missing_tools_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            # Analyze low-scoring dimensions
            dimension_scores = {}
            for log in failed_evaluations:
                for dimension, score in log.dimension_scores.items():
                    if dimension not in dimension_scores:
                        dimension_scores[dimension] = []
                    dimension_scores[dimension].append(score)
            
            dimension_averages = {
                dim: sum(scores) / len(scores)
                for dim, scores in dimension_scores.items()
            }
            
            failure_analysis["low_scoring_dimensions"] = sorted(
                dimension_averages.items(),
                key=lambda x: x[1]
            )[:3]
        
        return {
            "conversation_patterns": conversation_patterns,
            "evaluation_trends": evaluation_trends,
            "failure_analysis": failure_analysis,
            "recommendations": self._generate_improvement_recommendations(
                conversation_patterns, evaluation_trends, failure_analysis
            )
        }
    
    def _generate_improvement_recommendations(
        self,
        conversation_patterns: Dict[str, Any],
        evaluation_trends: Dict[str, Any],
        failure_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations based on analysis."""
        
        recommendations = []
        
        # Response time recommendations
        if conversation_patterns.get("average_response_time", 0) > 5.0:
            recommendations.append("Optimize response time - current average exceeds 5 seconds")
        
        # Tool usage recommendations
        if failure_analysis.get("common_missing_tools"):
            missing_tools = [tool for tool, _ in failure_analysis["common_missing_tools"]]
            recommendations.append(f"Improve usage of commonly missed tools: {', '.join(missing_tools)}")
        
        # Dimension-specific recommendations
        if failure_analysis.get("low_scoring_dimensions"):
            low_dimensions = [dim for dim, _ in failure_analysis["low_scoring_dimensions"]]
            recommendations.append(f"Focus on improving: {', '.join(low_dimensions)}")
        
        # Scenario-specific recommendations
        if evaluation_trends.get("worst_scenario"):
            worst_scenario, score = evaluation_trends["worst_scenario"]
            recommendations.append(f"Review scenario '{worst_scenario}' - lowest average score ({score:.3f})")
        
        # Failure rate recommendations
        failure_rate = failure_analysis.get("failure_rate", 0)
        if failure_rate > 0.2:
            recommendations.append(f"High failure rate ({failure_rate:.1%}) - review overall system performance")
        
        return recommendations[:5]  # Limit to top 5 recommendations