"""
LLM Selection utilities for CLI and frontend
"""

import os
from typing import Dict, Any, Optional, List
from .models import (
    load_llm,
    list_available_models, 
    list_available_providers,
    LLMModelManager,
    ModelProvider,
    validate_api_key,
    check_ollama_connection,
    get_installed_ollama_models
)


def get_ollama_info() -> Dict[str, Any]:
    """
    Get Ollama connection and model information
    
    Returns:
        Dictionary with Ollama status and available models
    """
    connection_info = check_ollama_connection()
    installed_models = get_installed_ollama_models()
    
    manager = LLMModelManager()
    configured_models = manager.get_models_by_provider(ModelProvider.OLLAMA)
    
    return {
        "connected": connection_info["connected"],
        "url": connection_info["url"],
        "error": connection_info.get("error"),
        "installed_models": installed_models,
        "installed_count": len(installed_models),
        "configured_models": [model.model_name for model in configured_models if model.model_name != "-"],
        "configured_count": len([model for model in configured_models if model.model_name != "-"])
    }


def get_model_selection_info() -> Dict[str, Any]:
    """
    Get comprehensive model selection information for UI
    
    Returns:
        Dictionary containing providers, models, and status information
    """
    providers = list_available_providers()
    models = list_available_models()
    
    # Group models by provider
    models_by_provider = {}
    for model in models:
        provider = model["provider"]
        if provider not in models_by_provider:
            models_by_provider[provider] = []
        models_by_provider[provider].append(model)
    
    return {
        "providers": providers,
        "models": models,
        "models_by_provider": models_by_provider,
        "total_models": len(models),
        "available_providers": len([p for p in providers if p["api_key_available"]])
    }


def create_model_selection_menu() -> List[Dict[str, Any]]:
    """
    Create a structured menu for model selection
    
    Returns:
        List of menu items with model information
    """
    models = list_available_models()
    menu_items = []
    
    for model in models:
        status = "✅" if model["api_key_available"] else "❌"
        
        menu_items.append({
            "id": f"{model['provider']}:{model['model_name']}",
            "display": f"{status} {model['display_name']}",
            "description": model.get("description", ""),
            "provider": model["provider"],
            "model_name": model["model_name"],
            "available": model["api_key_available"],
            "supports_tools": model.get("supports_tools", True),
            "supports_streaming": model.get("supports_streaming", True),
            "context_length": model.get("context_length")
        })
    
    # Sort by availability first, then by provider and model name
    menu_items.sort(key=lambda x: (not x["available"], x["provider"], x["model_name"]))
    
    return menu_items


def get_model_from_selection(selection: str) -> Optional[Dict[str, str]]:
    """
    Parse model selection string and return model info
    
    Args:
        selection: Model selection in format "provider:model_name" or just "model_name"
    
    Returns:
        Dictionary with provider and model_name, or None if invalid
    """
    if ":" in selection:
        provider, model_name = selection.split(":", 1)
        return {"provider": provider, "model_name": model_name}
    else:
        # Try to find model by name
        models = list_available_models()
        for model in models:
            if model["model_name"] == selection or model["display_name"] == selection:
                return {"provider": model["provider"], "model_name": model["model_name"]}
        return None


def create_configurable_llm(**kwargs):
    """
    Create a configurable LLM that can be changed at runtime
    
    Args:
        **kwargs: Additional arguments for the model
    
    Returns:
        Configurable chat model that can be configured with different models at runtime
    """
    # Filter out None values from kwargs
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    return load_llm(
        configurable_fields=("model", "model_provider"),
        **filtered_kwargs
    )


def load_model_from_config(config: Dict[str, Any], **kwargs):
    """
    Load model from configuration dictionary
    
    Args:
        config: Configuration containing 'model' and optionally 'provider'
        **kwargs: Additional arguments for the model
    
    Returns:
        Initialized chat model
    """
    model_name = config.get("model")
    provider = config.get("provider")
    temperature = config.get("temperature", 0.0)
    max_tokens = config.get("max_tokens")
    
    # Prepare kwargs, excluding None values
    load_kwargs = {"temperature": temperature, **kwargs}
    
    # Only add max_tokens if it's not None
    if max_tokens is not None:
        load_kwargs["max_tokens"] = max_tokens
    
    return load_llm(
        model_name=model_name,
        provider=provider,
        **load_kwargs
    )


