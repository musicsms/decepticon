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
        """Load model data"""
        try:
            from src.utils.llm.models import list_available_models, check_ollama_connection
            
            with st.spinner("Loading available models..."):
                models = list_available_models()
                ollama_info = check_ollama_connection()
            
            available_models = [m for m in models if m.get("api_key_available", False)]
            
            if not available_models:
                st.error("No models available. Please set up your API keys.")
                return False
            
            # Group models by provider
            st.session_state.models_by_provider = {}
            for model in available_models:
                provider = model.get('provider', 'Unknown')
                if provider not in st.session_state.models_by_provider:
                    st.session_state.models_by_provider[provider] = []
                st.session_state.models_by_provider[provider].append(model)
            
            # Show Ollama info
            if ollama_info.get("connected", False):
                st.success(f"Ollama Connected - {ollama_info.get('count', 0)} local models available")
            
            return True
            
        except ImportError as e:
            st.error("Model selection feature unavailable")
            st.info("Setup Required: Please install CLI dependencies")
            return False
        except Exception as e:
            st.error(f"Error loading models: {str(e)}")
            return False

    def get_default_selection(self):
        """Get default provider and model selection"""
        # Default to Anthropic and Claude 3.5 Sonnet if available
        default_provider = None
        default_model = None
        
        if "anthropic" in st.session_state.models_by_provider:
            anthropic_models = st.session_state.models_by_provider["anthropic"]
            for model in anthropic_models:
                if "claude-3-5-sonnet" in model.get("model_name", "").lower():
                    default_provider = "anthropic"
                    default_model = model
                    break
        
        # If Claude 3.5 Sonnet not found, use first available Anthropic model
        if not default_model and "anthropic" in st.session_state.models_by_provider:
            default_provider = "anthropic"
            default_model = st.session_state.models_by_provider["anthropic"][0]
        
        # If no Anthropic models, use first available provider and model
        if not default_model:
            providers = list(st.session_state.models_by_provider.keys())
            if providers:
                default_provider = providers[0]
                default_model = st.session_state.models_by_provider[default_provider][0]
        
        return default_provider, default_model

    def display_model_selection_ui(self):
        """Simple dropdown-based model selection UI"""
        # Load model data (first time only)
        if not st.session_state.models_by_provider:
            if not self.load_models_data():
                return None
        
        # Center the content
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
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
            
            for idx, provider in enumerate(providers):
                provider_info = self.get_provider_info(provider)
                display_text = provider_info['name']
                provider_options.append(display_text)
                provider_mapping[display_text] = provider
                
                # Set default index if this is the default provider
                if provider == default_provider:
                    default_provider_index = idx
            
            selected_provider_display = st.selectbox(
                "Provider",
                options=provider_options,
                index=default_provider_index,
                help="Choose your service provider"
            )
            
            selected_provider = provider_mapping[selected_provider_display]
            
            # Step 2: Model selection
            if selected_provider:
                models = st.session_state.models_by_provider[selected_provider]
                model_options = []
                model_mapping = {}
                
                default_model_index = 0
                
                for idx, model in enumerate(models):
                    # Clean model name - remove provider prefix and simplify
                    display_name = model.get('display_name', 'Unknown Model')
                    if f"[{selected_provider}]" in display_name or f"{selected_provider.lower()}" in display_name.lower():
                        # Remove provider prefix
                        display_name = display_name.replace(f"[{selected_provider}] ", "")
                        display_name = display_name.replace(f"[{selected_provider.lower()}] ", "")
                    
                    model_options.append(display_name)
                    model_mapping[display_name] = model
                    
                    # Set default index if this matches the default model
                    if (default_model and 
                        model.get('model_name') == default_model.get('model_name')):
                        default_model_index = idx
                
                selected_model_display = st.selectbox(
                    "Model",
                    options=model_options,
                    index=default_model_index,
                    help="Choose the specific model variant"
                )
                
                selected_model = model_mapping[selected_model_display]
                
                # Confirmation button
                st.markdown("---")
                if st.button("Initialize AI Agents", type="primary", use_container_width=True):
                    return selected_model
        
        return None

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
