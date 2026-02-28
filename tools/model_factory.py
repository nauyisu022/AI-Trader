"""
Model Factory - Centralized model creation and management
Handles different LLM providers and their specific requirements
"""

import json
from typing import Optional
from langchain_openai import ChatOpenAI


class DeepSeekChatOpenAI(ChatOpenAI):
    """
    Custom ChatOpenAI wrapper for DeepSeek official API compatibility.
    Handles the case where DeepSeek returns tool_calls.args as JSON strings instead of dicts.
    
    Only use this wrapper when connecting to official DeepSeek API endpoints.
    """

    def _create_message_dicts(self, messages: list, stop: Optional[list] = None) -> list:
        """Override to handle response parsing"""
        message_dicts = super()._create_message_dicts(messages, stop)
        return message_dicts

    def _generate(self, messages: list, stop: Optional[list] = None, **kwargs):
        """Override generation to fix tool_calls format in responses"""
        result = super()._generate(messages, stop, **kwargs)

        for generation in result.generations:
            for gen in generation:
                if hasattr(gen, "message") and hasattr(gen.message, "additional_kwargs"):
                    tool_calls = gen.message.additional_kwargs.get("tool_calls")
                    if tool_calls:
                        for tool_call in tool_calls:
                            if "function" in tool_call and "arguments" in tool_call["function"]:
                                args = tool_call["function"]["arguments"]
                                if isinstance(args, str):
                                    try:
                                        tool_call["function"]["arguments"] = json.loads(args)
                                    except json.JSONDecodeError:
                                        pass

        return result

    async def _agenerate(self, messages: list, stop: Optional[list] = None, **kwargs):
        """Override async generation to fix tool_calls format in responses"""
        result = await super()._agenerate(messages, stop, **kwargs)

        for generation in result.generations:
            for gen in generation:
                if hasattr(gen, "message") and hasattr(gen.message, "additional_kwargs"):
                    tool_calls = gen.message.additional_kwargs.get("tool_calls")
                    if tool_calls:
                        for tool_call in tool_calls:
                            if "function" in tool_call and "arguments" in tool_call["function"]:
                                args = tool_call["function"]["arguments"]
                                if isinstance(args, str):
                                    try:
                                        tool_call["function"]["arguments"] = json.loads(args)
                                    except json.JSONDecodeError:
                                        pass

        return result


def create_chat_model(
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    max_retries: int = 3,
    timeout: int = 30,
    verbose: bool = False,
) -> ChatOpenAI:
    """
    Factory function to create appropriate ChatOpenAI instance based on API provider.
    
    Args:
        model: Model name/identifier
        base_url: API base URL
        api_key: API key
        max_retries: Maximum number of retries
        timeout: Request timeout in seconds
        verbose: Whether to print debug information
        
    Returns:
        ChatOpenAI or DeepSeekChatOpenAI instance
        
    Examples:
        >>> # Official DeepSeek API
        >>> model = create_chat_model(
        ...     model="deepseek-chat",
        ...     base_url="https://api.deepseek.com/v1",
        ...     api_key="sk-xxx"
        ... )
        
        >>> # OpenAI-compatible proxy (e.g., OneAPI)
        >>> model = create_chat_model(
        ...     model="deepseek/deepseek-chat",
        ...     base_url="https://your-proxy.com/v1",
        ...     api_key="sk-xxx"
        ... )
    """
    # Check if using official DeepSeek API based on base_url
    is_official_deepseek = (
        base_url and 
        "deepseek.com" in base_url.lower()
    )
    
    if is_official_deepseek:
        if verbose:
            print("🔧 Using DeepSeekChatOpenAI wrapper for official DeepSeek API")
        return DeepSeekChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout,
        )
    else:
        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout,
        )


def is_deepseek_official_api(base_url: Optional[str]) -> bool:
    """
    Check if the base_url points to official DeepSeek API.
    
    Args:
        base_url: API base URL to check
        
    Returns:
        True if official DeepSeek API, False otherwise
    """
    return base_url is not None and "deepseek.com" in base_url.lower()
