<div align="center">
  <img src="assets/cli.png" alt="Decepticon CLI">
</div>

<h1 align="center">Decepticon</h1>

<p align="center">AI-powered autonomous red team framework.</p>

<div align="center">

<a href="https://github.com/PurpleAILAB/Decepticon/blob/main/LICENSE">
  <img src="https://img.shields.io/github/license/PurpleAILAB/Decepticon?style=for-the-badge&color=blue" alt="License: Apache 2.0">
</a>
<a href="https://github.com/PurpleAILAB/Decepticon/stargazers">
  <img src="https://img.shields.io/github/stars/PurpleAILAB/Decepticon?style=for-the-badge&color=yellow" alt="Stargazers">
</a>
<a href="https://discord.gg/TZUYsZgrRG">
  <img src="https://img.shields.io/badge/Discord-Join%20Us-7289DA?logo=discord&logoColor=white&style=for-the-badge" alt="Join us on Discord">
</a>
<a href="https://purpleailab.mintlify.app">
  <img src="https://img.shields.io/badge/Docs-purpleailab.mintlify.app-8B5CF6?logo=bookstack&logoColor=white&style=for-the-badge" alt="Documentation">
</a>

</div>

---

> **Warning**: Do not use this project on any system or network without explicit authorization.

> **Note**: Decepticon 2.0 is currently under active development. For full documentation, architecture details, and philosophy, visit **[purpleailab.mintlify.app](https://purpleailab.mintlify.app)**.

---

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose

### Install

```bash
git clone -b refactor https://github.com/PurpleAILAB/Decepticon.git
cd Decepticon

uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

cp .env.example .env
# Edit .env — add your API keys
```

### Run

```bash
docker compose up -d --build
decepticon
```

## License

[Apache-2.0](LICENSE)
