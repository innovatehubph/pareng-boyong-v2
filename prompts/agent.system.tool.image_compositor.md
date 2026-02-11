### image_compositor:
**OVERLAY REAL LOGOS AND IMAGES** - Programmatic image compositing tool.
Use this tool to place EXACT logos, watermarks, or images onto other images.

**This is the ONLY tool that preserves logos exactly as they are.**
AI image generators (FLUX, Gemini) will create fake/approximated logos.

**Actions:**
- `overlay` - Place one image on top of another (logo on banner)
- `resize` - Resize an image
- `info` - Get image dimensions

---

### Overlay a logo on a banner:
~~~json
{
    "thoughts": ["User wants to add the real PlataPay logo to an image"],
    "headline": "Overlaying PlataPay logo on image",
    "tool_name": "image_compositor",
    "tool_args": {
        "action": "overlay",
        "base_image": "https://example.com/banner.png",
        "overlay_image": "/a0/tmp/platapay_logo.png",
        "position": "top-left",
        "scale": "0.15",
        "padding": "30"
    }
}
~~~

### Position options:
- `top-left` - Logo in top-left corner (most common for branding)
- `top-right` - Logo in top-right corner
- `bottom-left` - Logo in bottom-left corner
- `bottom-right` - Logo in bottom-right corner (common for watermarks)
- `center` - Logo centered in the image
- `top-center` - Logo centered at top
- `bottom-center` - Logo centered at bottom

### Parameters:
- `base_image` - Background image (URL or local path)
- `overlay_image` - Image to overlay (logo, watermark)
- `position` - Where to place overlay
- `scale` - Size relative to base (0.1 = 10%, 0.2 = 20%, etc.)
- `padding` - Pixels from edge (default: 20)
- `opacity` - Transparency (0.0 to 1.0, default: 1.0)

### Resize an image:
~~~json
{
    "thoughts": ["User wants to resize the logo"],
    "headline": "Resizing image",
    "tool_name": "image_compositor",
    "tool_args": {
        "action": "resize",
        "image": "/a0/tmp/logo.png",
        "width": "500"
    }
}
~~~

### Get image info:
~~~json
{
    "thoughts": ["Checking image dimensions"],
    "headline": "Getting image info",
    "tool_name": "image_compositor",
    "tool_args": {
        "action": "info",
        "image": "/a0/tmp/banner.png"
    }
}
~~~

---

### Logo Files Reference:
| Brand | Local Path |
|-------|------------|
| PlataPay | `/a0/tmp/platapay_logo.png` |

### Download logos if needed:
~~~bash
wget -O /a0/tmp/platapay_logo.png "https://platapay.ph/lovable-uploads/2ea0f2a8-30d6-4dc7-a90c-64114f4b68d7.png"
~~~

---

## When to use image_compositor vs multimodal_generator:

| Task | Tool |
|------|------|
| Create new image from text | `multimodal_generator` |
| Add REAL logo to image | `image_compositor` ✓ |
| Edit image style | `multimodal_generator` |
| Overlay watermark | `image_compositor` ✓ |
| Create image variations | `multimodal_generator` |
| Precise logo placement | `image_compositor` ✓ |
