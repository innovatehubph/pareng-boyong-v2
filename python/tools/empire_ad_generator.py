"""
Empire Ad Generator - PlataPay Marketing Content Automation
Generates complete marketing ads for PlataPay agent recruitment.

WHEN TO USE THIS TOOL:
- User asks to create marketing ads for PlataPay
- User mentions "Empire" (PlataPay's marketing arm)
- User wants to generate promotional content for PlataPay agents
- User asks for social media ads, video ads, or marketing materials for PlataPay
- Keywords: "platapay ad", "empire marketing", "agent recruitment ad", "platapay promo"

CAPABILITIES:
- Generate ad copy (Facebook, Instagram, TikTok, etc.)
- Generate marketing images via AI
- Generate marketing videos via AI
- Save all content to Google Sheets for tracking
"""

import httpx
import os
import json
from datetime import datetime
from typing import Any, Optional
from python.helpers.tool import Tool, Response

# Google Sheets integration
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class EmpireAdGenerator(Tool):
    """
    Generate complete marketing ads for PlataPay agent recruitment.
    Used by Empire (PlataPay's marketing arm).
    
    Triggers on:
    - "create platapay ad"
    - "generate marketing for platapay"
    - "empire ad generator"
    - "platapay marketing"
    - "agent recruitment ad"
    - "promotional content for platapay"
    """
    
    CREDENTIALS_PATH = "/root/.config/clawdbot/google-service-account.json"
    SPREADSHEET_ID = "11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg"
    REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
    
    # PlataPay Brand Guidelines
    BRAND = {
        "name": "PlataPay",
        "tagline": "INNOVATING PAYMENTS",
        "description": "Digital payment platform franchise for agents/outlet owners",
        "services": ["Bills Payment", "E-Load", "Remittance", "Bank Transfer", "QR Payments"],
        "value_props": [
            "Mababa ang puhunan, malaki ang kita",
            "Kumita sa bawat transaction",
            "Maging sarili mong boss",
            "Full support from PlataPay team"
        ],
        "target_audiences": [
            "Sari-sari store owners",
            "Aspiring entrepreneurs", 
            "OFW families",
            "Small business owners",
            "Stay-at-home parents"
        ],
        "tone": "Friendly, aspirational, Taglish (Filipino-English mix)",
        "colors": "Silver metallic, professional blue"
    }
    
    async def execute(self, **kwargs) -> Response:
        action = kwargs.get("action", "generate_full")
        theme = kwargs.get("theme", "extra income")
        target = kwargs.get("target", "sari-sari store owners")
        promo = kwargs.get("promo", "")
        ad_type = kwargs.get("ad_type", "facebook")
        generate_image = kwargs.get("generate_image", True)
        generate_video = kwargs.get("generate_video", True)
        save_to_sheet = kwargs.get("save_to_sheet", True)
        
        if action == "help":
            return await self._show_help()
        elif action == "generate_copy":
            return await self._generate_ad_copy(theme, target, promo, ad_type)
        elif action == "generate_image":
            return await self._generate_image(theme, target)
        elif action == "generate_video":
            image_url = kwargs.get("image_url", "")
            return await self._generate_video(image_url, theme)
        elif action == "generate_full":
            return await self._generate_full_ad(theme, target, promo, ad_type, generate_image, generate_video, save_to_sheet)
        elif action == "list_ads":
            return await self._list_recent_ads()
        else:
            return Response(
                message=f"Unknown action: {action}. Use: generate_full, generate_copy, generate_image, generate_video, list_ads, help",
                break_loop=False
            )
    
    async def _show_help(self) -> Response:
        return Response(
            message="""🎯 **Empire Ad Generator - PlataPay Marketing**

**What I do:** Generate complete marketing ads for PlataPay agent recruitment.

**Actions:**
- `generate_full` - Create ad copy + image + video (default)
- `generate_copy` - Create ad copy only
- `generate_image` - Generate marketing image
- `generate_video` - Generate marketing video
- `list_ads` - Show recent generated ads

**Parameters:**
- `theme` - Campaign theme (default: "extra income")
- `target` - Target audience (default: "sari-sari store owners")
- `promo` - Special promo text (optional)
- `ad_type` - facebook, instagram, tiktok, story (default: facebook)

**Example:**
```
Generate a PlataPay ad for OFW families with "FREE training" promo
```

**Target Audiences:** Sari-sari owners, Entrepreneurs, OFW families, Small business owners

**Ad Types:** Facebook, Instagram, TikTok/Reels, Story ads, Carousel""",
            break_loop=False
        )
    
    async def _generate_ad_copy(self, theme: str, target: str, promo: str, ad_type: str) -> Response:
        """Generate ad copy using AI."""
        openrouter_key = os.environ.get('OPENROUTER_API_KEY', '')
        
        prompt = f"""You are an expert Filipino marketing copywriter for PlataPay.

BRAND: {self.BRAND['name']} - {self.BRAND['tagline']}
PRODUCT: {self.BRAND['description']}
SERVICES: {', '.join(self.BRAND['services'])}
TONE: {self.BRAND['tone']}

Create a {ad_type.upper()} ad for PlataPay agent recruitment:
Theme: {theme}
Target Audience: {target}
Promo: {promo or 'Standard recruitment - no special promo'}

Write in Taglish. Include emojis. Make it scroll-stopping.

Format:
HOOK: [one attention-grabbing line]
BODY: [main copy with benefits, 80-100 words]
CTA: [call to action]
HASHTAGS: [5-7 relevant hashtags]"""

        try:
            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60
            )
            result = response.json()
            ad_copy = result['choices'][0]['message']['content']
            
            return Response(
                message=f"📝 **Generated {ad_type.upper()} Ad Copy**\n\n{ad_copy}",
                break_loop=False
            )
        except Exception as e:
            return Response(message=f"Error generating ad copy: {e}", break_loop=False)
    
    async def _generate_image(self, theme: str, target: str) -> Response:
        """Generate marketing image using FLUX."""
        image_prompt = f"""Professional Filipino marketing photo for digital payment business.

SUBJECT: Happy Filipino {target.replace('owners', 'owner')} holding smartphone, with warm genuine smile.

DEVICE RULES:
- Person CAN hold phone or tablet
- Device SCREEN must face AWAY from camera (show back of phone)
- NEVER show what is on the screen
- Focus on PERSON'S FACE, device is secondary

MONEY RULES (IMPORTANT):
- If showing money/cash, it MUST be Philippine Peso bills
- NO foreign currency (no US dollars, no other currencies)
- Money should be slightly blurred or not in sharp focus
- Philippine Peso bills are colorful (blue 1000, orange 20, green 200)
- Money is background element - person is the focus

OTHER REQUIREMENTS:
- NO text or words in the image
- NO logos or brand symbols (real logo added in post)
- Clear space at top-left corner for logo overlay
- Clear space at center for text overlay

COMPOSITION:
- Filipino person in sari-sari store
- Smiling at camera, confident successful expression
- Warm natural lighting, Philippine setting

STYLE: Professional advertising photography, aspirational mood.
THEME: {theme}
OUTPUT: Clean image ready for branding overlay."""
        
        try:
            response = httpx.post(
                "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions",
                headers={
                    "Authorization": f"Bearer {self.REPLICATE_API_TOKEN}",
                    "Content-Type": "application/json",
                    "Prefer": "wait"
                },
                json={
                    "input": {
                        "prompt": image_prompt,
                        "num_outputs": 1,
                        "aspect_ratio": "4:5",
                        "output_format": "webp",
                        "output_quality": 90
                    }
                },
                timeout=120
            )
            result = response.json()
            
            if result.get('output'):
                image_url = result['output'][0] if isinstance(result['output'], list) else result['output']
                return Response(
                    message=f"🖼️ **Image Generated!**\n\nURL: {image_url}\n\nPrompt used: {image_prompt[:200]}...",
                    break_loop=False
                )
            else:
                return Response(message=f"Image generation failed: {result}", break_loop=False)
        except Exception as e:
            return Response(message=f"Error generating image: {e}", break_loop=False)
    
    async def _generate_video(self, image_url: str, theme: str, ad_copy: str = "") -> Response:
        """Generate marketing video using Seedance with Filipino voiceover."""
        if not image_url:
            return Response(message="Error: image_url is required for video generation", break_loop=False)
        
        video_prompt = f"""Filipino business owner using phone then celebrating success.

DEVICE RULES:
- Person CAN hold and use phone/tablet
- Device SCREEN must face AWAY from camera or be OUT OF FOCUS
- NEVER show what is on the screen
- Focus on person's face, not the device

OTHER REQUIREMENTS:
- NO text overlays or captions
- NO logos in frame
- Clean footage for post-production branding

ACTION: Person looks at phone (screen away from camera), receives good news, looks up at camera with big confident smile.
CAMERA: Medium shot, smooth movement, cinematic.
MOOD: Uplifting, aspirational, Filipino success with technology. Theme: {theme}.
DURATION: 5 seconds."""
        
        try:
            # Step 1: Generate video with Seedance
            response = httpx.post(
                "https://api.replicate.com/v1/models/bytedance/seedance-1.5-pro/predictions",
                headers={
                    "Authorization": f"Bearer {self.REPLICATE_API_TOKEN}",
                    "Content-Type": "application/json",
                    "Prefer": "wait"
                },
                json={
                    "input": {
                        "image": image_url,
                        "prompt": video_prompt
                    }
                },
                timeout=300
            )
            result = response.json()
            
            if result.get('status') == 'succeeded' and result.get('output'):
                video_url = result['output']
                
                # Step 2: Add Filipino voiceover if ad_copy provided
                final_video_url = video_url
                voiceover_note = ""
                
                if ad_copy:
                    try:
                        final_video_url, voiceover_note = await self._add_filipino_voiceover(video_url, ad_copy, theme)
                    except Exception as e:
                        voiceover_note = f"\n⚠️ Could not add voiceover: {e}"
                
                return Response(
                    message=f"🎬 **Video Generated!**\n\nURL: {final_video_url}{voiceover_note}",
                    break_loop=False
                )
            else:
                return Response(message=f"Video generation status: {result.get('status')}", break_loop=False)
        except Exception as e:
            return Response(message=f"Error generating video: {e}", break_loop=False)
    
    async def _add_filipino_voiceover(self, video_url: str, ad_copy: str, theme: str) -> tuple:
        """Add Filipino voiceover to video using Google TTS."""
        import subprocess
        import tempfile
        
        # Extract a short script from ad copy (for voiceover)
        voiceover_script = self._extract_voiceover_script(ad_copy, theme)
        
        try:
            from google.cloud import texttospeech
            import os
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.CREDENTIALS_PATH
            
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=voiceover_script)
            voice = texttospeech.VoiceSelectionParams(
                language_code="fil-PH",
                name="fil-ph-Neural2-A"  # Filipino female voice
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
                audio_file.write(response.audio_content)
                audio_path = audio_file.name
            
            # Download video
            video_response = httpx.get(video_url, timeout=60)
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
                video_file.write(video_response.content)
                video_path = video_file.name
            
            # Combine with ffmpeg
            output_path = f"/root/clawd/assets/platapay_ad_{int(datetime.now().timestamp())}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", output_path
            ], capture_output=True, timeout=60)
            
            if os.path.exists(output_path):
                return output_path, "\n🎙️ Filipino voiceover added!"
            else:
                return video_url, "\n⚠️ Voiceover merge failed, using original"
                
        except Exception as e:
            return video_url, f"\n⚠️ Voiceover error: {e}"
    
    def _extract_voiceover_script(self, ad_copy: str, theme: str) -> str:
        """Extract a short voiceover script from ad copy."""
        # Default Filipino voiceover script
        default_scripts = {
            "extra income": "Gusto mo bang kumita ng extra? Maging PlataPay Agent ka na! Mababa lang ang puhunan, malaki ang kita. Mag-apply na!",
            "be your own boss": "Maging sarili mong boss! PlataPay Agent - kumita habang tumutulong sa community mo. Mag-apply na!",
            "default": "PlataPay Agent ka na ba? Bills payment, e-load, remittance - lahat pwede mo i-offer! Mababa ang puhunan, malaki ang kita. Mag-apply na!"
        }
        
        # Try to extract from ad copy, otherwise use default
        theme_lower = theme.lower()
        for key, script in default_scripts.items():
            if key in theme_lower:
                return script
        return default_scripts["default"]
    
    async def _generate_full_ad(self, theme: str, target: str, promo: str, ad_type: str, 
                                 generate_image: bool, generate_video: bool, save_to_sheet: bool) -> Response:
        """Generate complete ad with copy, image, and video."""
        output = f"🎯 **Empire Ad Generator - Full Ad Creation**\n\n"
        output += f"📋 Theme: {theme}\n🎯 Target: {target}\n🎁 Promo: {promo or 'None'}\n\n"
        
        ad_id = f"AD-{int(datetime.now().timestamp())}"
        ad_copy = ""
        image_url = ""
        video_url = ""
        
        # 1. Generate Ad Copy
        output += "---\n\n📝 **Generating Ad Copy...**\n\n"
        copy_result = await self._generate_ad_copy(theme, target, promo, ad_type)
        ad_copy = copy_result.message
        output += ad_copy + "\n\n"
        
        # 2. Generate Image
        if generate_image:
            output += "---\n\n🖼️ **Generating Image...**\n\n"
            image_result = await self._generate_image(theme, target)
            output += image_result.message + "\n\n"
            # Extract URL from message
            if "URL:" in image_result.message:
                image_url = image_result.message.split("URL:")[1].split("\n")[0].strip()
        
        # 3. Generate Video
        if generate_video and image_url:
            output += "---\n\n🎬 **Generating Video...**\n\n"
            video_result = await self._generate_video(image_url, theme)
            output += video_result.message + "\n\n"
            # Extract URL from message
            if "URL:" in video_result.message:
                video_url = video_result.message.split("URL:")[1].split("\n")[0].strip()
        
        # 4. Save to Google Sheets
        if save_to_sheet and GOOGLE_AVAILABLE:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.CREDENTIALS_PATH,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                service = build('sheets', 'v4', credentials=credentials)
                
                values = [[
                    ad_id,
                    ad_type,
                    theme,
                    target,
                    ad_copy[:1000],
                    promo,
                    "Generated",
                    datetime.now().strftime("%Y-%m-%d"),
                    image_url,
                    video_url
                ]]
                
                service.spreadsheets().values().append(
                    spreadsheetId=self.SPREADSHEET_ID,
                    range='Ads!A:J',
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body={'values': values}
                ).execute()
                
                output += f"---\n\n💾 **Saved to Google Sheets!**\nAd ID: {ad_id}\n"
                output += f"📊 View: https://docs.google.com/spreadsheets/d/{self.SPREADSHEET_ID}\n"
            except Exception as e:
                output += f"\n⚠️ Could not save to sheet: {e}\n"
        
        output += "\n---\n✅ **Ad Generation Complete!**"
        
        return Response(message=output, break_loop=False)
    
    async def _list_recent_ads(self) -> Response:
        """List recent generated ads from Google Sheets."""
        if not GOOGLE_AVAILABLE:
            return Response(message="Google Sheets not available", break_loop=False)
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.CREDENTIALS_PATH,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            service = build('sheets', 'v4', credentials=credentials)
            
            result = service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range='Ads!A:J'
            ).execute()
            
            values = result.get('values', [])
            
            if len(values) <= 1:
                return Response(message="📚 No ads generated yet.", break_loop=False)
            
            output = "📚 **Recent Generated Ads**\n\n"
            for row in values[-5:]:  # Last 5 ads
                if row and row[0] != 'Ad ID':
                    output += f"**{row[0]}** | {row[2] if len(row) > 2 else ''} | {row[3] if len(row) > 3 else ''}\n"
            
            output += f"\n📊 Full list: https://docs.google.com/spreadsheets/d/{self.SPREADSHEET_ID}"
            
            return Response(message=output, break_loop=False)
        except Exception as e:
            return Response(message=f"Error listing ads: {e}", break_loop=False)
