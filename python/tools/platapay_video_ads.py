"""
PlataPay Video Ads Generator v2 - Fixed Version

WHEN TO USE THIS TOOL:
- User wants to create a VIDEO AD for PlataPay
- User mentions "video ad", "video marketing", "video promo" for PlataPay
- User asks to create TikTok/Reels/Facebook video ads for PlataPay

PIPELINE:
1. Generate CLEAN AI video (no text/logos/screens)
2. Add Filipino voiceover (ElevenLabs)
3. Brand with Remotion (logo + text)
4. Final polished video
"""

import os
import json
import httpx
import subprocess
import base64
import time
from datetime import datetime
from typing import Optional, Dict, Any
from python.helpers.tool import Tool, Response

# Google Sheets integration
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class PlatapayVideoAds(Tool):
    """
    Create professional video ads for PlataPay agent recruitment.
    Uses clean AI video generation + Remotion branding pipeline.
    """
    
    # Use environment variables (with fallbacks for safety)
    REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
    ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", os.environ.get("API_KEY_OPENROUTER", ""))
    
    # Paths
    CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "/root/.config/clawdbot/google-service-account.json")
    SPREADSHEET_ID = "11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg"
    OUTPUT_DIR = "/root/clawd/video-studio/out"
    VIDEO_STUDIO_PATH = "/root/clawd/video-studio"
    
    # Video Models with CORRECT Replicate API format
    MODELS = {
        "kling": {
            "name": "Kling v2.1",
            "model": "kwaivgi/kling-v2.1",
            "cost": 0.032,
            "supports_image": True,
            "image_key": "start_image"
        },
        "seedance": {
            "name": "Seedance 1.5 Pro", 
            "model": "bytedance/seedance-1.5-pro",
            "cost": 0.035,
            "supports_image": True,
            "image_key": "image"
        },
        "wan": {
            "name": "Wan 2.2 Fast",
            "model": "wan-video/wan-2.2-t2v-fast",
            "cost": 0.025,
            "supports_image": False,
            "image_key": None
        }
    }
    
    # Voices
    VOICES = {
        "sarah": {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "desc": "Confident Female"},
        "laura": {"id": "FGY2WhTYpPnrIDTdsKH5", "name": "Laura", "desc": "Quirky Female"},
        "roger": {"id": "CwhRBWXzGAHq8TQ4Fs17", "name": "Roger", "desc": "Casual Male"},
        "charlie": {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "desc": "Confident Male"}
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
    
    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "create").lower()
        
        # Validate API keys first
        if not self.REPLICATE_API_TOKEN:
            return Response(message="❌ Error: REPLICATE_API_TOKEN not set in environment", break_loop=False)
        
        actions = {
            "create": self._create_video_ad,
            "generate": self._create_video_ad,
            "text2video": self._text_to_video,
            "image2video": self._image_to_video,
            "add_voiceover": self._add_voiceover,
            "list": self._list_videos,
            "help": self._show_help,
            "test": self._test_api,  # Debug action
        }
        
        if action not in actions:
            return await self._show_help()
        
        try:
            return await actions[action]()
        except Exception as e:
            return Response(
                message=f"❌ Error: {str(e)}\n\n**Debug Info:**\n- Action: {action}\n- Args: {self.args}",
                break_loop=False
            )
    
    async def _test_api(self) -> Response:
        """Test API connectivity."""
        output = "🔧 **API Connectivity Test**\n\n"
        
        # Test Replicate
        try:
            resp = httpx.get(
                "https://api.replicate.com/v1/models/kwaivgi/kling-v2.1",
                headers={"Authorization": f"Bearer {self.REPLICATE_API_TOKEN}"},
                timeout=10
            )
            if resp.status_code == 200:
                output += "✅ Replicate API: Connected\n"
            else:
                output += f"❌ Replicate API: {resp.status_code}\n"
        except Exception as e:
            output += f"❌ Replicate API: {e}\n"
        
        # Test ElevenLabs
        try:
            resp = httpx.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": self.ELEVENLABS_API_KEY},
                timeout=10
            )
            if resp.status_code == 200:
                output += "✅ ElevenLabs API: Connected\n"
            else:
                output += f"❌ ElevenLabs API: {resp.status_code}\n"
        except Exception as e:
            output += f"❌ ElevenLabs API: {e}\n"
        
        return Response(message=output, break_loop=False)
    
    async def _show_help(self) -> Response:
        return Response(
            message="""🎬 **PlataPay Video Ads Generator v2**

**Actions:**
- `create` - Full pipeline (video + voice + branding)
- `text2video` - Generate clean video only
- `image2video` - Animate an image
- `add_voiceover` - Add voice to video
- `list` - Show recent videos
- `test` - Test API connectivity

**Parameters:**
| Param | Default | Options |
|-------|---------|---------|
| `theme` | extra income | be your own boss, community service |
| `target` | sari-sari owners | entrepreneurs, OFW families |
| `model` | kling | seedance, wan |
| `voice` | sarah | laura, roger, charlie |
| `headline` | Kumita Ka Na! | Custom text |
| `cta` | APPLY NOW! | Custom CTA |

**Example:**
```
action=create theme="extra income" target="entrepreneurs" voice=charlie
```""",
            break_loop=False
        )
    
    async def _create_video_ad(self) -> Response:
        """Full video ad pipeline with robust error handling."""
        theme = self.args.get("theme", "extra income")
        target = self.args.get("target", "sari-sari store owners")
        model = self.args.get("model", "kling")
        voice = self.args.get("voice", "sarah")
        headline = self.args.get("headline", "Kumita Ka Na!")
        subheadline = self.args.get("subheadline", "Mababang Puhunan, Malaking Kita")
        cta = self.args.get("cta", "APPLY NOW!")
        image_url = self.args.get("image_url", "")
        skip_branding = self.args.get("skip_branding", "false").lower() == "true"
        
        ad_id = f"VID-{int(datetime.now().timestamp())}"
        total_cost = 0.0
        
        output = f"🎬 **Creating PlataPay Video Ad**\n\n"
        output += f"📋 ID: {ad_id}\n"
        output += f"🎯 Theme: {theme} | Target: {target}\n"
        output += f"🎥 Model: {self.MODELS.get(model, self.MODELS['kling'])['name']}\n\n"
        
        # Step 1: Generate clean video
        output += "---\n**Step 1: Generating Clean Video**\n\n"
        
        if image_url:
            video_result = await self._generate_video_from_image(image_url, theme, model)
        else:
            video_result = await self._generate_video_from_text(theme, target, model)
        
        if video_result.get("error"):
            return Response(
                message=f"❌ Video generation failed:\n```\n{video_result['error']}\n```\n\n**Debug:** Model={model}, Theme={theme}",
                break_loop=False
            )
        
        video_url = video_result["url"]
        total_cost += self.MODELS.get(model, self.MODELS['kling'])['cost']
        output += f"✅ Video generated: {video_url[:60]}...\n\n"
        
        # Step 2: Generate voiceover
        output += "---\n**Step 2: Generating Filipino Voiceover**\n\n"
        script = self._generate_script(theme, target)
        output += f"📝 Script: {script[:80]}...\n"
        
        voice_result = await self._generate_voiceover(script, voice)
        voice_path = None
        
        if voice_result.get("error"):
            output += f"⚠️ Voiceover failed: {voice_result['error']}\n"
            output += "Continuing without voiceover...\n\n"
        else:
            voice_path = voice_result["path"]
            total_cost += 0.015
            output += f"✅ Voiceover created: {voice_path}\n\n"
        
        # Step 3: Brand with Remotion (if not skipped)
        final_video = video_url
        
        if not skip_branding:
            output += "---\n**Step 3: Adding PlataPay Branding (Remotion)**\n\n"
            
            brand_result = await self._apply_remotion_branding(
                video_url, voice_path, headline, subheadline, cta
            )
            
            if brand_result.get("error"):
                output += f"⚠️ Branding failed: {brand_result['error']}\n"
                output += "Returning unbranded video...\n\n"
            else:
                final_video = brand_result["path"]
                output += f"✅ Branded video: {final_video}\n\n"
        
        # Summary
        output += f"""---
✅ **Video Ad Complete!**

📹 **Final Video:** {final_video}
💰 **Total Cost:** ${total_cost:.3f}
🆔 **Ad ID:** {ad_id}

**Branding Applied:**
- Logo: PlataPay (animated)
- Headline: "{headline}"
- CTA: "{cta}"
"""
        
        return Response(message=output, break_loop=False)
    
    async def _generate_video_from_text(self, theme: str, target: str, model: str) -> Dict[str, Any]:
        """Generate clean video from text prompt using Replicate."""
        prompt = self._build_clean_prompt(theme, target)
        model_config = self.MODELS.get(model, self.MODELS['kling'])
        
        try:
            # Use the correct Replicate API format
            response = httpx.post(
                f"https://api.replicate.com/v1/models/{model_config['model']}/predictions",
                headers={
                    "Authorization": f"Bearer {self.REPLICATE_API_TOKEN}",
                    "Content-Type": "application/json",
                    "Prefer": "wait"  # Wait for result
                },
                json={
                    "input": {
                        "prompt": prompt
                    }
                },
                timeout=300
            )
            
            if response.status_code == 401:
                return {"error": "API authentication failed (401). Check REPLICATE_API_TOKEN."}
            elif response.status_code == 422:
                return {"error": f"Invalid payload (422): {response.text[:200]}"}
            elif response.status_code == 429:
                return {"error": "Rate limited (429). Please wait and try again."}
            elif response.status_code not in [200, 201]:
                return {"error": f"API error ({response.status_code}): {response.text[:200]}"}
            
            result = response.json()
            
            # Handle different response formats
            if result.get("output"):
                output = result["output"]
                url = output[0] if isinstance(output, list) else output
                return {"url": url}
            elif result.get("status") == "failed":
                return {"error": f"Generation failed: {result.get('error', 'Unknown error')}"}
            elif result.get("status") == "processing":
                return {"error": "Generation still processing. Try again in 30 seconds."}
            else:
                return {"error": f"Unexpected response: {json.dumps(result)[:200]}"}
                
        except httpx.TimeoutException:
            return {"error": "Request timed out (300s). Video may still be generating."}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def _generate_video_from_image(self, image_url: str, theme: str, model: str) -> Dict[str, Any]:
        """Generate video from image using image-to-video model."""
        model_config = self.MODELS.get(model, self.MODELS['kling'])
        
        if not model_config.get("supports_image"):
            # Fallback to text-to-video
            return await self._generate_video_from_text(theme, "entrepreneurs", model)
        
        motion_prompt = f"Person smiles warmly, subtle natural movement. Theme: {theme}. NO text, NO logos."
        
        try:
            payload = {
                "input": {
                    model_config["image_key"]: image_url,
                    "prompt": motion_prompt
                }
            }
            
            response = httpx.post(
                f"https://api.replicate.com/v1/models/{model_config['model']}/predictions",
                headers={
                    "Authorization": f"Bearer {self.REPLICATE_API_TOKEN}",
                    "Content-Type": "application/json",
                    "Prefer": "wait"
                },
                json=payload,
                timeout=300
            )
            
            if response.status_code not in [200, 201]:
                return {"error": f"API error ({response.status_code}): {response.text[:200]}"}
            
            result = response.json()
            
            if result.get("output"):
                output = result["output"]
                url = output[0] if isinstance(output, list) else output
                return {"url": url}
            else:
                return {"error": f"No output in response: {json.dumps(result)[:200]}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _generate_voiceover(self, script: str, voice: str) -> Dict[str, Any]:
        """Generate Filipino voiceover using ElevenLabs."""
        if not self.ELEVENLABS_API_KEY:
            return {"error": "ELEVENLABS_API_KEY not set"}
        
        voice_config = self.VOICES.get(voice, self.VOICES['sarah'])
        
        try:
            response = httpx.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_config['id']}",
                headers={
                    "xi-api-key": self.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": script,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return {"error": f"ElevenLabs error ({response.status_code}): {response.text[:100]}"}
            
            # Save audio file
            timestamp = int(datetime.now().timestamp())
            audio_path = f"{self.OUTPUT_DIR}/vo_{timestamp}.mp3"
            
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            return {"path": audio_path}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _apply_remotion_branding(
        self, video_url: str, voice_path: Optional[str],
        headline: str, subheadline: str, cta: str
    ) -> Dict[str, Any]:
        """Apply PlataPay branding using Remotion."""
        timestamp = int(datetime.now().timestamp())
        
        try:
            # Download video
            video_filename = f"input_{timestamp}.mp4"
            video_local = f"{self.VIDEO_STUDIO_PATH}/public/{video_filename}"
            
            resp = httpx.get(video_url, timeout=120, follow_redirects=True)
            if resp.status_code != 200:
                return {"error": f"Failed to download video: {resp.status_code}"}
            
            with open(video_local, 'wb') as f:
                f.write(resp.content)
            
            # Build props for Remotion
            props = {
                "videoSrc": video_filename,
                "headline": headline,
                "subheadline": subheadline,
                "cta": cta,
                "theme": "dark",
                "logoPosition": "top-left"
            }
            
            # Add voiceover if available
            if voice_path and os.path.exists(voice_path):
                vo_filename = os.path.basename(voice_path)
                # Copy to public folder
                vo_public = f"{self.VIDEO_STUDIO_PATH}/public/{vo_filename}"
                subprocess.run(["cp", voice_path, vo_public], check=True)
                props["voiceoverSrc"] = vo_filename
            
            props_json = json.dumps(props)
            output_path = f"{self.OUTPUT_DIR}/branded_{timestamp}.mp4"
            
            # Render with Remotion
            result = subprocess.run(
                [
                    "npx", "remotion", "render",
                    "src/index.ts", "VideoOverlay", output_path,
                    f"--props={props_json}",
                    "--log=error"
                ],
                cwd=self.VIDEO_STUDIO_PATH,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            # Cleanup
            if os.path.exists(video_local):
                os.remove(video_local)
            
            if result.returncode != 0:
                return {"error": f"Remotion error: {result.stderr[:200]}"}
            
            if os.path.exists(output_path):
                return {"path": output_path}
            else:
                return {"error": "Output file not created"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Remotion render timed out (180s)"}
        except Exception as e:
            return {"error": str(e)}
    
    def _build_clean_prompt(self, theme: str, target: str) -> str:
        """Build a CLEAN video prompt - devices OK but screen not visible."""
        person = {
            "sari-sari store owners": "Filipino sari-sari store owner",
            "entrepreneurs": "Filipino entrepreneur", 
            "OFW families": "Filipino family member",
            "small business owners": "Filipino small business owner",
        }.get(target, "Filipino person")
        
        scene = {
            "extra income": "holding smartphone and smiling at good news, celebrating success",
            "be your own boss": "confidently checking phone then looking up proudly at camera",
            "community service": "helping customer with tablet, both smiling warmly",
        }.get(theme.lower(), "using phone then smiling warmly at camera")
        
        return f"""Cinematic video of a happy {person} {scene}.

DEVICE RULES:
- Person CAN hold phone, tablet, or laptop
- Device SCREEN must face AWAY from camera or be OUT OF FOCUS
- NEVER show what is on the screen
- Focus on PERSON'S FACE, not the device

MONEY RULES (IMPORTANT):
- If showing money/cash, it MUST look like Philippine Peso bills
- NO foreign currency (no US dollars, no other currencies)
- Money should be slightly OUT OF FOCUS or not too close-up
- Money is secondary - focus remains on person's happy expression
- Philippine Peso bills are colorful (blue, orange, green, brown)

OTHER REQUIREMENTS:
1. NO text, words, or captions overlaid on the video
2. NO logos or brand symbols anywhere
3. Clean footage only - branding added in post-production

SCENE COMPOSITION:
- Person in Philippine sari-sari store or small business
- Warm, natural golden hour lighting
- Focus on person's happy, successful Filipino expression

CAMERA: Medium shot focusing on person's face and emotion.
MOOD: Aspirational, warm, authentic Filipino success.
DURATION: 5 seconds."""
    
    def _generate_script(self, theme: str, target: str) -> str:
        """Generate Filipino voiceover script."""
        scripts = {
            "extra income": f"Gusto mo bang kumita ng extra? Maging PlataPay Agent ka na! Mababa ang puhunan, malaki ang kita!",
            "be your own boss": f"Maging sarili mong boss! PlataPay Agent - ikaw ang may hawak ng oras at kita mo!",
            "community service": f"Tumulong sa community mo habang kumikita! PlataPay Agent ka na!",
        }
        return scripts.get(theme.lower(), scripts["extra income"])
    
    async def _text_to_video(self) -> Response:
        """Generate clean video only (no branding)."""
        theme = self.args.get("theme", "extra income")
        target = self.args.get("target", "entrepreneurs")
        model = self.args.get("model", "kling")
        
        result = await self._generate_video_from_text(theme, target, model)
        
        if result.get("error"):
            return Response(message=f"❌ Error: {result['error']}", break_loop=False)
        
        return Response(
            message=f"""✅ **Clean Video Generated**

🎥 URL: {result['url']}
🎬 Model: {self.MODELS.get(model, {}).get('name', model)}
💰 Cost: ~${self.MODELS.get(model, {}).get('cost', 0.03):.3f}

**Note:** This is clean footage (no branding).
Use `remotion_branding` tool to add PlataPay logo and text.""",
            break_loop=False
        )
    
    async def _image_to_video(self) -> Response:
        """Animate an image into video."""
        image_url = self.args.get("image_url", "")
        theme = self.args.get("theme", "extra income")
        model = self.args.get("model", "kling")
        
        if not image_url:
            return Response(message="❌ Error: `image_url` is required", break_loop=False)
        
        result = await self._generate_video_from_image(image_url, theme, model)
        
        if result.get("error"):
            return Response(message=f"❌ Error: {result['error']}", break_loop=False)
        
        return Response(
            message=f"""✅ **Image Animated**

🎥 Video: {result['url']}
🖼️ Source: {image_url[:50]}...""",
            break_loop=False
        )
    
    async def _add_voiceover(self) -> Response:
        """Add voiceover to video."""
        video_url = self.args.get("video_url", "")
        script = self.args.get("script", "")
        voice = self.args.get("voice", "sarah")
        
        if not video_url or not script:
            return Response(message="❌ Error: `video_url` and `script` required", break_loop=False)
        
        result = await self._generate_voiceover(script, voice)
        
        if result.get("error"):
            return Response(message=f"❌ Error: {result['error']}", break_loop=False)
        
        return Response(
            message=f"""✅ **Voiceover Generated**

🎙️ Audio: {result['path']}
📝 Script: {script[:50]}...""",
            break_loop=False
        )
    
    async def _list_videos(self) -> Response:
        """List recent generated videos."""
        try:
            files = os.listdir(self.OUTPUT_DIR)
            videos = [f for f in files if f.endswith('.mp4')]
            videos.sort(reverse=True)
            
            if not videos:
                return Response(message="📹 No videos generated yet.", break_loop=False)
            
            output = "📹 **Recent Videos:**\n\n"
            for v in videos[:10]:
                path = f"{self.OUTPUT_DIR}/{v}"
                size = os.path.getsize(path) // 1024
                output += f"- `{v}` ({size} KB)\n"
            
            return Response(message=output, break_loop=False)
        except Exception as e:
            return Response(message=f"Error: {e}", break_loop=False)
