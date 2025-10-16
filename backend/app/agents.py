"""
LLM Agent integration for AI-driven content generation
"""
import os
import structlog
from typing import Dict, Any, Tuple
from anthropic import Anthropic, APIError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .errors import TokenBudgetExceededError

logger = structlog.get_logger()

# Token limits (updated 2025-10-16)
# Total budget: 1,500 tokens per job
# Agent1: 900 tokens (prompt generation)
# Agent2: 600 tokens (JSON formatting)
MAX_AGENT1_TOKENS = int(os.getenv('TOKEN_BUDGET_AGENT1', '900'))
MAX_AGENT2_TOKENS = int(os.getenv('TOKEN_BUDGET_AGENT2', '600'))
MAX_TOTAL_TOKENS = int(os.getenv('TOKEN_BUDGET_TOTAL', '1500'))

# Pricing (per 1M tokens) - Claude Sonnet 4
COST_PER_1M_INPUT_TOKENS = 3.00
COST_PER_1M_OUTPUT_TOKENS = 15.00


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text (rough approximation)

    Rule of thumb: ~4 characters per token for English
    For more accurate estimates, use tiktoken library

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Rough estimate: 1 token ≈ 4 characters
    return len(text) // 4


class Agent1:
    """
    Agent1: Prompt generation from template and user inputs
    """

    def __init__(self):
        """Initialize Agent1"""
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        logger.info("agent1_initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError))
    )
    def generate_prompt(
        self,
        template_name: str,
        inputs: Dict[str, Any],
        temperature: float = 0.7,
        intensity: str = 'medium'
    ) -> Tuple[str, int, int]:
        """
        Generate optimized prompt for Figma content generation

        Args:
            template_name: Template name
            inputs: User input data
            temperature: LLM temperature (0.0-1.0)
            intensity: Generation intensity (low/medium/high)

        Returns:
            Tuple of (generated_prompt, prompt_tokens, completion_tokens)

        Raises:
            TokenBudgetExceededError: If estimated tokens exceed budget
        """
        try:
            # Construct system prompt
            system_prompt = self._build_system_prompt(intensity)

            # Construct user prompt
            user_prompt = self._build_user_prompt(template_name, inputs)

            # Pre-check token budget
            estimated_input_tokens = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
            # Assume max_tokens will be used for output
            estimated_total_tokens = estimated_input_tokens + MAX_AGENT1_TOKENS

            if estimated_total_tokens > MAX_AGENT1_TOKENS:
                logger.warning(
                    "agent1_token_budget_exceeded_precheck",
                    estimated_tokens=estimated_total_tokens,
                    budget=MAX_AGENT1_TOKENS
                )
                raise TokenBudgetExceededError(
                    estimated_tokens=estimated_total_tokens,
                    budget_tokens=MAX_AGENT1_TOKENS,
                    agent="Agent1"
                )

            logger.info(
                "agent1_generate_start",
                template=template_name,
                temperature=temperature,
                intensity=intensity,
                estimated_input_tokens=estimated_input_tokens
            )

            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=MAX_AGENT1_TOKENS,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            generated_prompt = response.content[0].text
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens

            # Check Agent1 token limit (actual usage)
            total_tokens = prompt_tokens + completion_tokens
            if total_tokens > MAX_AGENT1_TOKENS:
                logger.warning(
                    "agent1_token_budget_exceeded_actual",
                    actual_tokens=total_tokens,
                    budget=MAX_AGENT1_TOKENS
                )
                raise TokenBudgetExceededError(
                    estimated_tokens=total_tokens,
                    budget_tokens=MAX_AGENT1_TOKENS,
                    agent="Agent1"
                )

            logger.info(
                "agent1_generate_success",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                output_length=len(generated_prompt)
            )

            return generated_prompt, prompt_tokens, completion_tokens

        except TokenBudgetExceededError:
            # Re-raise without wrapping
            raise
        except RateLimitError as e:
            logger.error("agent1_rate_limit", error=str(e))
            raise
        except APIError as e:
            logger.error("agent1_api_error", error=str(e))
            raise
        except Exception as e:
            logger.error("agent1_error", error=str(e), exc_info=True)
            raise

    def _build_system_prompt(self, intensity: str) -> str:
        """Build system prompt based on intensity"""
        base_prompt = """You are a creative content generator for Figma templates.
Your task is to generate compelling, on-brand content based on user inputs.

Guidelines:
- Be concise but impactful
- Match the tone to the template type
- Follow brand guidelines if provided
- Ensure content fits visual constraints"""

        intensity_prompts = {
            'low': "\n- Keep content minimal and straightforward",
            'medium': "\n- Balance creativity with clarity",
            'high': "\n- Be bold and creative, push boundaries"
        }

        return base_prompt + intensity_prompts.get(intensity, intensity_prompts['medium'])

    def _build_user_prompt(self, template_name: str, inputs: Dict[str, Any]) -> str:
        """Build user prompt from template and inputs"""
        inputs_str = "\n".join([f"- {key}: {value}" for key, value in inputs.items()])

        return f"""Template: {template_name}

User Inputs:
{inputs_str}

Generate optimized content for each field in the template. Return as JSON format:
{{
  "field_name": "generated content",
  ...
}}"""


