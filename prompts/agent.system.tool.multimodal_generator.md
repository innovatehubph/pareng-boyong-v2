### multimodal_generator:
**CREATE IMAGES, VIDEOS, AND AUDIO** - All-in-one multimodal content generator.
Use this tool to analyze images, generate images from text, create videos, and add audio.

**Actions:**
- `analyze_image` - Analyze/describe an image (Gemini)
- `generate_image` - Create image from text (FLUX 2 Pro)
- `generate_video` - Create video from text (Seedance/Kling/Wan)
- `add_audio` - Add audio/sound to video (MMAudio)
- `models` - List available models

---

### Analyze an image:
~~~json
{
    "thoughts": ["User wants to know what's in this image"],
    "headline": "Analyzing image content",
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "analyze_image",
        "image_url": "https://example.com/photo.jpg",
        "prompt": "Describe this image in detail"
    }
}
~~~

### Generate an image:
~~~json
{
    "thoughts": ["Creating an image from the user's description"],
    "headline": "Generating image with FLUX 2 Pro",
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "generate_image",
        "prompt": "A futuristic cityscape at sunset with flying cars and neon lights, cyberpunk style, highly detailed",
        "aspect_ratio": "16:9"
    }
}
~~~

### Generate a video (normal quality - fast):
~~~json
{
    "thoughts": ["User wants a quick video, using normal quality"],
    "headline": "Generating video with Wan 2.2",
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "generate_video",
        "prompt": "A sports car driving along a beach at sunset, golden hour lighting",
        "quality": "normal"
    }
}
~~~

### Generate a video (premium quality):
~~~json
{
    "thoughts": ["User wants high quality video, using Seedance"],
    "headline": "Generating premium video",
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "generate_video",
        "prompt": "A young astronaut in a spacecraft cockpit, cinematic lighting, sci-fi atmosphere",
        "quality": "premium"
    }
}
~~~

### Generate video from image (image-to-video):
~~~json
{
    "thoughts": ["User has an image they want animated"],
    "headline": "Creating video from image",
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "generate_video",
        "prompt": "The person starts walking forward slowly",
        "image_url": "https://example.com/photo.jpg",
        "quality": "premium"
    }
}
~~~

### Add audio to video:
~~~json
{
    "thoughts": ["User wants to add sound effects to their video"],
    "headline": "Adding audio to video",
    "tool_name": "multimodal_generator",
    "tool_args": {
        "action": "add_audio",
        "video_url": "https://example.com/video.mp4",
        "prompt": "ocean waves, seagulls, beach ambience"
    }
}
~~~

---

**Quality Levels for Video:**
- `normal` - Wan 2.2 (fast, good for drafts)
- `premium` - Seedance 1.5 Pro (best quality)
- `premium_alt` - Kling v2.5 Turbo Pro (alternative premium)

**Aspect Ratios for Images:**
- `1:1` (square)
- `16:9` (landscape)
- `9:16` (portrait/vertical)
- `4:3`, `3:4`, `21:9`, etc.
