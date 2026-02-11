# Image Generation Workflow Guide

## 🎯 Decision Matrix: Which Tool to Use

### When User Wants to CREATE a Marketing Image with a SPECIFIC LOGO:

**ALWAYS use this two-step workflow:**

1. **Step 1 - Generate Background:** Use `multimodal_generator action=generate_image`
   - Create the background/banner WITHOUT the logo
   - In the prompt, mention "leave space for logo in [position]"
   
2. **Step 2 - Add Real Logo:** Use `image_compositor action=overlay`
   - Overlay the ACTUAL logo file onto the generated background
   - This ensures 100% accurate logo reproduction

**Example workflow for PlataPay marketing image:**
```
# Step 1: Generate background
multimodal_generator action=generate_image prompt="Professional fintech marketing banner for digital payments, vibrant Filipino colors, modern gradient background, space for logo in top-left corner, 16:9 aspect ratio" aspect_ratio=16:9

# Step 2: Download the generated image and overlay real logo
image_compositor action=overlay base_image=<generated_image_url> overlay_image=/a0/tmp/platapay_logo.png position=top-left scale=0.15 padding=30
```

---

## ⚠️ CRITICAL: AI Models CANNOT Preserve Exact Logos

**DO NOT** try to make AI models reproduce specific logos like PlataPay, InnovateHub, etc.
- FLUX 2 Pro: Will generate a FAKE logo based on text description
- Gemini 3 Pro: Will APPROXIMATE the logo but alter details
- FLUX Redux: Will create VARIATIONS that change the logo

**The ONLY way to get the exact logo** is programmatic compositing via `image_compositor`.

---

## Tool Selection Guide

| User Request | Tool to Use | Why |
|--------------|-------------|-----|
| "Create image with PlataPay logo" | `multimodal_generator` + `image_compositor` | Need exact logo |
| "Generate a banner with our logo" | `multimodal_generator` + `image_compositor` | Need exact logo |
| "Put the real logo on this image" | `image_compositor` only | Just compositing |
| "Create an artistic image" (no logo) | `multimodal_generator` | Pure generation |
| "Transform this image style" | `multimodal_generator action=edit_image` | Style change |
| "Create variations of this design" | `multimodal_generator action=vary_image` | Variations |
| "Resize this logo" | `image_compositor action=resize` | Simple resize |
| "Overlay logo on banner" | `image_compositor action=overlay` | Compositing |

---

## Logo Files Reference

### PlataPay
- **Local path:** `/a0/tmp/platapay_logo.png`
- **URL:** `https://platapay.ph/lovable-uploads/2ea0f2a8-30d6-4dc7-a90c-64114f4b68d7.png`
- **Download command:** `wget -O /a0/tmp/platapay_logo.png "https://platapay.ph/lovable-uploads/2ea0f2a8-30d6-4dc7-a90c-64114f4b68d7.png"`

### InnovateHub
- **URL:** Check `https://innovatehub.ph` for latest logo

---

## image_compositor Parameters

```
image_compositor action=overlay
  base_image=<path_or_url>     # Background image
  overlay_image=<path_or_url>  # Logo/image to overlay
  position=top-left            # top-left, top-right, bottom-left, bottom-right, center
  scale=0.15                   # Size relative to base (0.1 to 1.0)
  padding=30                   # Pixels from edge
  opacity=1.0                  # Transparency (0.0 to 1.0)
```

---

## Quick Decision Flow

```
User wants image with specific brand logo?
  │
  ├─► YES → Use TWO-STEP WORKFLOW:
  │         1. multimodal_generator (generate background)
  │         2. image_compositor (add real logo)
  │
  └─► NO → Use multimodal_generator directly
```

**Remember:** When in doubt about logos, ALWAYS use image_compositor for the final logo placement!
