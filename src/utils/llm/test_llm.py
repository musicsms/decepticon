#!/usr/bin/env python3
"""
LLM Model Testing CLI

This script allows you to test different LLM models interactively.
Usage: python test_llm.py
"""

import os
import sys
import argparse
from typing import Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.utils.llm import (
    load_llm,
    list_available_models,
    list_available_providers,
    print_model_selection_help,
    get_model_selection_info,
    get_ollama_info,
    validate_model_config
)


def print_banner():
    """Print application banner"""
    print("🤖 DecepticonV2 LLM Model Tester")
    print("=" * 50)


def interactive_model_selection():
    """Interactive model selection"""
    print("\\n📋 Available Models:")
    models = list_available_models()
    
    available_models = [m for m in models if m["api_key_available"]]
    unavailable_models = [m for m in models if not m["api_key_available"]]
    
    if not available_models:
        print("❌ No models available. Please set up API keys or start Ollama.")
        print("\\nFor cloud models, set environment variables:")
        for model in models[:5]:  # Show first 5
            if model["provider"] != "ollama":
                provider = model["provider"].upper()
                print(f"   {provider}_API_KEY")
        print("\\nFor local models:")
        print("   Download and start Ollama from https://ollama.ai/")
        return None, None
    
    print("\\n✅ Available Models:")
    for i, model in enumerate(available_models, 1):
        tools = "🔧" if model["supports_tools"] else "  "
        stream = "⚡" if model["supports_streaming"] else "  "
        local = "🏠" if model["provider"] == "ollama" else "☁️"
        print(f"   {i:2d}. {tools}{stream}{local} {model['display_name']}")
        if model.get("description"):
            print(f"       {model['description']}")
    
    if unavailable_models:
        print("\\n❌ Unavailable Models:")
        cloud_models = [m for m in unavailable_models if m["provider"] != "ollama"]
        ollama_models = [m for m in unavailable_models if m["provider"] == "ollama"]
        
        if cloud_models:
            print("   Missing API keys:")
            for model in cloud_models[:3]:
                print(f"       {model['display_name']} ({model['provider']})")
        
        if ollama_models:
            print("   Ollama not running:")
            for model in ollama_models[:3]:
                print(f"       {model['display_name']}")
    
    while True:
        try:
            choice = input(f"\\nSelect model (1-{len(available_models)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None, None
            
            idx = int(choice) - 1
            if 0 <= idx < len(available_models):
                selected = available_models[idx]
                return selected["model_name"], selected["provider"]
            else:
                print(f"❌ Please enter a number between 1 and {len(available_models)}")
        except ValueError:
            print("❌ Please enter a valid number or 'q' to quit")


def test_model(model_name: str, provider: str, prompt: Optional[str] = None):
    """Test a specific model"""
    print(f"\\n🔄 Loading {model_name} ({provider})...")
    
    try:
        # Load the model
        llm = load_llm(model_name, provider, temperature=0.0)
        print("✅ Model loaded successfully!")
        
        # Test prompt
        test_prompt = prompt or "Hello! Can you tell me about yourself in one sentence?"
        print(f"\\n💬 Testing with prompt: '{test_prompt}'")
        print("\\n🤖 Response:")
        print("-" * 40)
        
        response = llm.invoke(test_prompt)
        print(response.content)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if "ollama" in provider.lower():
            print("💡 Tip: Make sure Ollama is running and the model is installed")
            print("   Start Ollama: ollama serve")
            print(f"   Install model: ollama pull {model_name}")
        return False


def chat_mode(model_name: str, provider: str):
    """Interactive chat mode"""
    print(f"\\n💬 Starting chat mode with {model_name} ({provider})")
    print("Type 'quit' or 'exit' to stop, 'help' for commands\\n")
    
    try:
        llm = load_llm(model_name, provider, temperature=0.1)
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'help':
                print("Commands:")
                print("  quit/exit/q - Exit chat")
                print("  help - Show this help")
                continue
            elif not user_input:
                continue
            
            try:
                print("🤖 Assistant: ", end="", flush=True)
                
                # Try streaming if supported
                try:
                    for chunk in llm.stream(user_input):
                        print(chunk.content, end="", flush=True)
                    print()  # New line after streaming
                except:
                    # Fallback to regular invoke
                    response = llm.invoke(user_input)
                    print(response.content)
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    except Exception as e:
        print(f"❌ Failed to start chat: {str(e)}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Test LLM models")
    parser.add_argument("--model", "-m", help="Model name")
    parser.add_argument("--provider", "-p", help="Provider name")
    parser.add_argument("--prompt", help="Test prompt")
    parser.add_argument("--chat", "-c", action="store_true", help="Start interactive chat")
    parser.add_argument("--list", "-l", action="store_true", help="List available models")
    parser.add_argument("--info", "-i", action="store_true", help="Show model information")
    parser.add_argument("--ollama", "-o", action="store_true", help="Show Ollama status")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Handle list command
    if args.list:
        print_model_selection_help()
        return
    
    # Handle info command
    if args.info:
        info = get_model_selection_info()
        print(f"\\n📊 Model Statistics:")
        print(f"   Total models: {info['total_models']}")
        print(f"   Available providers: {info['available_providers']}")
        print(f"   Total providers: {len(info['providers'])}")
        
        # Show Ollama specific info
        ollama_info = get_ollama_info()
        if ollama_info["connected"]:
            print(f"\\n🟢 Ollama Status:")
            print(f"   Running at: {ollama_info['url']}")
            print(f"   Installed models: {ollama_info['installed_count']}")
            if ollama_info["installed_models"]:
                print(f"   Models: {', '.join(ollama_info['installed_models'][:5])}")
                if len(ollama_info["installed_models"]) > 5:
                    print(f"   ... and {len(ollama_info['installed_models']) - 5} more")
        else:
            print(f"\\n🔴 Ollama Status: Not running")
            print(f"   Error: {ollama_info.get('error', 'Connection failed')}")
            print(f"   💡 Start with: ollama serve")
        return
    
    # Handle ollama command
    if args.ollama:
        ollama_info = get_ollama_info()
        print(f"\\n🔍 Ollama Status Check:")
        print(f"   URL: {ollama_info['url']}")
        if ollama_info["connected"]:
            print(f"   Status: 🟢 Running")
            print(f"   Installed models: {ollama_info['installed_count']}")
            if ollama_info["installed_models"]:
                print(f"   Available models:")
                for model in ollama_info["installed_models"]:
                    print(f"      • {model}")
            else:
                print(f"   💡 No models installed. Try: ollama pull llama3.1")
        else:
            print(f"   Status: 🔴 Not running")
            print(f"   Error: {ollama_info.get('error', 'Connection failed')}")
            print(f"   💡 Commands:")
            print(f"      Start Ollama: ollama serve")
            print(f"      Install model: ollama pull llama3.1")
        return
    
    # Get model selection
    if args.model and args.provider:
        model_name, provider = args.model, args.provider
        
        # Validate configuration
        config_result = validate_model_config({
            "model": model_name,
            "provider": provider
        })
        
        if not config_result["valid"]:
            print(f"❌ Configuration error: {config_result['error']}")
            if "missing_env_var" in config_result:
                print(f"   Please set: {config_result['missing_env_var']}")
            elif "missing_service" in config_result:
                print(f"   Please start Ollama: ollama serve")
            return
        
    else:
        model_name, provider = interactive_model_selection()
        if not model_name:
            return
    
    # Test the model
    if args.chat:
        chat_mode(model_name, provider)
    else:
        success = test_model(model_name, provider, args.prompt)
        if success and not args.prompt:
            # Ask if user wants to continue to chat mode
            response = input("\\n🤔 Would you like to start chat mode? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                chat_mode(model_name, provider)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n\\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
