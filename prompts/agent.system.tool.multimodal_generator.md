### multimodal_generator:
**CREATE IMAGES, VIDEOS, AND AUDIO** - All-in-one multimodal content generator.
Use this tool to analyze images, generate images from text, create videos, and add audio.

**Actions:**
- `analyze_image` - Analyze/describe an image (Gemini)
- `generate_image` - Create image from text (FLUX 2 Pro)
- `edit_image` - Edit/transform image (Gemini 3 Pro / Nano Banana)
- `vary_image` - Create variations (FLUX Redux)
- `generate_video` - Create video from text (Seedance/Kling/Wan)
- `add_audio` - Add audio/sound to video (MMAudio)
- `models` - List available models

---

## ⚠️ CRITICAL: PlataPay Content Workflow

**AI models CANNOT perfectly reproduce:**
- Specific logos (PlataPay, InnovateHub, etc.)
- Text/captions in Filipino
- App screens that look realistic

### FOR PLATAPAY VIDEO ADS - Use `platapay_video_ads` tool!

For PlataPay marketing videos, use the dedicated `platapay_video_ads` tool instead.
It generates clean footage and uses Remotion for perfect branding.

### FOR PLATAPAY IMAGES - Two-Step Workflow:

**Step 1:** Generate background with `multimodal_generator`
~~~json
{
    "thoughts": ["Need marketing image with PlataPay logo - generating background first"],
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "generate_image",
        "prompt": "Professional fintech marketing banner, modern gradient, Filipino colors, clean area in top-left for logo placement, NO TEXT, NO LOGOS, 16:9"
    }
}
~~~

**Step 2:** Overlay REAL logo with `image_compositor`
~~~json
{
    "thoughts": ["Now adding the real PlataPay logo"],
    "tool_name": "image_compositor",
    "tool_args": {
        "action": "overlay",
        "base_image": "<URL_from_step_1>",
        "overlay_image": "/a0/tmp/platapay_logo.png",
        "position": "top-left"
    }
}
~~~

---

## ⚠️ CLEAN VIDEO PROMPTS (When using this tool for video)

When generating videos that will have branding added later, ALWAYS include in prompt:
- "NO text overlays"
- "NO logos or brand marks"
- "NO visible phone/tablet screens"
- "Clean footage only"

Example clean prompt:
```
Happy Filipino entrepreneur in sari-sari store, celebrating success.
NO text overlays, NO logos, NO visible device screens.
Clean footage only - text will be added in post-production.
Warm lighting, natural movements, 5 seconds.
```

---

### Analyze an image:
~~~json
{
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "analyze_image",
        "image_url": "https://example.com/photo.jpg",
        "prompt": "Describe this image in detail"
    }
}
~~~

### Generate an image (NO brand logos):
~~~json
{
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "generate_image",
        "prompt": "A futuristic cityscape at sunset with flying cars",
        "aspect_ratio": "16:9"
    }
}
~~~

### Generate CLEAN video (for later branding):
~~~json
{
    "thoughts": ["Generating clean footage - branding will be added with Remotion"],
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "generate_video",
        "prompt": "Happy Filipino person smiling warmly. NO text, NO logos, NO device screens. Clean footage only.",
        "quality": "premium"
    }
}
~~~

Then use `remotion_branding` to add logo/text.

### Add audio to video:
~~~json
{
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "add_audio",
        "video_url": "https://example.com/video.mp4",
        "prompt": "upbeat music, positive mood"
    }
}
~~~

---

**Quality Levels for Video:**
- `normal` - Wan 2.2 (fast)
- `premium` - Seedance 1.5 Pro (best)
- `premium_alt` - Kling v2.5 Turbo Pro

**Aspect Ratios:** `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`

**Logo Files:**
- **PlataPay:** `/a0/tmp/platapay_logo.png`

---

## Tool Routing for PlataPay:

| Content Type | Tool |
|-------------|------|
| PlataPay **video** ad | `platapay_video_ads` |
| PlataPay **image** ad | `empire_ad_generator` |
| Add branding to video | `remotion_branding` |
| Add logo to image | `image_compositor` |
| General image (no brand) | `multimodal_generator` |
| General video (no brand) | `multimodal_generator` |
