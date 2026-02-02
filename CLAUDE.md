# CLAUDE.md - AI Assistant Guide for Pareng Boyong

This file provides guidance for AI assistants working with the Pareng Boyong codebase.

## Project Overview

**Pareng Boyong v2** is InnovateHub's customized AI assistant built on the Agent Zero framework.

- **Repository**: innovatehubph/pareng-boyong-v2
- **Upstream**: agent0ai/agent-zero
- **Owner**: InnovateHub Philippines / Boss Marc

## Key Customizations

### Branding Changes

| File | Customization |
|------|---------------|
| `webui/index.html` | Title: "Pareng Boyong - InnovateHub AI" |
| `webui/login.html` | Login page branding |
| `webui/components/welcome/` | Welcome screen with Pareng Boyong name |
| `prompts/fw.initial_message.md` | Filipino greeting message |
| `webui/public/innovatehub-logo.png` | InnovateHub logo |

### Personality

Pareng Boyong uses Filipino-friendly greetings like "Kumusta!" and identifies as a Filipino AI assistant.

## Development Workflow

### Syncing with Upstream

```bash
git fetch upstream
git merge upstream/main
# Resolve any conflicts, keeping our branding
git push origin main
```

### Testing Changes

```bash
# Local development
python run_ui.py

# Or with Docker
docker-compose up
```

## Architecture

Pareng Boyong inherits all capabilities from Agent Zero:

- **Multi-agent orchestration** - Creates sub-agents for complex tasks
- **Tool use** - Code execution, web browsing, file operations
- **Memory** - Persistent conversation memory
- **Knowledge** - RAG-based knowledge retrieval

## File Structure Highlights

```
├── agent.py           # Core agent logic (don't modify unless necessary)
├── prompts/           # System prompts (customize personality here)
├── webui/             # Web interface (branding changes)
├── python/api/        # API endpoints
└── conf/              # Model and provider configuration
```

## Deployment

### Production (Docker)

```bash
docker run -d \
  --name pareng-boyong \
  -p 50001:80 \
  -v /path/to/data:/a0 \
  agent0ai/agent-zero:latest
```

### Environment Variables

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` - LLM API keys
- `BASIC_AUTH_USERNAME` / `BASIC_AUTH_PASSWORD` - Optional auth
- `ALLOWED_ORIGINS` - CORS whitelist

## Contact

- **Company**: InnovateHub Philippines
- **Website**: https://innovatehub.ph
- **Project Lead**: Boss Marc
