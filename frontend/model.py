import streamlit as st
import time

class ModelSelectionUI:
    """Simple Dropdown Model Selection UI Class"""
    
    def __init__(self, theme_manager):
        """UI initialization"""
        self.theme_manager = theme_manager
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize model selection related session state"""
        if "models_by_provider" not in st.session_state:
            st.session_state.models_by_provider = {}
    
    def get_provider_info(self, provider):
        """Provider information"""
        provider_info = {
            "Anthropic": {"name": "Anthropic"},
            "OpenAI": {"name": "OpenAI"},
            "DeepSeek": {"name": "DeepSeek"},
            "Gemini": {"name": "Gemini"},
            "Groq": {"name": "Groq"},
            "Ollama": {"name": "Ollama"}
        }
        return provider_info.get(provider, {"name": provider})

    def load_models_data(self):
        """Load model data - returns status dict instead of displaying messages"""
        try:
            from src.utils.llm.models import list_available_models, check_ollama_connection
            
            # Return loading status info
            models = list_available_models()
            ollama_info = check_ollama_connection()
            
            available_models = [m for m in models if m.get("api_key_available", False)]
            
            if not available_models:
                return {
                    "success": False,
                    "error": "No models available. Please set up your API keys.",
                    "type": "error"
                }
            
            # Group models by provider
            st.session_state.models_by_provider = {}
            for model in available_models:
                provider = model.get('provider', 'Unknown')
                if provider not in st.session_state.models_by_provider:
                    st.session_state.models_by_provider[provider] = []
                st.session_state.models_by_provider[provider].append(model)
            
            # Return success status with Ollama info if connected
            result = {"success": True, "type": "success"}
            if ollama_info.get("connected", False):
                result["ollama_message"] = f"Ollama Connected - {ollama_info.get('count', 0)} local models available"
            
            return result
            
        except ImportError as e:
            return {
                "success": False,
                "error": "Model selection feature unavailable",
                "info": "Setup Required: Please install CLI dependencies",
                "type": "import_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error loading models: {str(e)}",
                "type": "error"
            }

    def get_default_selection(self):
        """Get default provider and model selection"""
        # Default to Anthropic and Claude 3.5 Sonnet if available
        default_provider = None
        default_model = None
        
        # Look for Anthropic provider (case insensitive)
        anthropic_provider_key = None
        for provider_key in st.session_state.models_by_provider.keys():
            if provider_key.lower() == "anthropic":
                anthropic_provider_key = provider_key
                break
        
        if anthropic_provider_key:
            anthropic_models = st.session_state.models_by_provider[anthropic_provider_key]
            for model in anthropic_models:
                if "claude-3-5-sonnet" in model.get("model_name", "").lower():
                    default_provider = anthropic_provider_key
                    default_model = model
                    break
        
        # If Claude 3.5 Sonnet not found, use first available Anthropic model
        if not default_model and anthropic_provider_key:
            default_provider = anthropic_provider_key
            default_model = st.session_state.models_by_provider[anthropic_provider_key][0]
        
        # If no Anthropic models, use first available provider and model
        if not default_model:
            providers = list(st.session_state.models_by_provider.keys())
            if providers:
                default_provider = providers[0]
                default_model = st.session_state.models_by_provider[default_provider][0]
        
        return default_provider, default_model

    def display_model_selection_ui(self):
        """Simple dropdown-based model selection UI"""
        # Center the content
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Load model data (first time only)
            if not st.session_state.models_by_provider:
                with st.spinner("Loading available models..."):
                    load_result = self.load_models_data()
                
                # Display messages within col2
                if not load_result["success"]:
                    if load_result["type"] == "import_error":
                        st.error(load_result["error"])
                        st.info(load_result["info"])
                    else:
                        st.error(load_result["error"])
                    return None
                
                # Show Ollama success message if available
                if "ollama_message" in load_result:
                    st.success(load_result["ollama_message"])
            
            # Header
            st.markdown("### Select AI Model")
            st.markdown("Choose the AI model for your red team operations")
            st.markdown("---")
            
            # Get default selections
            default_provider, default_model = self.get_default_selection()
            
            # Step 1: Provider selection
            providers = list(st.session_state.models_by_provider.keys())
            provider_options = []
            provider_mapping = {}
            
            default_provider_index = 0
            
            for idx, provider_key in enumerate(providers):
                provider_info = self.get_provider_info(provider_key)
                display_text = provider_info['name']
                provider_options.append(display_text)
                provider_mapping[display_text] = provider_key  # Map display name to actual key
                
                # Set default index if this is the default provider
                if provider_key == default_provider:
                    default_provider_index = idx
            
            selected_provider_display = st.selectbox(
                "Provider",
                options=provider_options,
                index=default_provider_index,
                help="Choose your service provider",
                key="provider_selection"
            )
            
            selected_provider_key = provider_mapping[selected_provider_display]
            
            # Step 2: Model selection
            if selected_provider_key and selected_provider_key in st.session_state.models_by_provider:
                models = st.session_state.models_by_provider[selected_provider_key]
                model_options = []
                model_mapping = {}
                
                default_model_index = 0
                
                for idx, model in enumerate(models):
                    # Clean model name - remove provider prefix and simplify
                    display_name = model.get('display_name', 'Unknown Model')
                    
                    # Clean up display name
                    for prefix in [f"[{selected_provider_key}]", f"[{selected_provider_key.lower()}]", 
                                 f"{selected_provider_key}", f"{selected_provider_key.lower()}"]:
                        if prefix in display_name:
                            display_name = display_name.replace(f"{prefix} ", "").replace(prefix, "")
                    
                    model_options.append(display_name)
                    model_mapping[display_name] = model
                    
                    # Set default index if this matches the default model
                    if (default_model and 
                        model.get('model_name') == default_model.get('model_name')):
                        default_model_index = idx
                
                if model_options:  # Only show if there are models available
                    selected_model_display = st.selectbox(
                        "Model",
                        options=model_options,
                        index=default_model_index,
                        help="Choose the specific model variant",
                        key="model_selection"
                    )
                    
                    selected_model = model_mapping[selected_model_display]
                    
                    # Confirmation button
                    st.markdown("---")
                    if st.button("Initialize AI Agents", type="primary", use_container_width=True):
                        # Initialize with spinner directly (no extra messages)
                        with st.spinner(f"Initializing {selected_model.get('display_name', 'AI agents')} for red team operations..."):
                            result = self.initialize_agents(selected_model)
                        
                        if result["success"]:
                            st.success(result.get("message", "AI Agents initialized successfully!"))
                            # Small delay to show success message
                            time.sleep(1.5)
                            return selected_model
                        else:
                            st.error(result.get("error", "Failed to initialize AI agents"))
                            return None
                else:
                    st.warning(f"No models available for {selected_provider_display}")
            else:
                st.warning("Please select a valid provider")
        
        return None
    

    

    
    def initialize_agents(self, selected_model):
        """Initialize AI agents - replace this with your actual initialization logic"""
        try:
            # Simulate initialization time
            time.sleep(2)
            
            # Here you would add your actual agent initialization code
            # For example:
            # from src.your_agent_module import initialize_agents
            # success = initialize_agents(selected_model)
            
            # Simulate success/failure for demonstration
            # Replace this with your actual initialization logic
            import random
            if random.choice([True, True, True, False]):  # 75% success rate for demo
                return {
                    "success": True,
                    "message": f"Successfully initialized {selected_model.get('display_name', 'AI agents')} for red team operations!"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to connect to the selected model. Please check your API configuration."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Initialization error: {str(e)}"
            }

    def show_loading_screen(self, model_info):
        """Simple loading screen"""
        provider_info = self.get_provider_info(model_info.get('provider', 'Unknown'))
        
        # Center the loading content
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 60px 0;">
                <h2>Setting up {model_info.get('display_name', 'Model')}</h2>
                <p style="opacity: 0.7;">Initializing AI agents for red team operations...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
        
        return st.empty()

    def reset_selection(self):
        """Reset model selection state"""
        if "models_by_provider" in st.session_state:
            st.session_state.models_by_provider = {}
