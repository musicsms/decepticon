# 📋 Decepticon Frontend 마이그레이션 가이드

## 🔄 **폴더 구조 변경사항**

### **이전 구조 → 새로운 구조**

```
❌ 이전 구조:
frontend/
├── components_refactored/
├── core_refactored/
└── utils_refactored/

✅ 새로운 구조:
frontend/
└── web/
    ├── components/
    ├── core/
    └── utils/
```

---

## 📝 **Import 경로 변경사항**

모든 import 경로가 Streamlit 네이티브 구조로 변경되었습니다:

### **Components**
```python
# ❌ 이전
from frontend.components_refactored.chat_messages import ChatMessagesComponent
from frontend.components_refactored.terminal_ui import TerminalUIComponent
from frontend.components_refactored.sidebar import SidebarComponent
from frontend.components_refactored.theme_ui import ThemeUIComponent

# ✅ 새로운
from frontend.web.components.chat_messages import ChatMessagesComponent
from frontend.web.components.terminal_ui import TerminalUIComponent
from frontend.web.components.sidebar import SidebarComponent
from frontend.web.components.theme_ui import ThemeUIComponent
```

### **Core (비즈니스 로직)**
```python
# ❌ 이전
from frontend.core_refactored.app_state import get_app_state_manager
from frontend.core_refactored.executor_manager import get_executor_manager
from frontend.core_refactored.workflow_handler import get_workflow_handler
from frontend.core_refactored.model_manager import get_model_manager

# ✅ 새로운
from frontend.web.core.app_state import get_app_state_manager
from frontend.web.core.executor_manager import get_executor_manager
from frontend.web.core.workflow_handler import get_workflow_handler
from frontend.web.core.model_manager import get_model_manager
```

### **Utils (유틸리티)**
```python
# ❌ 이전
from frontend.utils_refactored.constants import ICON, ICON_TEXT, COMPANY_LINK
from frontend.utils_refactored.validation import check_model_required

# ✅ 새로운
from frontend.web.utils.constants import ICON, ICON_TEXT, COMPANY_LINK
from frontend.web.utils.validation import check_model_required
```

---

## 🔧 **파일명 변경사항**

### **메인 앱 파일**
```
❌ 이전: streamlit_app_refactored.py
✅ 새로운: streamlit_app.py
```

---

## 🏗️ **새로운 아키텍처 사용법**

### **1. 새로운 페이지 개발**

```python
# pages/new_page.py
import streamlit as st

# 새로운 import 경로 사용
from frontend.web.components.theme_ui import ThemeUIComponent
from frontend.web.core.app_state import get_app_state_manager
from frontend.web.utils.constants import ICON, ICON_TEXT

def main():
    # 컴포넌트 초기화
    theme_ui = ThemeUIComponent()
    app_state = get_app_state_manager()
    
    # 테마 적용
    current_theme = \"dark\" if st.session_state.get('dark_mode', True) else \"light\"
    theme_ui.apply_theme_css(current_theme)
    
    # Streamlit 네이티브 직접 사용
    st.logo(ICON_TEXT, icon_image=ICON, size=\"large\")
    st.title(\"새로운 페이지\")

if __name__ == \"__main__\":
    main()
```

### **2. 기존 코드 마이그레이션**

**단계별 마이그레이션:**

1. **Import 경로 수정**
   ```python
   # 모든 import 문에서 경로 변경
   # components_refactored → web.components
   # core_refactored → web.core  
   # utils_refactored → web.utils
   ```

2. **코드 동작 확인**
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

3. **기능 테스트**
   - 모델 선택 기능
   - 채팅 기능
   - 터미널 UI
   - 히스토리 기능

---

## 🧪 **테스트 가이드**

### **기본 기능 테스트**

1. **모델 선택 테스트**
   ```bash
   streamlit run frontend/streamlit_app.py
   ```
   - 모델 목록 로드 확인
   - 모델 선택 및 초기화 확인
   - 스피너가 올바른 위치에 표시되는지 확인

2. **채팅 기능 테스트**
   ```bash
   streamlit run frontend/pages/01_Chat.py
   ```
   - 메시지 입력 및 응답 확인
   - 터미널 UI 정상 표시 확인 (남색 UI 없이)
   - 에이전트 상태 표시 확인

3. **히스토리 기능 테스트**
   ```bash
   streamlit run frontend/pages/02_📋_Chat_History.py
   ```
   - 세션 목록 로드 확인
   - Replay 버튼 정상 동작 확인 (오류 없이)

---

## ⚠️ **주의사항**

### **1. 캐시 초기화**
```bash
# Streamlit 캐시 초기화 (권장)
streamlit cache clear
```

### **2. 의존성 확인**
기존 코드에서 다음 경로를 사용하고 있다면 수정이 필요합니다:
- `frontend.components_refactored.*`
- `frontend.core_refactored.*`
- `frontend.utils_refactored.*`

### **3. IDE 설정 업데이트**
IDE에서 import 자동완성이 올바르게 동작하도록 프로젝트 루트 경로를 확인하세요.

---

## 🔍 **트러블슈팅**

### **문제 1: Import Error**
```
ImportError: No module named 'frontend.components_refactored'
```
**해결**: Import 경로를 새로운 구조로 변경
```python
# ❌ 잘못된 import
from frontend.components_refactored.xxx import xxx

# ✅ 올바른 import  
from frontend.web.components.xxx import xxx
```

### **문제 2: 모듈을 찾을 수 없음**
```
ModuleNotFoundError: No module named 'frontend.web'
```
**해결**: 프로젝트 루트에서 실행하고 있는지 확인
```bash
cd /path/to/Decepticon
streamlit run frontend/streamlit_app.py
```

### **문제 3: 터미널 UI 오류**
```
'TerminalUIComponent' object has no attribute 'clear_terminal'
```
**해결**: 이미 수정됨. 최신 코드 사용 확인

---

## 📚 **참고 자료**

- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [Streamlit 앱 구조 가이드](https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps)
- [Python 패키지 구조 베스트 프랙티스](https://docs.python.org/3/tutorial/modules.html)

---

## ✅ **마이그레이션 체크리스트**

- [ ] Import 경로 모두 변경됨
- [ ] 기본 페이지 로드 정상 동작
- [ ] 모델 선택 기능 정상 동작
- [ ] 채팅 기능 정상 동작
- [ ] 터미널 UI 정상 표시 (남색 UI 없음)
- [ ] Replay 기능 정상 동작 (오류 없음)
- [ ] 모든 기존 기능 정상 동작

---

## 🎯 **완료 후 혜택**

이 마이그레이션을 완료하면:
- ✅ **Streamlit 표준 구조** 준수
- ✅ **더 나은 코드 구조**
- ✅ **향상된 유지보수성**
- ✅ **쉬운 확장성**
- ✅ **표준 개발 관행** 준수

새로운 구조에서 더욱 효율적인 개발을 진행하세요! 🚀
