"""
Remotion Branding Tool - Add PlataPay Logo & Text to Videos

WHEN TO USE THIS TOOL:
- User has an AI-generated video and needs PlataPay branding
- User wants to add logo, text, or CTA overlays to a video
- User asks to "brand" a video with PlataPay
- After generating a "clean" video (no text/logos), use this to finalize it
- Keywords: "add logo", "add text", "brand video", "overlay", "finalize video"

THIS TOOL IS FOR THE FINAL STEP:
1. AI generates clean video (no text/logos) → multimodal_generator or platapay_video_ads
2. This tool adds perfect PlataPay branding → remotion_branding

CAPABILITIES:
- Add animated PlataPay logo
- Add headline text with animations
- Add subheadline
- Add CTA button (pulsing animation)
- Add "INNOVATING PAYMENTS" tagline
- Support portrait (TikTok/Reels), landscape (YouTube), square (Instagram)
"""

import os
import subprocess
import httpx
from datetime import datetime
from typing import Optional
from python.helpers.tool import Tool, Response


class RemotionBranding(Tool):
    """
    Add PlataPay branding (logo, text, CTA) to videos using Remotion.
    
    This tool renders pixel-perfect overlays on top of AI-generated videos.
    Use AFTER generating a clean video without text/logos.
    
    Triggers:
    - "add platapay branding to video"
    - "overlay logo on video"
    - "add text to video"
    - "finalize video with branding"
    - "brand this video"
    """
    
    VIDEO_STUDIO_PATH = "/root/clawd/video-studio"
    OUTPUT_DIR = "/root/clawd/video-studio/out"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
    
    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "brand").lower()
        
        actions = {
            "brand": self._brand_video,
            "overlay": self._brand_video,  # Alias
            "help": self._show_help,
            "formats": self._show_formats,
        }
        
        if action not in actions:
            return await self._show_help()
        
        try:
            return await actions[action]()
        except Exception as e:
            return Response(
                message=f"❌ Error: {str(e)}",
                break_loop=False
            )
    
    async def _show_help(self) -> Response:
        return Response(
            message="""🎬 **Remotion Branding Tool**

**Purpose:** Add pixel-perfect PlataPay logo & text to videos.

**Use AFTER generating a clean AI video (no text/logos).**

**Usage:**
```json
{
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
```

**Parameters:**
| Param | Default | Description |
|-------|---------|-------------|
| `video_url` | required | URL of clean AI video |
| `headline` | "Kumita Ka Na!" | Main text |
| `subheadline` | "Mababang..." | Secondary text |
| `cta` | "APPLY NOW!" | Call-to-action button |
| `format` | portrait | portrait/landscape/square |
| `voiceover_url` | optional | Audio to include |

**Formats:**
- `portrait` - 1080x1920 (TikTok, Reels, Stories)
- `landscape` - 1920x1080 (YouTube, Facebook)
- `square` - 1080x1080 (Instagram feed)""",
            break_loop=False
        )
    
    async def _show_formats(self) -> Response:
        return Response(
            message="""📐 **Video Formats:**

| Format | Resolution | Best For |
|--------|------------|----------|
| `portrait` | 1080x1920 | TikTok, Reels, Stories |
| `landscape` | 1920x1080 | YouTube, Facebook |
| `square` | 1080x1080 | Instagram feed |

**Usage:** Add `format="landscape"` to your request.""",
            break_loop=False
        )
    
    async def _brand_video(self) -> Response:
        """Add PlataPay branding to a video."""
        video_url = self.args.get("video_url", "")
        headline = self.args.get("headline", "Kumita Ka Na!")
        subheadline = self.args.get("subheadline", "Mababang Puhunan, Malaking Kita")
        cta = self.args.get("cta", "APPLY NOW!")
        format_type = self.args.get("format", "portrait")
        voiceover_url = self.args.get("voiceover_url", "")
        
        if not video_url:
            return Response(
                message="❌ Error: `video_url` is required.\n\nProvide the URL of the AI-generated video (without text/logos).",
                break_loop=False
            )
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"branded_{timestamp}.mp4"
        output_path = f"{self.OUTPUT_DIR}/{output_filename}"
        
        output = f"🎬 **Rendering PlataPay Branded Video**\n\n"
        output += f"📹 Source: {video_url[:50]}...\n"
        output += f"📐 Format: {format_type}\n"
        output += f"📝 Headline: {headline}\n"
        output += f"📝 Subheadline: {subheadline}\n"
        output += f"🔘 CTA: {cta}\n\n"
        
        try:
            # Download video first
            output += "⏳ Downloading source video...\n"
            video_filename = f"input_{timestamp}.mp4"
            video_path = f"{self.VIDEO_STUDIO_PATH}/public/{video_filename}"
            
            response = httpx.get(video_url, timeout=120, follow_redirects=True)
            if response.status_code != 200:
                return Response(message=f"❌ Failed to download video: HTTP {response.status_code}", break_loop=False)
            
            with open(video_path, 'wb') as f:
                f.write(response.content)
            
            output += f"✅ Downloaded ({len(response.content) // 1024} KB)\n\n"
            
            # Determine composition
            composition_map = {
                "portrait": "VideoOverlay",
                "landscape": "VideoOverlayLandscape",
                "square": "VideoOverlaySquare"
            }
            composition = composition_map.get(format_type, "VideoOverlay")
            
            # Build props JSON
            import json
            props = {
                "videoSrc": video_filename,
                "headline": headline,
                "subheadline": subheadline,
                "cta": cta,
                "theme": "dark",
                "logoPosition": "top-left"
            }
            
            if voiceover_url:
                # Download voiceover
                vo_filename = f"voiceover_{timestamp}.mp3"
                vo_path = f"{self.VIDEO_STUDIO_PATH}/public/{vo_filename}"
                vo_response = httpx.get(voiceover_url, timeout=60, follow_redirects=True)
                if vo_response.status_code == 200:
                    with open(vo_path, 'wb') as f:
                        f.write(vo_response.content)
                    props["voiceoverSrc"] = vo_filename
                    output += "✅ Voiceover downloaded\n"
            
            props_json = json.dumps(props)
            
            # Render with Remotion
            output += "⏳ Rendering with Remotion...\n"
            
            render_cmd = [
                "npx", "remotion", "render",
                "src/index.ts",
                composition,
                output_path,
                f"--props={props_json}",
                "--log=error"
            ]
            
            result = subprocess.run(
                render_cmd,
                cwd=self.VIDEO_STUDIO_PATH,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            # Cleanup downloaded files
            if os.path.exists(video_path):
                os.remove(video_path)
            if voiceover_url and os.path.exists(vo_path):
                os.remove(vo_path)
            
            if result.returncode != 0:
                return Response(
                    message=f"❌ Render failed:\n```\n{result.stderr[:500]}\n```",
                    break_loop=False
                )
            
            if not os.path.exists(output_path):
                return Response(message="❌ Output file not created", break_loop=False)
            
            file_size = os.path.getsize(output_path) // 1024
            
            output += f"""
✅ **Video Rendered Successfully!**

📹 **Output:** `{output_path}`
📦 **Size:** {file_size} KB
📐 **Format:** {format_type}

**Branding Applied:**
- ✅ PlataPay logo (animated)
- ✅ Headline: "{headline}"
- ✅ Subheadline: "{subheadline}"
- ✅ CTA button: "{cta}"
- ✅ Tagline: "INNOVATING PAYMENTS"

**Ready for upload to social media!** 🚀"""
            
            return Response(message=output, break_loop=False)
            
        except subprocess.TimeoutExpired:
            return Response(message="❌ Render timed out (180s limit)", break_loop=False)
        except Exception as e:
            return Response(message=f"❌ Error: {str(e)}", break_loop=False)
