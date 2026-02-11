# platapay_video_ads

## ⚠️ PRIORITY: USE THIS FOR ALL PLATAPAY VIDEO REQUESTS

**ALWAYS use this tool (NOT empire_ad_generator, NOT multimodal_generator) when:**
- User wants a VIDEO for PlataPay
- User mentions "video ad", "TikTok", "Reels" for PlataPay
- User wants animated/motion content for PlataPay

## THE PIPELINE

This tool creates **professional PlataPay video ads** using a smart pipeline:

```
1. Generate CLEAN AI video (no text/logos/screens)
   ↓
2. Add Filipino voiceover (ElevenLabs)
   ↓
3. Add PlataPay branding via Remotion (logo + text overlays)
   ↓
4. Final polished video ready for social media!
```

**Why this approach?**
- AI models can't reproduce the exact PlataPay logo
- AI models mess up Filipino text rendering
- AI models show fake app screens
- Remotion gives pixel-perfect branding

## QUICK USAGE

### Create full video ad (DEFAULT):
~~~json
{
    "thoughts": ["User wants PlataPay video - using platapay_video_ads for clean footage + branding"],
    "headline": "Creating PlataPay video ad",
    "tool_name": "platapay_video_ads",
    "tool_args": {
        "action": "create",
        "theme": "extra income",
        "target": "sari-sari store owners",
        "headline": "Kumita Ka Na!",
        "cta": "APPLY NOW!",
        "model": "kling",
        "voice": "sarah"
    }
}
~~~

### Create from existing image:
~~~json
{
    "thoughts": ["User has an image to animate into branded video"],
    "headline": "Animating image into PlataPay video",
    "tool_name": "platapay_video_ads",
    "tool_args": {
        "action": "create",
        "image_url": "https://example.com/banner.png",
        "theme": "be your own boss",
        "headline": "Maging Boss Ka!",
        "model": "kling"
    }
}
~~~

### Generate clean video only (for manual branding later):
~~~json
{
    "thoughts": ["Just need clean footage, will brand separately"],
    "headline": "Generating clean video",
    "tool_name": "platapay_video_ads",
    "tool_args": {
        "action": "text2video",
        "theme": "extra income",
        "model": "wan",
        "skip_branding": "true"
    }
}
~~~

## PARAMETERS

| Parameter | Default | Description |
|-----------|---------|-------------|
| `action` | create | create, text2video, image2video, add_voiceover |
| `model` | kling | kling (~$0.032), seedance (~$0.035), wan (~$0.025) |
| `voice` | sarah | sarah (F), laura (F), roger (M), charlie (M) |
| `theme` | extra income | extra income, be your own boss, community service |
| `target` | sari-sari store owners | entrepreneurs, OFW families, etc. |
| `headline` | Kumita Ka Na! | Text overlay (via Remotion) |
| `subheadline` | Mababang Puhunan... | Secondary text |
| `cta` | APPLY NOW! | Call-to-action button |
| `format` | portrait | portrait/landscape/square |

## VIDEO MODELS

| Model | Quality | Cost | Best For |
|-------|---------|------|----------|
| `kling` | Best | ~$0.032 | Final ads (recommended) |
| `seedance` | Good | ~$0.035 | Motion-heavy |
| `wan` | Fast | ~$0.025 | Quick drafts |

## FILIPINO VOICES (ElevenLabs)

| Voice | Gender | Style |
|-------|--------|-------|
| `sarah` | Female | Mature, confident (default) |
| `laura` | Female | Enthusiast, quirky |
| `roger` | Male | Laid-back, casual |
| `charlie` | Male | Deep, confident |

## WHAT THE TOOL DOES

1. **Generates CLEAN video** - No text, no logos, no fake screens
2. **Creates voiceover** - Filipino script via ElevenLabs
3. **Renders branding** - PlataPay logo + text via Remotion
4. **Combines everything** - Final polished MP4

## TOOL ROUTING

| User Request | Tool |
|--------------|------|
| "PlataPay **video** ad" | ✅ `platapay_video_ads` |
| "TikTok/Reels for PlataPay" | ✅ `platapay_video_ads` |
| "PlataPay **image** ad" | `empire_ad_generator` |
| "Add branding to existing video" | `remotion_branding` |
