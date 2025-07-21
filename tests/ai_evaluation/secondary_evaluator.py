"""Secondary AI evaluator for analyzing conversation logs and primary evaluations."""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import BaseModel

from .evaluator import ConversationEvaluation
from .logger import ConversationLogger, LogAnalyzer, EvaluationLogEntry
from .simulator import SimulationResult


class SecondaryAnalysisResult(BaseModel):
    """Result of secondary AI evaluation analysis."""
    
    analysis_id: str
    timestamp: datetime
    conversations_analyzed: int
    overall_assessment: str
    system_performance_score: float  # 0.0 to 1.0
    key_findings: List[str]
    pattern_analysis: Dict[str, Any]
    improvement_recommendations: List[str]
    quality_assessment: Dict[str, float]
    confidence_score: float  # How confident the AI is in its analysis
    detailed_insights: Dict[str, Any]


class PatternAnalysis(BaseModel):
    """Analysis of patterns in conversation data."""
    
    common_failure_modes: List[str]
    success_patterns: List[str]
    tool_usage_patterns: Dict[str, Any]
    conversation_flow_patterns: Dict[str, Any]
    temporal_patterns: Dict[str, Any]
    hotel_specific_patterns: Dict[str, Any]


class AdvancedSecondaryEvaluator:
    """Advanced secondary AI evaluator with deep analysis capabilities."""
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        """Initialize the advanced secondary evaluator.
        
        Args:
            openai_client: OpenAI client for AI analysis
        """
        self.openai_client = openai_client or AsyncOpenAI()
        self.logger = ConversationLogger()
        
    async def perform_comprehensive_analysis(
        self,
        evaluations: List[ConversationEvaluation],
        simulation_results: List[SimulationResult],
        conversation_logger: ConversationLogger
    ) -> SecondaryAnalysisResult:
        """Perform comprehensive secondary analysis.
        
        Args:
            evaluations: Primary evaluation results
            simulation_results: Original simulation results
            conversation_logger: Logger with conversation data
            
        Returns:
            Comprehensive secondary analysis result
        """
        analysis_id = f"secondary_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.log_info(f"Starting comprehensive secondary analysis: {analysis_id}")
        
        # Perform multiple analysis types
        pattern_analysis = await self._analyze_patterns(evaluations, simulation_results)
        quality_assessment = await self._assess_evaluation_quality(evaluations)
        system_performance = await self._analyze_system_performance(evaluations, simulation_results)
        improvement_recommendations = await self._generate_strategic_recommendations(
            evaluations, simulation_results, pattern_analysis
        )
        
        # Calculate overall system performance score
        system_score = await self._calculate_system_score(evaluations, pattern_analysis)
        
        # Generate key findings
        key_findings = await self._extract_key_findings(
            evaluations, pattern_analysis, quality_assessment
        )
        
        # Generate overall assessment
        overall_assessment = await self._generate_overall_assessment(
            evaluations, system_score, key_findings
        )
        
        # Calculate confidence in the analysis
        confidence_score = self._calculate_confidence_score(evaluations, simulation_results)
        
        result = SecondaryAnalysisResult(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            conversations_analyzed=len(evaluations),
            overall_assessment=overall_assessment,
            system_performance_score=system_score,
            key_findings=key_findings,
            pattern_analysis=pattern_analysis.model_dump() if isinstance(pattern_analysis, PatternAnalysis) else pattern_analysis,
            improvement_recommendations=improvement_recommendations,
            quality_assessment=quality_assessment,
            confidence_score=confidence_score,
            detailed_insights={
                "system_performance_details": system_performance,
                "evaluation_distribution": self._analyze_score_distribution(evaluations),
                "tool_effectiveness": self._analyze_tool_effectiveness(evaluations),
                "scenario_difficulty": self._analyze_scenario_difficulty(evaluations)
            }
        )
        
        self.logger.log_info(f"Completed secondary analysis: {analysis_id} - Score: {system_score:.3f}")
        
        return result
    
    async def _analyze_patterns(
        self,
        evaluations: List[ConversationEvaluation],
        simulation_results: List[SimulationResult]
    ) -> PatternAnalysis:
        """Analyze patterns in conversations and evaluations."""
        
        # Prepare data for AI analysis
        pattern_data = {
            "total_conversations": len(evaluations),
            "success_rate": len([e for e in evaluations if e.passed]) / len(evaluations) if evaluations else 0,
            "average_score": sum(e.overall_score for e in evaluations) / len(evaluations) if evaluations else 0,
            "common_failures": {},
            "tool_usage": {},
            "response_times": []
        }
        
        # Collect failure patterns
        failed_evals = [e for e in evaluations if not e.passed]
        for eval in failed_evals:
            for rec in eval.recommendations:
                pattern_data["common_failures"][rec] = pattern_data["common_failures"].get(rec, 0) + 1
        
        # Collect tool usage patterns
        for eval in evaluations:
            for tool in eval.actual_tools_used:
                pattern_data["tool_usage"][tool] = pattern_data["tool_usage"].get(tool, 0) + 1
        
        # Collect response times from simulation results
        for result in simulation_results:
            pattern_data["response_times"].extend([
                msg.get("processing_time", 0) for msg in result.messages 
                if msg.get("processing_time")
            ])
        
        # AI pattern analysis prompt
        analysis_prompt = f"""
Analyze the following hotel agent conversation data to identify patterns:

**System Overview:**
- Total conversations: {pattern_data['total_conversations']}
- Success rate: {pattern_data['success_rate']:.3f}
- Average score: {pattern_data['average_score']:.3f}

**Common Failures:**
{json.dumps(pattern_data['common_failures'], indent=2)}

**Tool Usage Frequency:**
{json.dumps(pattern_data['tool_usage'], indent=2)}

**Performance Data:**
- Average response time: {sum(pattern_data['response_times']) / len(pattern_data['response_times']):.2f}s (if available)

Identify and analyze:
1. Common failure modes and their root causes
2. Success patterns that lead to high-scoring conversations
3. Tool usage patterns and effectiveness
4. Conversation flow patterns
5. Any temporal or contextual patterns

Provide insights in JSON format:
{{
    "common_failure_modes": ["List of failure patterns with explanations"],
    "success_patterns": ["List of success patterns"],
    "tool_usage_patterns": {{"insights": "analysis of tool usage"}},
    "conversation_flow_patterns": {{"insights": "analysis of conversation flows"}},
    "key_insights": ["Most important insights"]
}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert AI systems analyst specializing in conversational AI pattern recognition and performance analysis."},
                    {"role": "user", "content": analysis_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            analysis_data = json.loads(response.choices[0].message.content)
            
            return PatternAnalysis(
                common_failure_modes=analysis_data.get("common_failure_modes", []),
                success_patterns=analysis_data.get("success_patterns", []),
                tool_usage_patterns=analysis_data.get("tool_usage_patterns", {}),
                conversation_flow_patterns=analysis_data.get("conversation_flow_patterns", {}),
                temporal_patterns={},  # Could be expanded with time-based analysis
                hotel_specific_patterns=self._analyze_hotel_patterns(evaluations)
            )
            
        except Exception as e:
            self.logger.log_error(f"Error in pattern analysis: {str(e)}")
            return PatternAnalysis(
                common_failure_modes=["Analysis error - manual review required"],
                success_patterns=[],
                tool_usage_patterns={},
                conversation_flow_patterns={},
                temporal_patterns={},
                hotel_specific_patterns={}
            )
    
    def _analyze_hotel_patterns(self, evaluations: List[ConversationEvaluation]) -> Dict[str, Any]:
        """Analyze patterns specific to different hotels."""
        
        hotel_performance = {}
        
        for eval in evaluations:
            if eval.hotel_id not in hotel_performance:
                hotel_performance[eval.hotel_id] = {
                    "scores": [],
                    "success_count": 0,
                    "total_count": 0
                }
            
            stats = hotel_performance[eval.hotel_id]
            stats["scores"].append(eval.overall_score)
            stats["total_count"] += 1
            if eval.passed:
                stats["success_count"] += 1
        
        # Calculate statistics
        hotel_stats = {}
        for hotel_id, data in hotel_performance.items():
            hotel_stats[hotel_id] = {
                "average_score": sum(data["scores"]) / len(data["scores"]),
                "success_rate": data["success_count"] / data["total_count"],
                "total_conversations": data["total_count"]
            }
        
        return hotel_stats
    
    async def _assess_evaluation_quality(self, evaluations: List[ConversationEvaluation]) -> Dict[str, float]:
        """Assess the quality of the evaluation system itself."""
        
        if not evaluations:
            return {"consistency": 0.0, "coverage": 0.0, "reliability": 0.0}
        
        # Calculate evaluation consistency
        score_variance = self._calculate_score_variance(evaluations)
        consistency_score = max(0.0, 1.0 - (score_variance / 0.25))  # Normalize variance
        
        # Calculate coverage (how well different scenarios are covered)
        unique_scenarios = len(set(e.scenario_id for e in evaluations))
        unique_hotels = len(set(e.hotel_id for e in evaluations))
        coverage_score = min(1.0, (unique_scenarios * unique_hotels) / 15.0)  # Assume 15 is ideal coverage
        
        # Calculate reliability (consistency in tool usage evaluation)
        tool_consistency = self._calculate_tool_evaluation_consistency(evaluations)
        
        # AI quality assessment
        quality_prompt = f"""
