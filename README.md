<div align="center">

# 🤖 Pareng Boyong v2

**A Filipino AI Super Agent powered by Agent Zero Framework**

[![InnovateHub](https://img.shields.io/badge/By-InnovateHub-blue?style=for-the-badge)](https://innovatehub.ph)
[![Agent Zero](https://img.shields.io/badge/Based%20on-Agent%20Zero-green?style=for-the-badge)](https://github.com/agent0ai/agent-zero)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

**Pareng Boyong** is InnovateHub's customized AI assistant built on the powerful Agent Zero framework. It combines world-class AI capabilities with Filipino-friendly personality and InnovateHub's business expertise.

[🌐 InnovateHub](https://innovatehub.ph) • [📘 Documentation](docs/) • [🚀 Quick Start](#-quick-start)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **Agent Zero Core** | Full Agent Zero capabilities with tool use, code execution, and multi-agent orchestration |
| 🇵🇭 **Filipino Personality** | Customized with Filipino-friendly greetings and personality |
| 🏢 **InnovateHub Integration** | Ready for InnovateHub business workflows |
| 🔄 **Upstream Sync** | Tracks latest Agent Zero updates for continuous improvements |
| 🐳 **Docker Ready** | Production-ready containerized deployment |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker (recommended for production)
- API keys for your preferred LLM (OpenAI, Anthropic, etc.)

### Option 1: Docker (Recommended)

```bash
# Clone this repository
git clone https://github.com/innovatehubph/pareng-boyong-v2.git
cd pareng-boyong-v2

# Create data directory
mkdir -p ~/pareng-boyong-data

# Run with Docker
docker run -d \
  --name pareng-boyong \
  --restart unless-stopped \
  -p 50001:80 \
  -v ~/pareng-boyong-data:/a0 \
  agent0ai/agent-zero:latest
```

### Option 2: Local Development

```bash
# Clone this repository
git clone https://github.com/innovatehubph/pareng-boyong-v2.git
cd pareng-boyong-v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run
python run_ui.py
```

Access the web UI at: `http://localhost:50001`

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Authentication (optional)
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=your_secure_password

# CORS (for production)
ALLOWED_ORIGINS=https://yourdomain.com
```

### Model Configuration

Edit `conf/model_providers.yaml` to configure your preferred models.

---

## 🔄 Syncing with Upstream

This repository is set up to track the official Agent Zero repository:

```bash
# Fetch latest from upstream
git fetch upstream

# Merge upstream changes
git merge upstream/main

# Push to your fork
git push origin main
```

---

## 📁 Project Structure

```
pareng-boyong-v2/
├── agent.py              # Main agent logic
├── agents/               # Sub-agent configurations
├── conf/                 # Configuration files
├── docker/               # Docker configurations
├── docs/                 # Documentation
├── instruments/          # Custom instruments/tools
├── knowledge/            # Knowledge base files
├── prompts/              # System prompts
├── python/               # Python API and helpers
├── webui/                # Web interface
└── README.md             # This file
```

---

## 🏢 About InnovateHub

[InnovateHub](https://innovatehub.ph) is a Philippine-based technology company specializing in:

- 💳 **PlataPay** - Digital payment solutions
- 🌐 **PayVerse** - Fintech platform
- 🤖 **AI Solutions** - Enterprise AI integration
- 💻 **Tech Consulting** - Digital transformation

---

## 🙏 Credits

- **[Agent Zero](https://github.com/agent0ai/agent-zero)** - The powerful AI agent framework this is built upon
- **InnovateHub Team** - Customization and deployment
- **Boss Marc** - Project lead and visionary

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

<div align="center">

**© 2026 InnovateHub Philippines. All rights reserved.**

Made with ❤️ in the Philippines 🇵🇭

</div>