def validate_model_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate model configuration
    
    Args:
        config: Model configuration to validate
    
    Returns:
        Dictionary with validation results
    """
    model_name = config.get("model")
    provider = config.get("provider")
    
    if not model_name:
        return {
            "valid": False,
            "error": "Model name is required"
        }
    
    try:
        # Try to get model config
        manager = LLMModelManager()
        model_config = manager.get_model_config(model_name, provider)
        
        if model_config:
            # Check API key
            if not validate_api_key(model_config.provider):
                if model_config.provider == ModelProvider.OLLAMA:
                    return {
                        "valid": False,
                        "error": "Ollama is not running or not accessible",
                        "missing_service": "ollama"
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"API key not found for {model_config.provider.value}",
                        "missing_env_var": f"{model_config.provider.value.upper()}_API_KEY"
                    }
            
            return {
                "valid": True,
                "model_config": {
                    "display_name": model_config.display_name,
                    "model_name": model_config.model_name,
                    "provider": model_config.provider.value,
                    "description": model_config.description,
                    "supports_tools": model_config.supports_tools,
                    "supports_streaming": model_config.supports_streaming
                }
            }
        else:
            # Model not in our config, but might still be valid
            if provider:
                try:
                    provider_enum = ModelProvider(provider)
                    if not validate_api_key(provider_enum):
                        if provider_enum == ModelProvider.OLLAMA:
                            return {
                                "valid": False,
                                "error": "Ollama is not running",
                                "missing_service": "ollama"
                            }
                        else:
                            return {
                                "valid": False,
                                "error": f"API key not found for {provider}",
                                "missing_env_var": f"{provider.upper()}_API_KEY"
                            }
                except ValueError:
                    return {
                        "valid": False,
                        "error": f"Unsupported provider: {provider}"
                    }
            
            return {
                "valid": True,
                "warning": "Model not in configuration, but might be valid"
            }
    
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


def get_missing_dependencies() -> List[Dict[str, Any]]:
    """
    Check for missing provider dependencies
    
    Returns:
        List of missing dependencies with installation instructions
    """
    dependencies = [
        {"provider": "openai", "package": "langchain-openai", "pip": "langchain-openai"},
        {"provider": "anthropic", "package": "langchain-anthropic", "pip": "langchain-anthropic"},
        {"provider": "google_genai", "package": "langchain-google-genai", "pip": "langchain-google-genai"},
        {"provider": "groq", "package": "langchain-groq", "pip": "langchain-groq"},
        {"provider": "mistralai", "package": "langchain-mistralai", "pip": "langchain-mistralai"},
        {"provider": "xai", "package": "langchain-xai", "pip": "langchain-xai"},
        {"provider": "perplexity", "package": "langchain-perplexity", "pip": "langchain-perplexity"},
        {"provider": "deepseek", "package": "langchain-deepseek", "pip": "langchain-deepseek"},
        {"provider": "ollama", "package": "langchain-ollama", "pip": "langchain-ollama"},
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep["package"].replace("-", "_"))
        except ImportError:
            missing.append(dep)
    
    return missing


def print_model_selection_help():
    """Print help information for model selection"""
    print("\\n🤖 Available LLM Models:")
    print("=" * 50)
    
    info = get_model_selection_info()
    
    for provider_info in info["providers"]:
        provider = provider_info["name"]
        status = "✅ Available" if provider_info["api_key_available"] else "❌ Missing API Key"
        count = provider_info["model_count"]
        
        print(f"\\n📦 {provider_info['display_name']} ({count} models) - {status}")
        
        if provider == "ollama":
            # Special handling for Ollama
            ollama_info = get_ollama_info()
            if ollama_info["connected"]:
                print(f"   🟢 Ollama running at {ollama_info['url']}")
                print(f"   📥 Installed models: {ollama_info['installed_count']}")
                if ollama_info["installed_models"][:3]:  # Show first 3 installed models
                    for model in ollama_info["installed_models"][:3]:
                        print(f"      • {model}")
                    if len(ollama_info["installed_models"]) > 3:
                        print(f"      ... and {len(ollama_info['installed_models']) - 3} more")
            else:
                print(f"   🔴 Ollama not running: {ollama_info.get('error', 'Connection failed')}")
                print(f"   💡 Start Ollama: Download from https://ollama.ai/")
        elif provider_info["api_key_available"]:
            models = info["models_by_provider"].get(provider, [])
            for model in models[:3]:  # Show first 3 models
                print(f"   • {model['display_name']}")
            if len(models) > 3:
                print(f"   ... and {len(models) - 3} more")
        else:
            print(f"   Set {provider.upper()}_API_KEY environment variable")
    
    missing_deps = get_missing_dependencies()
    if missing_deps:
        print("\\n⚠️  Missing Dependencies:")
        for dep in missing_deps:
            print(f"   pip install {dep['pip']}")
    
    print("\\n💡 Usage Examples:")
    print("   load_llm('gpt-4o', 'openai')")
    print("   load_llm('claude-3-5-sonnet-latest', 'anthropic')")
    print("   load_llm('llama3.3:70b', 'ollama')  # Ollama model")
    print("   load_llm('deepseek-chat', 'deepseek')")
    print("   load_llm()  # Configurable model")


__all__ = [
    "get_model_selection_info",
    "get_ollama_info",
    "create_model_selection_menu", 
    "get_model_from_selection",
    "create_configurable_llm",
    "load_model_from_config",
    "validate_model_config",
    "get_missing_dependencies",
    "print_model_selection_help"
]
