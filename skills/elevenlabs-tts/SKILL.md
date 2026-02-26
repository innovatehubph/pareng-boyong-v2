---
name: elevenlabs-tts
description: High-quality text-to-speech using ElevenLabs API. Convert text to natural-sounding voice audio.
version: 1.0.0
author: InnovateHub
tags:
  - audio
  - tts
  - voice
  - elevenlabs
  - speech
triggers:
  - text to speech
  - generate voice
  - speak this
  - voice over
  - tts
allowed_tools:
  - code_execution_tool
---

# ElevenLabs TTS

High-quality text-to-speech synthesis.

## Available Voices

| Name | Voice ID | Description |
|------|----------|-------------|
| Sarah | EXAVITQu4vr4xnSDxMaL | Mature, Confident female |
| Laura | FGY2WhTYpPnrIDTdsKH5 | Enthusiast, Quirky |
| Roger | CwhRBWXzGAHq8TQ4Fs17 | Laid-Back, Casual male |
| Charlie | IKne3meq5aSn9XLyUdCD | Deep, Confident male |

## Usage

```python
response = elevenlabs_tts(
    text="Hello, welcome to InnovateHub!",
    voice="sarah",  # or voice_id
    model="eleven_multilingual_v2"
)
```

## Environment Variables
- `ELEVENLABS_API_KEY` - Your ElevenLabs API key
