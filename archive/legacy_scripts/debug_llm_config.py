#!/usr/bin/env python3
"""Debug LLM configuration and model passing."""

from pathlib import Path
from app.config import AgentConfig
from app.llm import LLMLayer
from dotenv import load_dotenv

load_dotenv()

def debug_llm():
    """Debug LLM configuration."""
    print("="*60)
    print("LLM Configuration Debug")
    print("="*60)
    
    # Check environment
    import os
    print(f"\nEnvironment variables:")
    print(f"  OPENROUTER_API_KEY: {'*' * 10 if os.getenv('OPENROUTER_API_KEY') else 'NOT SET'}")
    print(f"  LLM_MODEL: {os.getenv('LLM_MODEL', 'NOT SET')}")
    print(f"  REFACTOR_LLM_MODEL: {os.getenv('REFACTOR_LLM_MODEL', 'NOT SET')}")
    
    # Create config
    config = AgentConfig.from_env()
    print(f"\nAgentConfig:")
    print(f"  llm.model: {config.llm.model}")
    print(f"  llm.api_key: {'*' * 10 if config.llm.api_key else 'NOT SET'}")
    print(f"  is_local: {config.llm.is_local}")
    
    # Create LLM layer
    llm = LLMLayer(config)
    
    # Try a simple call
    print(f"\nTesting simple LLM call...")
    try:
        response = llm.call([
            {"role": "user", "content": "Say 'test successful'"}
        ])
        print(f"SUCCESS: {response.content}")
    except Exception as e:
        print(f"ERROR: {e}")
        
        # Try with explicit model
        print(f"\nTrying with explicit openrouter model...")
        try:
            response = llm.call([
                {"role": "user", "content": "Say 'test successful'"}
            ], model="openrouter/openai/gpt-5.4-mini")
            print(f"SUCCESS: {response.content}")
        except Exception as e2:
            print(f"ERROR: {e2}")

if __name__ == "__main__":
    debug_llm()
