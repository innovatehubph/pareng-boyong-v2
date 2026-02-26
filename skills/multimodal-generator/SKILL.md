---
name: multimodal-generator
description: Generate AI images and videos using Replicate and OpenRouter APIs. Supports FLUX, Qwen, Gemini for images and Kling, Seedance, Wan for videos.
version: 1.0.0
author: InnovateHub
tags:
  - media
  - image-generation
  - video-generation
  - ai-art
  - replicate
  - openrouter
triggers:
  - generate image
  - create image
  - make image
  - generate video
  - create video
  - ai image
  - ai art
allowed_tools:
  - code_execution_tool
---

# Multimodal Generator

Generate AI images and videos using multiple providers.

## Capabilities

### Image Generation
- **Qwen Image** (Replicate) - Best for text rendering in images
- **Gemini 2.5 Flash** (OpenRouter) - Fast, affordable
- **Gemini 3 Pro** (OpenRouter) - Higher quality

### Video Generation
- **Kling v2.1** (Replicate) - Text-to-video & image-to-video
- **Seedance 1.5 Pro** (Replicate) - ByteDance video model
- **Wan 2.2** (Replicate) - Image-to-video fast

## Usage

### Generate Image
```python
# Using the tool
response = multimodal_generator(
    action="generate_image",
    prompt="A beautiful sunset over mountains",
    provider="qwen"  # or "gemini", "gemini_premium"
)
```

### Generate Video
```python
response = multimodal_generator(
    action="generate_video",
    prompt="Camera slowly pans across a serene lake",
    provider="kling"  # or "seedance", "wan"
)
```

### Image to Video
```python
response = multimodal_generator(
    action="image_to_video",
    image_url="https://example.com/image.jpg",
    prompt="Add gentle motion to the scene",
    provider="kling"
)
```

## Environment Variables Required
- `REPLICATE_API_TOKEN` - For Replicate models
- `OPENROUTER_API_KEY` - For OpenRouter/Gemini models

## PlataPay Branding
When generating content for PlataPay, include:
- Silver/metallic gradient aesthetic
- Professional fintech style
- "INNOVATING PAYMENTS" tagline when appropriate
