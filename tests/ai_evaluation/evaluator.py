"""AI-powered evaluation system for hotel agent conversations."""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import BaseModel

from .config import EvaluationCriteria, EVALUATION_CONFIG, ConversationScenario
from .simulator import SimulationResult
from .logger import ConversationLogger


class EvaluationScore(BaseModel):
    """Individual evaluation score component."""
    
    dimension: str
    score: float  # 0.0 to 1.0
    reasoning: str
    weight: float


class ConversationEvaluation(BaseModel):
    """Complete evaluation of a conversation."""
    
    conversation_id: str
    scenario_id: str
    hotel_id: str
    overall_score: float
    passed: bool
    scores: List[EvaluationScore]
    tool_coverage_score: float
    expected_tools_used: List[str]
    actual_tools_used: List[str]
    missing_tools: List[str]
    summary: str
    recommendations: List[str]
    timestamp: datetime


class ResponseEvaluation(BaseModel):
    """Evaluation of a single agent response."""
    
    turn_number: int
    response_text: str
    accuracy_score: float
    helpfulness_score: float
    politeness_score: float
    tool_usage_appropriate: bool
    issues: List[str]
    strengths: List[str]


class AIEvaluator:
    """AI-powered evaluator for hotel agent conversations."""
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None, config: Optional[EvaluationCriteria] = None):
        """Initialize the AI evaluator.
        
        Args:
            openai_client: OpenAI client for AI evaluation
            config: Evaluation criteria configuration
        """
        self.openai_client = openai_client or AsyncOpenAI()
        self.config = config or EVALUATION_CONFIG
        self.logger = ConversationLogger()
        
    async def evaluate_conversation(
        self,
        result: SimulationResult,
        scenario: ConversationScenario
    ) -> ConversationEvaluation:
        """Evaluate a complete conversation.
        
        Args:
            result: Simulation result to evaluate
            scenario: Original scenario configuration
            
        Returns:
            Comprehensive conversation evaluation
        """
        self.logger.log_info(f"Evaluating conversation {result.conversation_id}")
        
        # Evaluate individual responses
        response_evaluations = []
        for response_data in result.agent_responses:
            response_eval = await self._evaluate_single_response(
                response_data, scenario, result
            )
            response_evaluations.append(response_eval)
        
        # Evaluate overall conversation flow
        flow_score = await self._evaluate_conversation_flow(result, scenario)
        
        # Evaluate tool usage
        tool_score, missing_tools = self._evaluate_tool_usage(result, scenario)
        
        # Calculate dimension scores
        scores = []
        
        # Accuracy score (average of individual response accuracies)
        accuracy_avg = sum(r.accuracy_score for r in response_evaluations) / len(response_evaluations) if response_evaluations else 0.0
        scores.append(EvaluationScore(
            dimension="accuracy",
            score=accuracy_avg,
            reasoning=f"Average accuracy across {len(response_evaluations)} responses",
            weight=self.config.accuracy_weight
        ))
        
        # Helpfulness score
        helpfulness_avg = sum(r.helpfulness_score for r in response_evaluations) / len(response_evaluations) if response_evaluations else 0.0
        scores.append(EvaluationScore(
            dimension="helpfulness",
            score=helpfulness_avg,
            reasoning=f"Average helpfulness across {len(response_evaluations)} responses",
            weight=self.config.helpfulness_weight
        ))
        
        # Tool usage score
        scores.append(EvaluationScore(
            dimension="tool_usage",
            score=tool_score,
            reasoning=f"Tool usage appropriateness: {len(result.tools_used)}/{len(scenario.expected_tools)} expected tools used",
            weight=self.config.tool_usage_weight
        ))
        
        # Conversation flow score
        scores.append(EvaluationScore(
            dimension="conversation_flow",
            score=flow_score,
            reasoning="Natural conversation flow and context maintenance",
            weight=self.config.conversation_flow_weight
        ))
        
        # Politeness score
        politeness_avg = sum(r.politeness_score for r in response_evaluations) / len(response_evaluations) if response_evaluations else 0.0
        scores.append(EvaluationScore(
            dimension="politeness",
            score=politeness_avg,
            reasoning=f"Average politeness across {len(response_evaluations)} responses",
            weight=self.config.politeness_weight
        ))
        
        # Calculate weighted overall score
        overall_score = sum(score.score * score.weight for score in scores)
        passed = overall_score >= self.config.minimum_passing_score
        
        # Generate summary and recommendations
        summary = await self._generate_evaluation_summary(result, scenario, scores, overall_score)
        recommendations = await self._generate_recommendations(result, scenario, scores, response_evaluations)
        
        evaluation = ConversationEvaluation(
            conversation_id=result.conversation_id,
            scenario_id=result.scenario_id,
            hotel_id=result.hotel_id,
            overall_score=overall_score,
            passed=passed,
            scores=scores,
            tool_coverage_score=tool_score,
            expected_tools_used=scenario.expected_tools,
            actual_tools_used=result.tools_used,
            missing_tools=missing_tools,
            summary=summary,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
        
        self.logger.log_info(
            f"Evaluation completed: {result.conversation_id} - "
            f"Score: {overall_score:.3f} ({'PASSED' if passed else 'FAILED'})"
        )
        
        return evaluation
    
    async def _evaluate_single_response(
        self,
        response_data: Dict[str, Any],
        scenario: ConversationScenario,
        result: SimulationResult
    ) -> ResponseEvaluation:
        """Evaluate a single agent response using AI."""
        
        response_text = response_data.get("response", "")
        turn_number = response_data.get("turn", 0)
        tools_used = response_data.get("tools_used", [])
        
        # Prepare evaluation prompt
        evaluation_prompt = f"""
Evaluate this hotel agent response for accuracy, helpfulness, and politeness.

**Scenario Context:**
- Hotel: {scenario.hotel_id}
- Scenario: {scenario.title}
- Description: {scenario.description}

**Agent Response (Turn {turn_number}):**
{response_text}

**Tools Used:** {', '.join(tools_used) if tools_used else 'None'}

**Evaluation Criteria:**
1. Accuracy (0.0-1.0): Is the information correct and relevant?
2. Helpfulness (0.0-1.0): Does it address the user's needs effectively?  
3. Politeness (0.0-1.0): Is the tone professional and courteous?
4. Tool Usage: Are the tools used appropriately for the request?

**Expected Response Format (JSON):**
{{
    "accuracy_score": 0.85,
    "helpfulness_score": 0.90,
    "politeness_score": 0.95,
    "tool_usage_appropriate": true,
    "issues": ["Any specific issues found"],
    "strengths": ["Notable strengths in the response"],
    "reasoning": "Brief explanation of the evaluation"
}}

Provide your evaluation in JSON format:
"""
        
        try:
            # Get AI evaluation
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of customer service interactions. Provide objective, detailed evaluations based on the criteria given."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            evaluation_data = json.loads(response.choices[0].message.content)
            
            return ResponseEvaluation(
                turn_number=turn_number,
                response_text=response_text,
                accuracy_score=evaluation_data.get("accuracy_score", 0.5),
                helpfulness_score=evaluation_data.get("helpfulness_score", 0.5),
                politeness_score=evaluation_data.get("politeness_score", 0.5),
                tool_usage_appropriate=evaluation_data.get("tool_usage_appropriate", False),
                issues=evaluation_data.get("issues", []),
                strengths=evaluation_data.get("strengths", [])
            )
            
        except Exception as e:
            self.logger.log_error(f"Error evaluating response: {str(e)}")
            
            # Return default evaluation on error
            return ResponseEvaluation(
                turn_number=turn_number,
                response_text=response_text,
                accuracy_score=0.5,
                helpfulness_score=0.5,
                politeness_score=0.5,
                tool_usage_appropriate=len(tools_used) > 0,
                issues=[f"Evaluation error: {str(e)}"],
                strengths=[]
            )
    
    async def _evaluate_conversation_flow(
        self,
        result: SimulationResult,
        scenario: ConversationScenario
    ) -> float:
        """Evaluate the overall conversation flow using AI."""
        
        # Prepare conversation for evaluation
        conversation_text = ""
        for msg in result.messages:
            role = msg["role"].title()
            content = msg["content"]
            conversation_text += f"{role}: {content}\n\n"
        
        evaluation_prompt = f"""
Evaluate the conversation flow and context maintenance in this hotel service interaction.

**Scenario:** {scenario.title}
**Description:** {scenario.description}

**Full Conversation:**
{conversation_text}

**Evaluation Criteria:**
- Does the agent maintain context throughout the conversation?
- Are responses naturally connected to previous messages?
- Does the conversation feel coherent and professional?
- Are transitions between topics smooth?

Rate the conversation flow from 0.0 (poor) to 1.0 (excellent).

**Response Format (JSON):**
{{
    "flow_score": 0.85,
    "reasoning": "Brief explanation of the score"
}}

Provide your evaluation in JSON format:
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of conversation quality and customer service interactions."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            evaluation_data = json.loads(response.choices[0].message.content)
            return evaluation_data.get("flow_score", 0.5)
            
        except Exception as e:
            self.logger.log_error(f"Error evaluating conversation flow: {str(e)}")
            return 0.5
    
    def _evaluate_tool_usage(
        self,
        result: SimulationResult,
        scenario: ConversationScenario
    ) -> Tuple[float, List[str]]:
        """Evaluate tool usage coverage and appropriateness."""
        
        expected_tools = set(scenario.expected_tools)
        actual_tools = set(result.tools_used)
        
        # Calculate coverage
        if not expected_tools:
            coverage_score = 1.0 if not actual_tools else 0.8  # No tools expected
        else:
            covered_tools = expected_tools.intersection(actual_tools)
            coverage_score = len(covered_tools) / len(expected_tools)
        
        # Bonus for appropriate additional tools (but cap at 1.0)
        if actual_tools - expected_tools:
            # Small bonus for using additional relevant tools
            coverage_score = min(1.0, coverage_score + 0.1)
        
        missing_tools = list(expected_tools - actual_tools)
        
        return coverage_score, missing_tools
    
    async def _generate_evaluation_summary(
        self,
        result: SimulationResult,
        scenario: ConversationScenario,
        scores: List[EvaluationScore],
        overall_score: float
    ) -> str:
        """Generate a comprehensive evaluation summary."""
        
        score_breakdown = "\n".join([
            f"- {score.dimension.title()}: {score.score:.3f} (weight: {score.weight:.2f})"
            for score in scores
        ])
        
        tools_info = f"Tools used: {', '.join(result.tools_used) if result.tools_used else 'None'}"
        expected_tools_info = f"Expected tools: {', '.join(scenario.expected_tools) if scenario.expected_tools else 'None'}"
        
        summary_prompt = f"""
Generate a concise evaluation summary for this hotel agent conversation.

**Scenario:** {scenario.title}
**Overall Score:** {overall_score:.3f}
**Status:** {'PASSED' if overall_score >= self.config.minimum_passing_score else 'FAILED'}

**Score Breakdown:**
{score_breakdown}

**Tool Usage:**
{tools_info}
{expected_tools_info}

**Conversation Details:**
- Total turns: {len(result.messages)}
- Execution time: {result.execution_time:.2f} seconds
- Success: {result.success}

Provide a 2-3 sentence summary highlighting the key strengths and areas for improvement.
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator. Provide concise, actionable summaries."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.2,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.log_error(f"Error generating summary: {str(e)}")
            return f"Evaluation completed with overall score {overall_score:.3f}. Review individual scores for details."
    
    async def _generate_recommendations(
        self,
        result: SimulationResult,
        scenario: ConversationScenario,
        scores: List[EvaluationScore],
        response_evaluations: List[ResponseEvaluation]
    ) -> List[str]:
        """Generate actionable recommendations for improvement."""
        
        # Identify lowest scoring dimensions
        low_scores = [score for score in scores if score.score < 0.7]
        
        # Collect common issues from response evaluations
        all_issues = []
        for resp_eval in response_evaluations:
            all_issues.extend(resp_eval.issues)
        
        recommendations = []
        
        # Generate recommendations based on low scores
        for score in low_scores:
            if score.dimension == "accuracy":
                recommendations.append("Improve factual accuracy of responses and ensure information relevance")
            elif score.dimension == "helpfulness":
                recommendations.append("Enhance response helpfulness by providing more actionable information")
            elif score.dimension == "tool_usage":
                recommendations.append(f"Better tool utilization - missing tools: {', '.join(result.tools_used) if result.tools_used else 'multiple tools'}")
            elif score.dimension == "conversation_flow":
                recommendations.append("Improve context retention and conversation coherence")
            elif score.dimension == "politeness":
                recommendations.append("Maintain more professional and courteous tone throughout")
        
        # Add specific recommendations based on missing tools
        missing_tools = set(scenario.expected_tools) - set(result.tools_used)
        if missing_tools:
            recommendations.append(f"Utilize missing essential tools: {', '.join(missing_tools)}")
        
        # Limit to most important recommendations
        return recommendations[:5]
    
    async def evaluate_multiple_conversations(
        self,
        results: List[SimulationResult],
        scenarios: List[ConversationScenario]
    ) -> List[ConversationEvaluation]:
        """Evaluate multiple conversations in batch.
        
        Args:
            results: List of simulation results
            scenarios: Corresponding scenarios
            
        Returns:
            List of conversation evaluations
        """
        # Create a mapping of scenario_id to scenario
        scenario_map = {s.scenario_id: s for s in scenarios}
        
        evaluations = []
        
        for result in results:
            # Find matching scenario (handle modified scenario IDs)
            scenario = None
            scenario_id = result.scenario_id
            
            # Try direct match first
            if scenario_id in scenario_map:
                scenario = scenario_map[scenario_id]
            else:
                # Try to find base scenario ID (in case of hotel-specific modifications)
                for base_scenario_id in scenario_map:
                    if scenario_id.startswith(base_scenario_id):
                        scenario = scenario_map[base_scenario_id].model_copy()
                        scenario.hotel_id = result.hotel_id  # Update hotel ID
                        break
            
            if not scenario:
                self.logger.log_error(f"No scenario found for result: {result.scenario_id}")
                continue
            
            try:
                evaluation = await self.evaluate_conversation(result, scenario)
                evaluations.append(evaluation)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.log_error(f"Error evaluating {result.conversation_id}: {str(e)}")
        
        return evaluations


class SecondaryEvaluator:
    """Secondary AI evaluator for analyzing conversation logs and primary evaluations."""
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        """Initialize the secondary evaluator.
        
        Args:
            openai_client: OpenAI client for secondary evaluation
        """
        self.openai_client = openai_client or AsyncOpenAI()
        self.logger = ConversationLogger()
    
    async def evaluate_evaluation_quality(
        self,
        evaluations: List[ConversationEvaluation]
    ) -> Dict[str, Any]:
        """Perform secondary evaluation of the primary evaluations.
        
        Args:
            evaluations: List of primary evaluations to analyze
            
        Returns:
            Secondary evaluation results
        """
        self.logger.log_info(f"Performing secondary evaluation of {len(evaluations)} conversations")
        
        # Analyze evaluation patterns
        analysis = {
            "total_conversations": len(evaluations),
            "passed_conversations": len([e for e in evaluations if e.passed]),
            "average_scores": {},
            "common_issues": {},
            "tool_usage_analysis": {},
            "recommendations": []
        }
        
        if not evaluations:
            return analysis
        
        # Calculate averages by dimension
        dimensions = evaluations[0].scores[0].__dict__.keys() if evaluations[0].scores else []
        
        for evaluation in evaluations:
            for score in evaluation.scores:
                if score.dimension not in analysis["average_scores"]:
                    analysis["average_scores"][score.dimension] = []
                analysis["average_scores"][score.dimension].append(score.score)
        
        # Calculate averages
        for dimension in analysis["average_scores"]:
            scores = analysis["average_scores"][dimension]
            analysis["average_scores"][dimension] = sum(scores) / len(scores)
        
        # Analyze tool usage patterns
        all_expected_tools = set()
        all_used_tools = set()
        
        for evaluation in evaluations:
            all_expected_tools.update(evaluation.expected_tools_used)
            all_used_tools.update(evaluation.actual_tools_used)
        
        analysis["tool_usage_analysis"] = {
            "total_expected_tools": len(all_expected_tools),
            "total_used_tools": len(all_used_tools),
            "coverage_rate": len(all_used_tools.intersection(all_expected_tools)) / len(all_expected_tools) if all_expected_tools else 0,
            "most_missing_tools": self._find_most_missing_tools(evaluations)
        }
        
        # Generate meta-recommendations
        analysis["recommendations"] = await self._generate_meta_recommendations(evaluations, analysis)
        
        return analysis
    
    def _find_most_missing_tools(self, evaluations: List[ConversationEvaluation]) -> List[str]:
        """Find the most commonly missing tools across evaluations."""
        
        missing_tool_counts = {}
        
        for evaluation in evaluations:
            for tool in evaluation.missing_tools:
                missing_tool_counts[tool] = missing_tool_counts.get(tool, 0) + 1
        
        # Sort by frequency
        sorted_missing = sorted(missing_tool_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [tool for tool, count in sorted_missing[:5]]  # Top 5
    
    async def _generate_meta_recommendations(
        self,
        evaluations: List[ConversationEvaluation],
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate high-level recommendations based on evaluation patterns."""
        
        recommendations_prompt = f"""
Analyze these hotel agent evaluation results and provide system-level recommendations.

**Overall Statistics:**
- Total conversations: {analysis['total_conversations']}
- Pass rate: {analysis['passed_conversations']}/{analysis['total_conversations']} ({analysis['passed_conversations']/analysis['total_conversations']*100:.1f}%)

**Average Scores by Dimension:**
{chr(10).join([f"- {dim}: {score:.3f}" for dim, score in analysis['average_scores'].items()])}

**Tool Usage Analysis:**
- Coverage rate: {analysis['tool_usage_analysis']['coverage_rate']:.3f}
- Most missing tools: {', '.join(analysis['tool_usage_analysis']['most_missing_tools'])}

**Individual Conversation Issues:**
{chr(10).join([f"- {eval.scenario_id}: {', '.join(eval.recommendations[:2])}" for eval in evaluations[:5]])}

Generate 3-5 high-level system recommendations for improving the hotel agent performance.
Focus on patterns across all conversations rather than individual issues.

**Format:**
- Clear, actionable recommendations
- Focus on system-wide improvements
- Prioritize by impact potential
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior AI systems analyst specializing in conversational AI optimization."},
                    {"role": "user", "content": recommendations_prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            # Parse recommendations from response
            content = response.choices[0].message.content
            recommendations = [line.strip("- ") for line in content.split("\n") if line.strip().startswith("-")]
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            self.logger.log_error(f"Error generating meta-recommendations: {str(e)}")
            return ["Review evaluation results for system optimization opportunities"]