"""
ElevenLabs TTS Tool for Pareng Boyong
Generate high-quality voice overs using ElevenLabs API
"""

import os
import requests
import base64
import time
from python.helpers.tool import Tool, Response
from python.helpers.files import get_abs_path


class ElevenLabsTTS(Tool):
    """
    Generate high-quality voice overs using ElevenLabs API.
    Supports multiple voices and languages.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Available voices
        self.voices = {
            "madam_lyn": "NgAcehsHf3YdZ2ERfilE",
            "rachel": "21m00Tcm4TlvDq8ikWAM",
            "drew": "29vD33N1CtxCmqQRPOHJ",
            "clyde": "2EiwWnXFnvU5JabPnv8n",
            "paul": "5Q0t7uMcjvnagumLfvZi",
            "domi": "AZnzlk1XvdvUeBnXmlld",
            "dave": "CYw3kZ02Hs0563khs1Fj",
            "fin": "D38z5RcWu1voky8WS1ja",
            "sarah": "EXAVITQu4vr4xnSDxMaL",
            "antoni": "ErXwobaYiN019PkySvjV",
            "thomas": "GBv7mTt0atIp3Br8iCZE",
            "charlie": "IKne3meq5aSn9XLyUdCD",
            "emily": "LcfcDJNUP1GQjkzn1xUU",
        }

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "speak").lower()
        
        if action == "speak":
            return await self.text_to_speech()
        elif action == "voices":
            return await self.list_voices()
        else:
            return Response(
                message=f"Unknown action: {action}. Use: speak, voices",
                break_loop=False
            )

    async def text_to_speech(self) -> Response:
        """Convert text to speech and save as audio file."""
        text = self.args.get("text", "")
        voice = self.args.get("voice", "madam_lyn").lower()
        model = self.args.get("model", "eleven_multilingual_v2")
        output_file = self.args.get("output", "")
        stability = float(self.args.get("stability", 0.5))
        similarity = float(self.args.get("similarity", 0.75))
        
        if not text:
            return Response(message="Error: text is required", break_loop=False)
        
        # Get voice ID
        voice_id = self.voices.get(voice, voice)  # Allow direct voice ID too
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = int(time.time())
            output_file = f"tmp/tts_{timestamp}.mp3"
        
        output_path = get_abs_path(output_file)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            # Save audio file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024  # KB
            
            return Response(
                message=f"""✅ **Voice over generated!**

- **File:** `{output_file}`
- **Voice:** {voice}
- **Model:** {model}
- **Size:** {file_size:.1f} KB
- **Text:** {text[:100]}{'...' if len(text) > 100 else ''}

The audio file is ready at: `{output_path}`""",
                break_loop=False
            )
            
        except requests.exceptions.RequestException as e:
            return Response(
                message=f"ElevenLabs API Error: {str(e)}",
                break_loop=False
            )

    async def list_voices(self) -> Response:
        """List available voices."""
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            result = "**Available ElevenLabs Voices:**\n\n"
            result += "**Preset Voices:**\n"
            for name, vid in self.voices.items():
                result += f"- `{name}` ({vid[:8]}...)\n"
            
            result += "\n**All API Voices:**\n"
            for voice in data.get("voices", [])[:15]:
                result += f"- **{voice['name']}** (`{voice['voice_id'][:12]}...`)\n"
            
            return Response(message=result, break_loop=False)
            
        except requests.exceptions.RequestException as e:
            return Response(
                message=f"Error fetching voices: {str(e)}",
                break_loop=False
            )
