[![English](https://img.shields.io/badge/Language-English-blue?style=for-the-badge)](README.md)
[![한국어](https://img.shields.io/badge/Language-한국어-red?style=for-the-badge)](./docs/README_KO.md)

<h1 align="center"> Decepticon : Vibe Hacking Agent</h1>

<div align="center">
  <!-- GitHub License -->
  <a href="https://github.com/PurpleAILAB/Decepticon/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/PurpleAILAB/Decepticon?style=for-the-badge&color=blue" alt="License: Apache 2.0">
  </a>

  <!-- GitHub Stars -->
  <a href="https://github.com/PurpleAILAB/Decepticon/stargazers">
    <img src="https://img.shields.io/github/stars/PurpleAILAB/Decepticon?style=for-the-badge&color=yellow" alt="Stargazers">
  </a>

  <!-- GitHub Contributors -->
  <a href="https://github.com/PurpleAILAB/Decepticon/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/PurpleAILAB/Decepticon?style=for-the-badge&color=orange" alt="Contributors">
  </a>

  <br/>

  <!-- Discord -->
  <a href="https://discord.gg/XGytzHZU">
    <img src="https://img.shields.io/badge/Discord-Join%20Us-7289DA?logo=discord&logoColor=white&style=for-the-badge" alt="Join us on Discord">
  </a>

  <!-- Website -->
  <a href="https://purplelab.framer.ai">
    <img src="https://img.shields.io/badge/Visit%20Website-brightgreen?logo=vercel&logoColor=white&style=for-the-badge" alt="Visit Website">
  </a>



</div>

<div align="center">

| | Preview | Full |
|---|---------|------|
| **Web** | ![web](.github/web.gif) | [Full Demo](https://github.com/user-attachments/assets/a5286b0f-9b54-4e00-942d-ad3f8a1e7a5d) |
| **CLI** | ![cli](.github/cli.gif) | [Full Demo](https://github.com/user-attachments/assets/29d005ac-89c7-4d45-b11c-e0e7b2ddf094) |

</div>

---

<details>
<summary><strong>📚 Table of Contents</strong></summary>

- [💡 What is Vibe Hacking ?](#-what-is-vibe-hacking-)
- [💡 Why Decepticon?](#-why-decepticon)
- [🚀 Quick Start](#-quick-start)
- [🤖 Agents](#-agents)
  - [🔴 Red Team Agents](#-red-team-agents)
  - [🔵 Utility Agents](#-utility-agents)
- [🏛️ Multi-Architecture](#️-multi-architecture)
- [🔧 Installation](#-installation)
- [🧠 Advanced AI Models](#-advanced-ai-models)
  - [☁️ Cloud Models](#️-cloud-models)
  - [🏠 Local Models (Ollama)](#-local-models-ollama)
- [🔧 MCP Support](#-mcp-support)
  - [✅ Supported MCP Transports](#-supported-mcp-transports)
  - [📁 `mcp_config.json` Structure](#-mcp_configjson-structure)
  - [📌 Example](#-example)
- [⚠️ Experimental Technology Disclaimer](#️-experimental-technology-disclaimer)
- [🤝 Contributing](#-contributing)
  - [🔧 What You Can Contribute](#-what-you-can-contribute)
    - [🛠 Migrate Security Tools to MCP Format](#-migrate-security-tools-to-mcp-format)
    - [🧠 Develop ReAct-style Red Team Agents](#-develop-react-style-red-team-agents)
    - [🕸 Architect Multi-Agent Flows](#-architect-multi-agent-flows)
  - [🚀 How to Contribute](#-how-to-contribute)
  - [🌟 Join the Community](#-join-the-community)
- [📝 License](#-license)

</details>

---

## 💡 What is **Vibe Hacking** ?

**Vibe Hacking** is a new paradigm in Offensive Security defined by PurpleAILAB.  

Unlike traditional red teaming methods that rely on manual execution, **AI agents autonomously perform red teaming tasks** in Vibe Hacking.

> ### *The Best Defense is a Good Offense.*

## 💡 Why **Decepticon**?

As agents become more sophisticated, attackers evolve accordingly.  
From AI-driven phishing to self-learning malware, offensive techniques are becoming increasingly automated and intelligent.

To effectively defend against AI-powered threats, **we must act faster**—and **we must act first**.  
**Decepticon** is designed for that very purpose: using AI agents to automate red teaming **before attackers automate theirs.**

Built on the robust foundation of **LangChain/LangGraph**, Decepticon grows alongside the thriving AI agent ecosystem. By leveraging the same cutting-edge frameworks that power the future of AI, we ensure compatibility, scalability, and continuous innovation through community collaboration.

Delegate repetitive and manual tasks to agents, and focus on intuition and decision-making to fulfill the true essence of a **CyberSecurity Supervisor**.

> ### *Prepare before AI Hacks First.*

---

## Quick Start

### 1. Set up the environment with
```bash
uv venv
uv pip install -e .
```

### 2. Copy environment file 
```bash
cp .env.example .env
```

### 3. Docker
```bash
docker-compose up -d
```

### 4. Run MCP servers
#### Option 1: Use provided scripts
- On Windows:
```bash
./run_mcp.ps1
```
- On macOS/Linux:
```bash
./run_mcp.sh
```

#### Option 2: Run manually
```bash
python src/tools/mcp/Inital_Access.py
python src/tools/mcp/Recoonaissance.py
```

### 4. Run CLI or Web interface
```bash
python cli.py
streamlit run app.py
```

---

## Agents

#### 🔴 Red Team Agents
- **Reconnaissance Agent**: Network scanning, service enumeration, vulnerability discovery
- **Initial Access Agent**: Exploitation, credential attacks, system compromise
- **Privilege Escalation Agent**(Planned): Rights elevation and lateral movement
- **Defense Evasion Agent**(Planned): Anti-detection and stealth techniques
- **Persistence Agent**(Planned): Maintaining access and backdoor installation
- **Execution Agent**(Planned): Command execution and payload deployment

#### 🔵 Utility Agents 
- **Planner Agent**: Strategic brain coordinating the entire operation
- **Summary Agent**: Analysis compilation, reporting, and documentation
- **Supervisor Agent**(Planned): Workflow orchestration and decision routing

---

## Multi-Architecture

**Flexible Architecture Options:**
- **Swarm Architecture**: Direct peer-to-peer agent communication and collaboration
- **Supervisor Architecture**(Planned): Centralized control with supervisor-managed workflows
- **Hybrid Architecture**(Planned): Combined approach with both direct communication and centralized oversight
- **your custom Architecture**

---

## Installation

### 1. **Clone the repository**
```bash
git clone https://github.com/PurpleCHOIms/Decepticon.git
cd Decepticon
```

### 2. **Install dependencies** 
**UV (Recommended)**
```bash
# Create virtual environment
uv venv
# Install dependencies
uv pip install -e .
```

### 3. environment file .env

```bash
# Create environment file
cp .env.example .env
```

```bash
# Configure API Keys

# LLM API
OPENAI_API_KEY=your-api-key
ANTHROPIC_API_KEY=your-api-key
OPENROUTER_API_KEY=your-api-key

# Langsmith
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=your-api-key
LANGSMITH_PROJECT=Decepticon
LANGGRAPH_API_URL=http://127.0.0.1:2024
```

### 4. Docker Setup

```bash
# Start Kali Linux container with target
docker-compose up -d
```

### 5. Start MCP Server
```bash
python src/tools/mcp/Inital_Access.py
python src/tools/mcp/Recoonaissance.py
```

### 6. CLI 
```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run CLI
python cli.py
```

### 7. Web Interface

```bash
# Run web interface
streamlit run app.py
```
**Access the interface at:** http://localhost:8501

---

## Advanced AI Models

Support for **15+ AI providers** and **30+ models**:

### ☁️ Cloud Models
- **OpenAI**: GPT-4o, GPT-4o Mini, O1 Preview, O1 Mini
- **Anthropic**: Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3.7 Sonnet
- **Google**: Gemini 2.0 Flash, Gemini 2.5 Pro  
- **Groq**: Ultra-fast Llama 4 models (Scout, Maverick)
- **Mistral**: Mistral Large, Mistral Small
- **xAI**: Grok Beta
- **Perplexity**: Sonar models with web search

### 🏠 Local Models (Ollama)
- **Meta**: Llama 3.3 70B, Llama 3.1 models
- **DeepSeek**: DeepSeek-R1 variants  
- **Google**: Gemma 3 models (4B, 12B, 27B)
- **Alibaba**: Qwen 3 models
- **Mistral**: Mistral Small 3.1 (24B)

---

## MCP Support

This project supports loading tools via the [LangGraph MCP Adapter](https://github.com/langchain-ai/langchain-mcp-adapters).

You can define your MCP tools in a configuration file called `mcp_config.json`.  
Tools are grouped by **agent names**, and each agent can have multiple MCP servers.

### Supported MCP Transports

- `stdio` - Standard input/output communication
- `streamable_http` - HTTP-based streaming communication

### `mcp_config.json` Structure

```json
{
  "agent_name": {
    "mcp_server_1": {
      "command": "python",
      "args": ["./path/to/script.py"],
      "transport": "stdio"
    },
    "another_mcp_server_streamable_HTTP": {
      "url": "https://your-cloud-function/mcp?api_key=your-api-key"
    }
  }
}
```

### Example

```json
{
  "reconnaissance": {
    "reconnaissance": {
      "command": "python",
      "args": ["./src/tools/mcp/Reconnaissance.py"],
      "transport": "stdio"
    },
    "desktop_commander": {
      "url": "https://server.smithery.ai/@wonderwhy-er/desktop-commander/mcp?api_key=your-api-key"
    }
  },
  "initial_access": {
    "initial_access": {
      "command": "python",
      "args": ["./src/tools/mcp/Initial_Access.py"],
      "transport": "stdio"
    }
  }
}
```

**To add a new MCP tool:**
1. Create your MCP tool script under `src/tools/mcp/`
2. Add the corresponding entry in `mcp_config.json`
3. Restart the application to load the new tool

---

## ⚠️ Experimental Technology Disclaimer

**Decepticon** is an experimental project currently under active development. It is not yet stable and may contain bugs, incomplete features, or undergo breaking changes.

We're building this project openly with the community and warmly welcome:

- Bug reports  
- Feature requests  
- Pull requests  
- Good vibes  

Help us make Decepticon better by filing issues or submitting PRs (see the section below for how to contribute)!

---

## 🤝 Contributing

We welcome contributions from the community to make this project better, more powerful, and more secure.  
Whether you're an experienced developer, a security researcher, or just getting started in open-source, there are many ways to get involved.

### What You Can Contribute

#### Migrate Security Tools to MCP Format

Help transform existing security tools into modular, LangGraph-compatible **MCP (Modular Command Protocol) tools**.

- Wrap tools using the standard MCP interface (`stdio` or `streamable_http`)
- Ensure compatibility with `langgraph-mcp-adapter`
- Place them under the `src/tools/mcp/`

#### Develop ReAct-style Red Team Agents

Design and refine ReAct-style agents for Red Team operations:

- Reconnaissance  
- Initial Access  
- Privilege Escalation  
- Persistence and more

Contribute by:

- Creating tailored prompts under `src/prompts/`
- Implementing new agents with specific capabilities
- Improving task planning and memory usage

#### Architect Multi-Agent Flows

Contribute to the design and optimization of the multi-agent orchestration layer:

- Propose new workflows or agent roles
- Improve inter-agent communication and handoffs
- Extend state-driven logic using LangGraph

### How to Contribute

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes with clear messages
4. Push to your branch and open a **Pull Request**
5. Link the related issue (if any) and explain your solution

We encourage clean, well-tested code with documentation.  
Feel free to open issues to discuss ideas before jumping into a PR!

### Join the Community

Join our [Discord server](https://discord.gg/XGytzHZU) to connect with other developers, share ideas, ask questions, and collaborate on building the future of AI-powered red teaming!

Whether you're looking for help with contributions, want to discuss new features, or just want to chat about cybersecurity and AI, our community is here to support you.

---

## 📝 License

This repository is licensed under the [Apache-2.0 License](LICENSE).

---

![main](./assets/main.png)