"""
LLM Client wrapper supporting both OpenAI and Google Gemini
"""
import os
import time
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class LLMClient:
    """Universal LLM client supporting OpenAI and Google Gemini"""
    
    def __init__(self, provider: str = "auto", model: Optional[str] = None):
        """
        Initialize LLM client
        
        Args:
            provider: "openai", "google", or "auto" (auto-detect from env vars)
            model: Model name (optional, will use defaults if not provided)
        """
        self.provider = self._detect_provider(provider)
        self.model = model or self._get_default_model()
        self.client = self._initialize_client()
        
    def _detect_provider(self, provider: str) -> str:
        """Detect which provider to use based on environment variables"""
        if provider != "auto":
            return provider
            
        # Auto-detect based on available API keys
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_google = bool(os.getenv("GOOGLE_API_KEY"))
        
        if has_openai and not has_google:
            return "openai"
        elif has_google and not has_openai:
            return "google"
        elif has_openai and has_google:
            # Prefer OpenAI if both available
            return "openai"
        else:
            raise ValueError(
                "No API key found. Please set either OPENAI_API_KEY or GOOGLE_API_KEY"
            )
    
    def _get_default_model(self) -> str:
        """Get default model for the provider"""
        defaults = {
            "openai": "gpt-4o",
            "google": "gemini-2.0-flash-exp"  # or gemini-1.5-pro
        }
        return defaults.get(self.provider, "gpt-4o")
    
    def _initialize_client(self):
        """Initialize the appropriate client"""
        if self.provider == "openai":
            from openai import OpenAI
            return OpenAI()
        elif self.provider == "google":
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            genai.configure(api_key=api_key)
            return genai
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def parse_completion(
        self, 
        messages: List[Dict[str, Any]], 
        response_format: type[BaseModel],
        max_tokens: int = 16384
    ) -> tuple[BaseModel, Dict[str, Any]]:
        """
        Get structured completion from LLM
        
        Args:
            messages: Conversation messages
            response_format: Pydantic model for structured output
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (parsed_response, usage_stats)
        """
        if self.provider == "openai":
            return self._openai_parse(messages, response_format, max_tokens)
        elif self.provider == "google":
            return self._google_parse(messages, response_format, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _openai_parse(
        self, 
        messages: List[Dict[str, Any]], 
        response_format: type[BaseModel],
        max_tokens: int
    ) -> tuple[BaseModel, Dict[str, Any]]:
        """OpenAI structured output"""
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            response_format=response_format,
            messages=messages,
            max_completion_tokens=max_tokens,
        )
        
        parsed = completion.choices[0].message.parsed
        usage = {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens,
        }
        
        return parsed, usage
    
    def _google_parse(
        self, 
        messages: List[Dict[str, Any]], 
        response_format: type[BaseModel],
        max_tokens: int
    ) -> tuple[BaseModel, Dict[str, Any]]:
        """Google Gemini structured output using JSON mode"""
        
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages_to_gemini(messages)
        
        # Get schema from Pydantic model
        schema = response_format.model_json_schema()
        
        # Add schema instruction to system message
        system_content = gemini_messages.get("system_instruction", "")
        system_content += f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        
        # Create model with generation config
        model = self.client.GenerativeModel(
            model_name=self.model,
            system_instruction=system_content,
            generation_config={
                "temperature": 1.0,
                "max_output_tokens": max_tokens,
                "response_mime_type": "application/json",
                "response_schema": schema,
            }
        )
        
        # Generate response
        response = model.generate_content(gemini_messages["contents"])
        
        # Parse JSON response
        try:
            json_data = json.loads(response.text)
            parsed = response_format.model_validate(json_data)
        except Exception as e:
            # Fallback: try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group())
                parsed = response_format.model_validate(json_data)
            else:
                raise ValueError(f"Failed to parse response: {e}\nResponse: {response.text}")
        
        # Estimate usage (Gemini doesn't provide exact token counts in all cases)
        usage = {
            "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
            "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
            "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
        }
        
        return parsed, usage
    
    def _convert_messages_to_gemini(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert OpenAI-style messages to Gemini format"""
        system_instruction = ""
        contents = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction += content + "\n"
            elif role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant":
                # For assistant messages with tool_calls, format them
                if "tool_calls" in msg:
                    tool_text = content + "\n\nTool calls:\n"
                    for tc in msg["tool_calls"]:
                        tool_text += f"- {tc['function']['name']}: {tc['function']['arguments']}\n"
                    contents.append({
                        "role": "model",
                        "parts": [{"text": tool_text}]
                    })
                else:
                    contents.append({
                        "role": "model",
                        "parts": [{"text": content}]
                    })
            elif role == "tool":
                # Tool results go as user messages
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"Tool result:\n{content}"}]
                })
        
        return {
            "system_instruction": system_instruction.strip(),
            "contents": contents
        }
    
    def get_model_name(self) -> str:
        """Get the current model name"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return self.provider


# Example usage
if __name__ == "__main__":
    # Test auto-detection
    client = LLMClient(provider="auto")
    print(f"Using provider: {client.get_provider_name()}")
    print(f"Using model: {client.get_model_name()}")
