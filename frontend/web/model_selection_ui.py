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
        """Load model data with optimizations - returns status dict instead of displaying messages"""
        try:
            from src.utils.llm.models import list_available_models, check_ollama_connection
            import concurrent.futures
            
            # 병렬 처리로 모델 목록과 Ollama 연결 동시 체크
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # 타임아웃을 짧게 설정하여 빠른 응답
                model_future = executor.submit(list_available_models)
                ollama_future = executor.submit(check_ollama_connection)
                
                try:
                    # 최대 5초 대기 (기존보다 단축)
                    models = model_future.result(timeout=5.0)
                    ollama_info = ollama_future.result(timeout=2.0)  # Ollama는 더 짧게
                except concurrent.futures.TimeoutError:
                    # 타임아웃 시 기본값 사용
                    models = model_future.result() if model_future.done() else []
                    ollama_info = ollama_future.result() if ollama_future.done() else {"connected": False, "count": 0}
            
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
        """Simple dropdown-based model selection UI - 헤더 제거, 부모 컴포넌트에서 레이아웃 처리"""
        # 개선된 캐싱: 모델 데이터 로드 (첫 번째만 또는 캐시 만료시)
        cache_key = "models_cache_timestamp"
        cache_duration = 300  # 5분 캐시
        current_time = time.time()
        
        # 캐시 체크: 모델 데이터가 없거나 캐시가 만료된 경우
        needs_refresh = (
            not st.session_state.models_by_provider or 
            current_time - st.session_state.get(cache_key, 0) > cache_duration
        )
        
        if needs_refresh:
            with st.spinner("Loading available models..."):
                load_result = self.load_models_data()
                st.session_state[cache_key] = current_time  # 캐시 시간 업데이트
            
            # Display messages
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
        
        # 모델 선택 헤더 (유지) - 컴팩트하게
        st.markdown("### Select AI Model")
        st.markdown("Choose the AI model for your red team operations")
        
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
                
                # Confirmation button - 간결하게
                if st.button("Initialize AI Agents", type="primary", use_container_width=True):
                    return selected_model
            else:
                st.warning(f"No models available for {selected_provider_display}")
        else:
            st.warning("Please select a valid provider")
        
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
        """Reset model selection state including cache"""
        # 캐시 포함 전체 리셋
        reset_keys = ["models_by_provider", "models_cache_timestamp"]
        
        for key in reset_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        # 기본 상태로 초기화
        st.session_state.models_by_provider = {}
