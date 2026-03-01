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
    Also ensures message content is always a string, not a list.
    
    Only use this wrapper when connecting to official DeepSeek API endpoints.
    """
    
    def _convert_message_to_dict(self, message):
        """Convert a message to dict format, ensuring content is string"""
        from langchain_core.messages import BaseMessage
        
        if isinstance(message, BaseMessage):
            msg_dict = message.dict()
        elif isinstance(message, dict):
            msg_dict = message.copy()
        else:
            return message
            
        # DeepSeek API requires content to be string, not list
        if "content" in msg_dict and isinstance(msg_dict["content"], list):
            content_parts = []
            for part in msg_dict["content"]:
                if isinstance(part, dict):
                    if "text" in part:
                        content_parts.append(part["text"])
                    elif "type" in part and part["type"] == "text":
                        content_parts.append(part.get("text", ""))
                    else:
                        content_parts.append(str(part))
                else:
                    content_parts.append(str(part))
            msg_dict["content"] = "\n".join(content_parts) if content_parts else ""
            
        return msg_dict

    def _create_message_dicts(self, messages: list, stop: Optional[list] = None) -> list:
        """Override to handle request formatting - ensure content is always string"""
        message_dicts = super()._create_message_dicts(messages, stop)
        
        # Convert all message contents from list to string if needed
        converted_dicts = []
        for msg in message_dicts:
            converted_msg = self._convert_message_to_dict(msg)
            converted_dicts.append(converted_msg)
        
        return converted_dicts

    def _convert_messages_for_api(self, messages: list) -> list:
        """Convert messages to ensure content is always string for DeepSeek API"""
        from langchain_core.messages import BaseMessage
        
        converted = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                # Convert BaseMessage to dict
                msg_dict = msg.dict() if hasattr(msg, 'dict') else msg.model_dump()
                
                # Fix content if it's a list
                if "content" in msg_dict and isinstance(msg_dict["content"], list):
                    content_parts = []
                    for part in msg_dict["content"]:
                        if isinstance(part, dict):
                            if "text" in part:
                                content_parts.append(part["text"])
                            elif "type" in part and part["type"] == "text":
                                content_parts.append(part.get("text", ""))
                            else:
                                content_parts.append(str(part))
                        else:
                            content_parts.append(str(part))
                    msg_dict["content"] = "\n".join(content_parts) if content_parts else ""
                
                # Reconstruct message
                converted.append(type(msg)(**msg_dict))
            else:
                converted.append(msg)
        
        return converted
    
    def _generate(self, messages: list, stop: Optional[list] = None, **kwargs):
        """Override generation to fix message format and tool_calls in responses"""
        # Convert messages to ensure content is string
        messages = self._convert_messages_for_api(messages)
        
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
        """Override async generation to fix message format and tool_calls in responses"""
        # Convert messages to ensure content is string
        messages = self._convert_messages_for_api(messages)
        
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