class Agent2:
    """
    Agent2: Format Agent1 output to structured JSON
    """

    def __init__(self):
        """Initialize Agent2"""
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        logger.info("agent2_initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError))
    )
    def format_to_json(
        self,
        agent1_output: str,
        template_name: str
    ) -> Tuple[Dict[str, Any], int, int]:
        """
        Format Agent1 output to structured JSON

        Args:
            agent1_output: Raw output from Agent1
            template_name: Template name

        Returns:
            Tuple of (formatted_json, prompt_tokens, completion_tokens)

        Raises:
            TokenBudgetExceededError: If estimated tokens exceed budget
        """
        try:
            system_prompt = """You are a JSON formatter. Convert the provided content into valid JSON format.
Ensure all fields are properly escaped and formatted."""

            user_prompt = f"""Template: {template_name}

Content to format:
{agent1_output}

Return ONLY valid JSON, no additional text."""

            # Pre-check token budget
            estimated_input_tokens = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
            # Assume max_tokens will be used for output
            estimated_total_tokens = estimated_input_tokens + MAX_AGENT2_TOKENS

            if estimated_total_tokens > MAX_AGENT2_TOKENS:
                logger.warning(
                    "agent2_token_budget_exceeded_precheck",
                    estimated_tokens=estimated_total_tokens,
                    budget=MAX_AGENT2_TOKENS
                )
                raise TokenBudgetExceededError(
                    estimated_tokens=estimated_total_tokens,
                    budget_tokens=MAX_AGENT2_TOKENS,
                    agent="Agent2"
                )

            logger.info(
                "agent2_format_start",
                template=template_name,
                estimated_input_tokens=estimated_input_tokens
            )

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=MAX_AGENT2_TOKENS,
                temperature=0.0,  # Deterministic for formatting
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            json_output = response.content[0].text
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens

            # Check Agent2 token limit (actual usage)
            total_tokens = prompt_tokens + completion_tokens
            if total_tokens > MAX_AGENT2_TOKENS:
                logger.warning(
                    "agent2_token_budget_exceeded_actual",
                    actual_tokens=total_tokens,
                    budget=MAX_AGENT2_TOKENS
                )
                raise TokenBudgetExceededError(
                    estimated_tokens=total_tokens,
                    budget_tokens=MAX_AGENT2_TOKENS,
                    agent="Agent2"
                )

            # Parse JSON to validate
            import json
            parsed_json = json.loads(json_output)

            logger.info(
                "agent2_format_success",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                fields_count=len(parsed_json)
            )

            return parsed_json, prompt_tokens, completion_tokens

        except json.JSONDecodeError as e:
            logger.error("agent2_json_decode_error", error=str(e), output=json_output)
            raise ValueError(f"Invalid JSON output: {str(e)}")
        except TokenBudgetExceededError:
            # Re-raise without wrapping
            raise
        except RateLimitError as e:
            logger.error("agent2_rate_limit", error=str(e))
            raise
        except APIError as e:
            logger.error("agent2_api_error", error=str(e))
            raise
        except Exception as e:
            logger.error("agent2_error", error=str(e), exc_info=True)
            raise


def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate cost in USD for token usage

    Args:
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Estimated cost in USD
    """
    input_cost = (prompt_tokens / 1_000_000) * COST_PER_1M_INPUT_TOKENS
    output_cost = (completion_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
    total_cost = input_cost + output_cost

    logger.debug(
        "cost_calculated",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=total_cost
    )

    return round(total_cost, 6)


def check_rate_limit(user_id: str) -> bool:
    """
    Check if user is within rate limits

    TODO: Implement actual rate limiting with Redis
    For now, returns True (rate limiting handled by Flask-Limiter)

    Args:
        user_id: User ID

    Returns:
        True if within limits, False otherwise
    """
    # Placeholder - implement with Redis counter
    return True
