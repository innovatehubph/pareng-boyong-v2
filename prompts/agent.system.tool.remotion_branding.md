# remotion_branding

## THE FINAL STEP FOR PLATAPAY VIDEOS

**Use this tool AFTER generating a clean AI video (no text/logos/screens).**

This tool adds **pixel-perfect PlataPay branding** that AI cannot create:
- ✅ Real PlataPay logo (exact PNG)
- ✅ Perfect Filipino text rendering
- ✅ Animated text overlays
- ✅ Pulsing CTA button
- ✅ "INNOVATING PAYMENTS" tagline

## WHEN TO USE

**Use remotion_branding when:**
- You have an AI-generated video ready for branding
- User wants to "finalize" a video with PlataPay branding
- Adding logo and text overlays to existing video
- Creating the final polished video for social media

## WORKFLOW

```
1. Generate clean AI video (no text/logos) → platapay_video_ads or multimodal_generator
2. Add branding → remotion_branding ← YOU ARE HERE
3. Final video ready for upload!
```

## QUICK USAGE

### Brand a video (most common):
~~~json
{
    "thoughts": ["Have an AI video, now adding PlataPay branding with Remotion"],
    "headline": "Adding PlataPay branding to video",
    "tool_name": "remotion_branding",
    "tool_args": {
        "action": "brand",
        "video_url": "https://replicate.delivery/.../video.mp4",
        "headline": "Kumita Ka Na!",
        "subheadline": "Mababang Puhunan, Malaking Kita",
        "cta": "APPLY NOW!",
        "format": "portrait"
    }
}
~~~

### With voiceover:
~~~json
{
    "thoughts": ["Adding branding and voiceover together"],
    "headline": "Branding video with voiceover",
    "tool_name": "remotion_branding",
    "tool_args": {
        "action": "brand",
        "video_url": "https://replicate.delivery/.../video.mp4",
        "voiceover_url": "https://example.com/voice.mp3",
        "headline": "Maging Agent Ka Na!",
        "cta": "APPLY TODAY!",
        "format": "portrait"
    }
}
~~~

## PARAMETERS

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `video_url` | ✅ | - | URL of clean AI video |
| `headline` | ❌ | "Kumita Ka Na!" | Main text overlay |
| `subheadline` | ❌ | "Mababang Puhunan..." | Secondary text |
| `cta` | ❌ | "APPLY NOW!" | Call-to-action button |
| `format` | ❌ | portrait | portrait/landscape/square |
| `voiceover_url` | ❌ | - | Audio URL to include |

## FORMATS

| Format | Resolution | Best For |
|--------|------------|----------|
| `portrait` | 1080x1920 | TikTok, Reels, Stories |
| `landscape` | 1920x1080 | YouTube, Facebook |
| `square` | 1080x1080 | Instagram feed |

## WHAT IT ADDS

1. **PlataPay Logo** - Top-left, animated entrance
2. **"PLATAPAY" text** - Next to logo, silver with glow
3. **Headline** - Center, fade-in + slide animation
4. **Subheadline** - Below headline, fade-in
5. **CTA Button** - Pulsing blue button
6. **Tagline** - Bottom, "INNOVATING PAYMENTS"

## IMPORTANT NOTES

- Input video should have **NO text, NO logos, NO screens**
- AI videos with fake logos/text will look bad
- This tool creates the **final polished output**
- Output is saved to `/root/clawd/video-studio/out/`