Assess the quality of this AI evaluation system based on the following data:

**Evaluation Statistics:**
- Total evaluations: {len(evaluations)}
- Score variance: {score_variance:.4f}
- Unique scenarios tested: {unique_scenarios}
- Unique hotels tested: {unique_hotels}
- Average overall score: {sum(e.overall_score for e in evaluations) / len(evaluations):.3f}

**Sample Evaluation Results:**
{json.dumps([{
    "scenario": e.scenario_id,
    "score": e.overall_score,
    "passed": e.passed,
    "tool_coverage": len(e.actual_tools_used) / max(1, len(e.expected_tools_used))
} for e in evaluations[:5]], indent=2)}

Rate the evaluation system quality on these dimensions (0.0 to 1.0):

{{
    "accuracy": 0.85,
    "consistency": 0.90,
    "comprehensiveness": 0.80,
    "reliability": 0.88
}}

Consider:
- How consistent are the scores?
- How comprehensive is the evaluation coverage?
- How reliable do the evaluations appear?
- Overall system accuracy assessment
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in AI evaluation systems and quality assessment."},
                    {"role": "user", "content": quality_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            ai_assessment = json.loads(response.choices[0].message.content)
            
            return {
                "consistency": consistency_score,
                "coverage": coverage_score,
                "tool_reliability": tool_consistency,
                "ai_accuracy_assessment": ai_assessment.get("accuracy", 0.5),
                "ai_consistency_assessment": ai_assessment.get("consistency", 0.5),
                "ai_comprehensiveness": ai_assessment.get("comprehensiveness", 0.5),
                "ai_reliability_assessment": ai_assessment.get("reliability", 0.5)
            }
            
        except Exception as e:
            self.logger.log_error(f"Error in quality assessment: {str(e)}")
            return {
                "consistency": consistency_score,
                "coverage": coverage_score,
                "tool_reliability": tool_consistency,
                "ai_accuracy_assessment": 0.5,
                "ai_consistency_assessment": 0.5,
                "ai_comprehensiveness": 0.5,
                "ai_reliability_assessment": 0.5
            }
    
    def _calculate_score_variance(self, evaluations: List[ConversationEvaluation]) -> float:
        """Calculate variance in evaluation scores."""
        if len(evaluations) < 2:
            return 0.0
        
        scores = [e.overall_score for e in evaluations]
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        return variance
    
    def _calculate_tool_evaluation_consistency(self, evaluations: List[ConversationEvaluation]) -> float:
        """Calculate consistency in tool usage evaluation."""
        if not evaluations:
            return 0.0
        
        tool_coverage_scores = []
        for eval in evaluations:
            if eval.expected_tools_used:
                coverage = len(eval.actual_tools_used) / len(eval.expected_tools_used)
                tool_coverage_scores.append(min(1.0, coverage))
        
        if not tool_coverage_scores:
            return 0.0
        
        # Higher consistency = lower variance in tool coverage scores
        mean_coverage = sum(tool_coverage_scores) / len(tool_coverage_scores)
        variance = sum((score - mean_coverage) ** 2 for score in tool_coverage_scores) / len(tool_coverage_scores)
        
        return max(0.0, 1.0 - variance)
    
    async def _analyze_system_performance(
        self,
        evaluations: List[ConversationEvaluation],
        simulation_results: List[SimulationResult]
    ) -> Dict[str, Any]:
        """Analyze overall system performance."""
        
        performance_metrics = {
            "conversation_success_rate": len([e for e in evaluations if e.passed]) / len(evaluations) if evaluations else 0,
            "average_response_quality": sum(e.overall_score for e in evaluations) / len(evaluations) if evaluations else 0,
            "tool_utilization_rate": 0,
            "error_rate": len([r for r in simulation_results if not r.success]) / len(simulation_results) if simulation_results else 0,
            "average_conversation_length": 0,
            "system_reliability": 0
        }
        
        # Calculate tool utilization
        if evaluations:
            total_expected_tools = sum(len(e.expected_tools_used) for e in evaluations)
            total_used_tools = sum(len(e.actual_tools_used) for e in evaluations)
            performance_metrics["tool_utilization_rate"] = total_used_tools / total_expected_tools if total_expected_tools > 0 else 0
        
        # Calculate average conversation length
        if simulation_results:
            conversation_lengths = [len(r.messages) for r in simulation_results]
            performance_metrics["average_conversation_length"] = sum(conversation_lengths) / len(conversation_lengths)
        
        # Calculate system reliability (successful execution rate)
        performance_metrics["system_reliability"] = 1.0 - performance_metrics["error_rate"]
        
        return performance_metrics
    
    async def _generate_strategic_recommendations(
        self,
        evaluations: List[ConversationEvaluation],
        simulation_results: List[SimulationResult],
        pattern_analysis: PatternAnalysis
    ) -> List[str]:
        """Generate strategic recommendations for system improvement."""
        
        # Prepare strategic analysis data
        strategic_data = {
            "system_metrics": {
                "total_evaluations": len(evaluations),
                "success_rate": len([e for e in evaluations if e.passed]) / len(evaluations) if evaluations else 0,
                "average_score": sum(e.overall_score for e in evaluations) / len(evaluations) if evaluations else 0
            },
            "pattern_insights": {
                "failure_modes": pattern_analysis.common_failure_modes,
                "success_patterns": pattern_analysis.success_patterns,
                "tool_patterns": pattern_analysis.tool_usage_patterns
            },
            "performance_issues": []
        }
        
        # Identify performance issues
        low_performing_scenarios = [
            e.scenario_id for e in evaluations 
            if e.overall_score < 0.6
        ]
        
        if low_performing_scenarios:
            strategic_data["performance_issues"].append(f"Low-performing scenarios: {set(low_performing_scenarios)}")
        
        strategic_prompt = f"""
As a senior AI systems strategist, analyze this hotel agent system and provide strategic recommendations.

**System Performance:**
{json.dumps(strategic_data['system_metrics'], indent=2)}

**Pattern Analysis:**
{json.dumps(strategic_data['pattern_insights'], indent=2)}

**Performance Issues:**
{json.dumps(strategic_data['performance_issues'], indent=2)}

Provide 5-7 strategic recommendations focused on:
1. System architecture improvements
2. Training and optimization strategies
3. Tool integration enhancements
4. User experience improvements
5. Scalability and reliability measures

Format as a JSON list:
{{
    "recommendations": [
        "Strategic recommendation 1...",
        "Strategic recommendation 2...",
        ...
    ]
}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior AI systems strategist with expertise in conversational AI optimization and scalable system design."},
                    {"role": "user", "content": strategic_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            strategic_response = json.loads(response.choices[0].message.content)
            return strategic_response.get("recommendations", [])
            
        except Exception as e:
            self.logger.log_error(f"Error generating strategic recommendations: {str(e)}")
            return [
                "Review system performance metrics and identify optimization opportunities",
                "Improve tool integration and utilization patterns",
                "Enhance conversation flow and context management",
                "Implement better error handling and reliability measures",
                "Optimize response quality and user experience"
            ]
    
    async def _calculate_system_score(
        self,
        evaluations: List[ConversationEvaluation],
        pattern_analysis: PatternAnalysis
    ) -> float:
        """Calculate overall system performance score."""
        
        if not evaluations:
            return 0.0
        
        # Base score from evaluation averages
        base_score = sum(e.overall_score for e in evaluations) / len(evaluations)
        
        # Adjust for success rate
        success_rate = len([e for e in evaluations if e.passed]) / len(evaluations)
        success_adjustment = (success_rate - 0.5) * 0.2  # -0.1 to +0.1 adjustment
        
        # Adjust for pattern quality
        pattern_adjustment = 0.0
        if len(pattern_analysis.success_patterns) > len(pattern_analysis.common_failure_modes):
            pattern_adjustment += 0.05
        elif len(pattern_analysis.common_failure_modes) > len(pattern_analysis.success_patterns):
            pattern_adjustment -= 0.05
        
        # Adjust for tool usage effectiveness
        tool_adjustment = 0.0
        # This would be calculated based on tool usage patterns
        
        final_score = base_score + success_adjustment + pattern_adjustment + tool_adjustment
        
        return max(0.0, min(1.0, final_score))
    
    async def _extract_key_findings(
        self,
        evaluations: List[ConversationEvaluation],
        pattern_analysis: PatternAnalysis,
        quality_assessment: Dict[str, float]
    ) -> List[str]:
        """Extract key findings from the analysis."""
        
        findings_data = {
            "total_conversations": len(evaluations),
            "success_rate": len([e for e in evaluations if e.passed]) / len(evaluations) if evaluations else 0,
            "average_score": sum(e.overall_score for e in evaluations) / len(evaluations) if evaluations else 0,
            "top_failure_modes": pattern_analysis.common_failure_modes[:3],
            "top_success_patterns": pattern_analysis.success_patterns[:3],
            "evaluation_quality": quality_assessment
        }
        
        findings_prompt = f"""
Extract the most important key findings from this hotel agent analysis:

**System Overview:**
{json.dumps(findings_data, indent=2)}

Identify 5-7 key findings that are:
1. Most impactful for system improvement
2. Actionable and specific
3. Based on clear evidence from the data
4. Critical for stakeholder understanding

Format as JSON:
{{
    "key_findings": [
        "Finding 1: Specific insight with impact...",
        "Finding 2: Another critical finding...",
        ...
    ]
}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert data analyst specializing in extracting actionable insights from AI system performance data."},
                    {"role": "user", "content": findings_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            findings_response = json.loads(response.choices[0].message.content)
            return findings_response.get("key_findings", [])
            
        except Exception as e:
            self.logger.log_error(f"Error extracting key findings: {str(e)}")
            return [
                f"System achieved {len([e for e in evaluations if e.passed])}/{len(evaluations)} successful conversations",
                f"Average conversation quality score: {sum(e.overall_score for e in evaluations) / len(evaluations):.3f}",
                "Pattern analysis reveals specific areas for improvement",
                "Tool usage optimization opportunities identified",
                "Evaluation system quality assessment completed"
            ]
    
    async def _generate_overall_assessment(
        self,
        evaluations: List[ConversationEvaluation],
        system_score: float,
        key_findings: List[str]
    ) -> str:
        """Generate overall assessment of the system."""
        
        assessment_data = {
            "system_score": system_score,
            "total_conversations": len(evaluations),
            "success_rate": len([e for e in evaluations if e.passed]) / len(evaluations) if evaluations else 0,
            "key_findings": key_findings[:3]  # Top 3 findings
        }
        
        assessment_prompt = f"""
Generate a comprehensive overall assessment of this hotel agent system:

**System Performance:**
- Overall Score: {system_score:.3f}/1.0
- Conversations Analyzed: {assessment_data['total_conversations']}
- Success Rate: {assessment_data['success_rate']:.1%}

**Key Findings:**
{chr(10).join(['- ' + finding for finding in assessment_data['key_findings']])}

Write a 3-4 sentence executive summary that:
1. Summarizes the current system performance
2. Highlights the most critical findings
3. Indicates the overall trajectory (improving/declining/stable)
4. Provides context for stakeholders

Keep it professional and actionable.
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert AI systems analyst providing executive summaries for technical stakeholders."},
                    {"role": "user", "content": assessment_prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.log_error(f"Error generating overall assessment: {str(e)}")
            return f"Hotel agent system analysis completed with overall performance score of {system_score:.3f}. {assessment_data['total_conversations']} conversations analyzed with {assessment_data['success_rate']:.1%} success rate. Key areas for improvement identified through comprehensive pattern analysis."
    
    def _calculate_confidence_score(
        self,
        evaluations: List[ConversationEvaluation],
        simulation_results: List[SimulationResult]
    ) -> float:
        """Calculate confidence in the analysis based on data quality and quantity."""
        
        # Base confidence from data quantity
        data_quantity_score = min(1.0, len(evaluations) / 20.0)  # Assume 20+ conversations for high confidence
        
        # Data quality score based on successful executions
        execution_success_rate = len([r for r in simulation_results if r.success]) / len(simulation_results) if simulation_results else 0
        
        # Evaluation completeness score
        complete_evaluations = len([e for e in evaluations if len(e.scores) >= 4])  # Assume 4+ dimension scores
        completeness_score = complete_evaluations / len(evaluations) if evaluations else 0
        
        # Scenario coverage score
        unique_scenarios = len(set(e.scenario_id for e in evaluations))
        unique_hotels = len(set(e.hotel_id for e in evaluations))
        coverage_score = min(1.0, (unique_scenarios * unique_hotels) / 10.0)  # Assume 10 is good coverage
        
        # Weighted confidence score
        confidence = (
            data_quantity_score * 0.3 +
            execution_success_rate * 0.3 +
            completeness_score * 0.2 +
            coverage_score * 0.2
        )
        
        return confidence
    
    def _analyze_score_distribution(self, evaluations: List[ConversationEvaluation]) -> Dict[str, Any]:
        """Analyze the distribution of evaluation scores."""
        
        if not evaluations:
            return {}
        
        scores = [e.overall_score for e in evaluations]
        
        return {
            "mean": sum(scores) / len(scores),
            "median": sorted(scores)[len(scores) // 2],
            "min": min(scores),
            "max": max(scores),
            "std_dev": (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))**0.5,
            "score_ranges": {
                "excellent": len([s for s in scores if s >= 0.9]),
                "good": len([s for s in scores if 0.7 <= s < 0.9]),
                "acceptable": len([s for s in scores if 0.5 <= s < 0.7]),
                "poor": len([s for s in scores if s < 0.5])
            }
        }
    
    def _analyze_tool_effectiveness(self, evaluations: List[ConversationEvaluation]) -> Dict[str, Any]:
        """Analyze the effectiveness of different tools."""
        
        tool_stats = {}
        
        for eval in evaluations:
            for tool in eval.actual_tools_used:
                if tool not in tool_stats:
                    tool_stats[tool] = {
                        "usage_count": 0,
                        "success_scores": [],
                        "conversation_scores": []
                    }
                
                tool_stats[tool]["usage_count"] += 1
                tool_stats[tool]["conversation_scores"].append(eval.overall_score)
                
                # Find tool-specific score if available
                tool_score = next((s.score for s in eval.scores if "tool" in s.dimension), None)
                if tool_score is not None:
                    tool_stats[tool]["success_scores"].append(tool_score)
        
        # Calculate effectiveness metrics
        tool_effectiveness = {}
        for tool, stats in tool_stats.items():
            avg_conversation_score = sum(stats["conversation_scores"]) / len(stats["conversation_scores"])
            avg_tool_score = sum(stats["success_scores"]) / len(stats["success_scores"]) if stats["success_scores"] else 0
            
            tool_effectiveness[tool] = {
                "usage_frequency": stats["usage_count"],
                "average_conversation_impact": avg_conversation_score,
                "average_tool_score": avg_tool_score,
                "effectiveness_rating": (avg_conversation_score + avg_tool_score) / 2 if avg_tool_score > 0 else avg_conversation_score
            }
        
        return tool_effectiveness
    
    def _analyze_scenario_difficulty(self, evaluations: List[ConversationEvaluation]) -> Dict[str, Any]:
        """Analyze the difficulty of different scenarios."""
        
        scenario_stats = {}
        
        for eval in evaluations:
            if eval.scenario_id not in scenario_stats:
                scenario_stats[eval.scenario_id] = {
                    "scores": [],
                    "success_count": 0,
                    "total_count": 0
                }
            
            stats = scenario_stats[eval.scenario_id]
            stats["scores"].append(eval.overall_score)
            stats["total_count"] += 1
            if eval.passed:
                stats["success_count"] += 1
        
        # Calculate difficulty metrics
        scenario_analysis = {}
        for scenario_id, stats in scenario_stats.items():
            avg_score = sum(stats["scores"]) / len(stats["scores"])
            success_rate = stats["success_count"] / stats["total_count"]
            
            # Difficulty estimation (lower scores and success rates = higher difficulty)
            difficulty = 1.0 - ((avg_score + success_rate) / 2.0)
            
            scenario_analysis[scenario_id] = {
                "average_score": avg_score,
                "success_rate": success_rate,
                "difficulty_estimate": difficulty,
                "total_attempts": stats["total_count"],
                "difficulty_level": "Hard" if difficulty > 0.6 else "Medium" if difficulty > 0.3 else "Easy"
            }
        
        return scenario_analysis
    
    async def export_analysis_report(
        self,
        analysis_result: SecondaryAnalysisResult,
        output_path: Optional[str] = None
    ) -> str:
        """Export comprehensive analysis report to JSON file.
        
        Args:
            analysis_result: Secondary analysis result to export
            output_path: Optional output file path
            
        Returns:
            Path to exported report
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"logs/ai_evaluation/secondary_analysis_report_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare comprehensive report
        report_data = {
            "metadata": {
                "report_type": "Secondary AI Evaluation Analysis",
                "generated_at": datetime.now().isoformat(),
                "analysis_id": analysis_result.analysis_id,
                "conversations_analyzed": analysis_result.conversations_analyzed
            },
            "executive_summary": {
                "overall_assessment": analysis_result.overall_assessment,
                "system_performance_score": analysis_result.system_performance_score,
                "confidence_score": analysis_result.confidence_score,
                "key_findings": analysis_result.key_findings
            },
            "detailed_analysis": {
                "pattern_analysis": analysis_result.pattern_analysis,
                "quality_assessment": analysis_result.quality_assessment,
                "detailed_insights": analysis_result.detailed_insights
            },
            "recommendations": {
                "improvement_recommendations": analysis_result.improvement_recommendations,
                "priority_actions": analysis_result.improvement_recommendations[:3]  # Top 3 as priority
            }
        }
        
        # Write report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str, ensure_ascii=False)
        
        self.logger.log_info(f"Exported secondary analysis report to: {output_file}")
        
        return str(output_file)