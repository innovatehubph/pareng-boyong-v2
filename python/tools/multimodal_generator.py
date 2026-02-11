"""
Multimodal Generator Tool for Pareng Boyong
Generate and analyze images, videos, and audio using multiple AI models
"""

import os
import time
import json
import base64
import requests
from python.helpers.tool import Tool, Response
from python.helpers.files import get_abs_path


class MultimodalGenerator(Tool):
    """
    Comprehensive multimodal content generator.
    Supports: image analysis, image generation, video generation, audio generation
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "") or os.environ.get("API_KEY_OPENROUTER", "")
        self.replicate_token = os.environ.get("REPLICATE_API_TOKEN", "")
        
        # Model configurations
        self.models = {
            # Image Generation
            "image_analyze": "google/gemini-2.5-flash-image",
            "image_generate": "black-forest-labs/flux-2-pro",
            "image_generate_gemini": "google/gemini-2.5-flash-image",  # Fast generation
            "image_edit_premium": "google/gemini-3-pro-image-preview",  # Nano Banana Pro - Advanced editing
            
            # Image Variation/Reference (preserves elements)
            "image_redux": "black-forest-labs/flux-redux-dev",  # Create variations preserving key elements
            "image_inpaint": "black-forest-labs/flux-fill-dev",  # Inpainting - edit parts of image
            "image_canny": "black-forest-labs/flux-canny-dev",  # Edge-guided generation
            
            # Video
            "video_premium": "bytedance/seedance-1.5-pro",
            "video_premium_alt": "kwaivgi/kling-v2.5-turbo-pro",
            "video_normal": "wan-video/wan-2.2-t2v-fast",
            
            # Audio
            "audio_from_video": "hkchengrex/mmaudio",
        }

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "").lower()
        
        if action == "analyze_image":
            return await self.analyze_image()
        elif action == "generate_image":
            return await self.generate_image()
        elif action == "edit_image":
            return await self.edit_image()
        elif action == "vary_image":
            return await self.vary_image()
        elif action == "generate_video":
            return await self.generate_video()
        elif action == "add_audio":
            return await self.add_audio_to_video()
        elif action == "models":
            return await self.list_models()
        else:
            return Response(
                message="""**Multimodal Generator Actions:**

- `analyze_image` - Analyze/describe an image (OpenRouter/Gemini)
- `generate_image` - Create image from text prompt (FLUX 2 Pro)
- `edit_image` - Edit/transform image with AI (Gemini 3 Pro / Nano Banana) ⭐
- `vary_image` - Create variations preserving key elements (FLUX Redux) ⭐
- `generate_video` - Create video from text prompt (Seedance/Kling/Wan)
- `add_audio` - Add audio to video (MMAudio)
- `models` - List available models

**⚠️ IMPORTANT for Logo Placement:**
To place a REAL logo (like PlataPay) on an image, use the `image_compositor` tool instead!
AI models cannot perfectly preserve specific logos - they will generate approximations.

Use action parameter to specify what you want to do.""",
                break_loop=False
            )

    async def analyze_image(self) -> Response:
        """Analyze an image using OpenRouter/Gemini."""
        image_url = self.args.get("image_url", "")
        prompt = self.args.get("prompt", "What is in this image? Describe it in detail.")
        
        if not image_url:
            return Response(message="Error: image_url is required", break_loop=False)
        
        if not self.openrouter_key:
            return Response(message="Error: OPENROUTER_API_KEY not configured", break_loop=False)
        
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://innovatehub.ph",
                    "X-Title": "Pareng Boyong AI",
                },
                json={
                    "model": self.models["image_analyze"],
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]
                        }
                    ]
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            analysis = data.get("choices", [{}])[0].get("message", {}).get("content", "No analysis available")
            
            return Response(
                message=f"""✅ **Image Analysis Complete**

**Image:** {image_url}
**Model:** {self.models["image_analyze"]}

**Analysis:**
{analysis}""",
                break_loop=False
            )
            
        except requests.exceptions.RequestException as e:
            return Response(message=f"Image analysis error: {str(e)}", break_loop=False)

    async def generate_image(self) -> Response:
        """Generate an image using FLUX 2 Pro on Replicate."""
        prompt = self.args.get("prompt", "")
        aspect_ratio = self.args.get("aspect_ratio", "1:1")
        output_format = self.args.get("output_format", "webp")
        
        if not prompt:
            return Response(message="Error: prompt is required", break_loop=False)
        
        if not self.replicate_token:
            return Response(message="Error: REPLICATE_API_TOKEN not configured", break_loop=False)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.replicate_token}",
                "Content-Type": "application/json",
                "Prefer": "wait"
            }
            
            payload = {
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "output_format": output_format
                }
            }
            
            response = requests.post(
                f"https://api.replicate.com/v1/models/{self.models['image_generate']}/predictions",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            
            output = result.get("output")
            if isinstance(output, list):
                output = output[0] if output else None
            
            return Response(
                message=f"""✅ **Image Generated!**

**Prompt:** {prompt[:100]}{'...' if len(prompt) > 100 else ''}
**Model:** FLUX 2 Pro
**Aspect Ratio:** {aspect_ratio}

**Image URL:** {output}""",
                break_loop=False
            )
            
        except requests.exceptions.RequestException as e:
            return Response(message=f"Image generation error: {str(e)}", break_loop=False)

    async def edit_image(self) -> Response:
        """
        Edit or transform an image using Gemini 3 Pro Image (Nano Banana Pro).
        Can edit existing images or generate new ones with advanced capabilities.
        """
        prompt = self.args.get("prompt", "")
        image_url = self.args.get("image_url", "")
        image_base64 = self.args.get("image_base64", "")
        
        if not prompt:
            return Response(message="Error: prompt is required describing what to edit/generate", break_loop=False)
        
        if not self.openrouter_key:
            return Response(message="Error: OPENROUTER_API_KEY not configured", break_loop=False)
        
        try:
            # Build message content
            content = []
            
            # Add image if provided (for editing)
            if image_url:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
            elif image_base64:
                # Handle base64 image
                if not image_base64.startswith("data:"):
                    image_base64 = f"data:image/png;base64,{image_base64}"
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_base64}
                })
            
            # Add the editing prompt
            content.append({"type": "text", "text": prompt})
            
            self.log.update(progress="🎨 Processing with Gemini 3 Pro (Nano Banana)...")
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://innovatehub.ph",
                    "X-Title": "Pareng Boyong AI",
                },
                json={
                    "model": self.models["image_edit_premium"],
                    "messages": [{"role": "user", "content": content}],
                    "modalities": ["image", "text"]
                },
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract response
            message = data.get("choices", [{}])[0].get("message", {})
            text_response = message.get("content", "")
            
            # Check for generated images in the response
            images = message.get("images", [])
            
            # Also check inline_data format
            if not images and isinstance(message.get("content"), list):
                for part in message.get("content", []):
                    if isinstance(part, dict) and part.get("type") == "image":
                        images.append(part.get("data", ""))
            
            result_msg = f"""✅ **Image Edited with Nano Banana Pro!**

**Prompt:** {prompt[:100]}{'...' if len(prompt) > 100 else ''}
**Model:** Gemini 3 Pro Image (google/gemini-3-pro-image-preview)
**Input Image:** {'Provided' if (image_url or image_base64) else 'None (generation mode)'}
"""
            
            if images:
                result_msg += f"\n**Generated Images:** {len(images)}\n"
                for i, img in enumerate(images):
                    if isinstance(img, str) and len(img) > 100:
                        # It's base64 data
                        result_msg += f"\n**Image {i+1}:** [Base64 data - {len(img)} chars]\n"
                        # Save to file
                        output_path = f"/a0/tmp/edited_image_{int(time.time())}_{i}.png"
                        try:
                            img_data = img
                            if img.startswith("data:"):
                                img_data = img.split(",", 1)[1]
                            with open(output_path, "wb") as f:
                                f.write(base64.b64decode(img_data))
                            result_msg += f"**Saved to:** {output_path}\n"
                        except Exception as e:
                            result_msg += f"(Could not save: {e})\n"
                    else:
                        result_msg += f"\n**Image {i+1}:** {img}\n"
            
            if text_response:
                result_msg += f"\n**AI Response:**\n{text_response[:500]}{'...' if len(text_response) > 500 else ''}"
            
            return Response(message=result_msg, break_loop=False)
            
        except requests.exceptions.RequestException as e:
            return Response(message=f"Image editing error: {str(e)}", break_loop=False)

    async def vary_image(self) -> Response:
        """
        Create variations of an image while preserving key elements using FLUX Redux.
        Good for creating alternate versions while keeping the overall composition.
        NOTE: For exact logo placement, use image_compositor instead!
        """
        image_url = self.args.get("image_url", "")
        guidance = float(self.args.get("guidance", 3))
        aspect_ratio = self.args.get("aspect_ratio", "1:1")
        num_outputs = int(self.args.get("num_outputs", 1))
        
        if not image_url:
            return Response(message="Error: image_url is required (the reference image)", break_loop=False)
        
        if not self.replicate_token:
            return Response(message="Error: REPLICATE_API_TOKEN not configured", break_loop=False)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.replicate_token}",
                "Content-Type": "application/json",
                "Prefer": "wait"
            }
            
            payload = {
                "input": {
                    "redux_image": image_url,
                    "guidance": guidance,
                    "aspect_ratio": aspect_ratio,
                    "num_outputs": min(num_outputs, 4),
                    "output_format": "webp",
                    "output_quality": 90
                }
            }
            
            self.log.update(progress="🔄 Creating image variation with FLUX Redux...")
            
            response = requests.post(
                f"https://api.replicate.com/v1/models/{self.models['image_redux']}/predictions",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            
            output = result.get("output", [])
            if isinstance(output, str):
                output = [output]
            
            result_msg = f"""✅ **Image Variation Created!**

**Reference Image:** {image_url}
**Model:** FLUX Redux
**Guidance:** {guidance}
**Variations Generated:** {len(output)}

"""
            for i, url in enumerate(output):
                result_msg += f"**Variation {i+1}:** {url}\n"
            
            result_msg += """
⚠️ **Note:** FLUX Redux creates variations but may not perfectly preserve specific logos or text.
For exact logo placement, use the `image_compositor` tool instead."""
            
            return Response(message=result_msg, break_loop=False)
            
        except requests.exceptions.RequestException as e:
            return Response(message=f"Image variation error: {str(e)}", break_loop=False)

    async def generate_video(self) -> Response:
        """Generate a video using Replicate models."""
        prompt = self.args.get("prompt", "")
        quality = self.args.get("quality", "normal").lower()  # normal, premium, premium_alt
        image_url = self.args.get("image_url", "")  # For image-to-video
        duration = self.args.get("duration", 5)
        
        if not prompt:
            return Response(message="Error: prompt is required", break_loop=False)
        
        if not self.replicate_token:
            return Response(message="Error: REPLICATE_API_TOKEN not configured", break_loop=False)
        
        # Select model based on quality
        if quality == "premium":
            model = self.models["video_premium"]
            model_name = "Seedance 1.5 Pro"
        elif quality == "premium_alt":
            model = self.models["video_premium_alt"]
            model_name = "Kling v2.5 Turbo Pro"
        else:
            model = self.models["video_normal"]
            model_name = "Wan 2.2 T2V Fast"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.replicate_token}",
                "Content-Type": "application/json",
                "Prefer": "wait"
            }
            
            payload = {"input": {"prompt": prompt}}
            
            # Add image for image-to-video
            if image_url:
                payload["input"]["image"] = image_url
            
            # Add duration if supported
            if quality != "normal":
                payload["input"]["duration"] = duration
            
            self.set_progress(f"Generating video with {model_name}...")
            
            response = requests.post(
                f"https://api.replicate.com/v1/models/{model}/predictions",
                headers=headers,
                json=payload,
                timeout=300  # 5 min timeout for video
            )
            response.raise_for_status()
            result = response.json()
            
            # Handle async predictions
            status = result.get("status")
            prediction_id = result.get("id")
            
            if status == "succeeded":
                output = result.get("output")
            else:
                # Poll for completion
                output = await self._poll_prediction(prediction_id)
            
            if isinstance(output, list):
                output = output[0] if output else None
            
            return Response(
                message=f"""✅ **Video Generated!**

**Prompt:** {prompt[:100]}{'...' if len(prompt) > 100 else ''}
**Model:** {model_name}
**Quality:** {quality}

**Video URL:** {output}

Tip: Use action='add_audio' to add sound to this video.""",
                break_loop=False
            )
            
        except requests.exceptions.RequestException as e:
            return Response(message=f"Video generation error: {str(e)}", break_loop=False)

    async def add_audio_to_video(self) -> Response:
        """Add audio to a video using MMAudio."""
        video_url = self.args.get("video_url", "")
        prompt = self.args.get("prompt", "")
        
        if not video_url:
            return Response(message="Error: video_url is required", break_loop=False)
        
        if not prompt:
            return Response(message="Error: prompt describing the audio is required", break_loop=False)
        
        if not self.replicate_token:
            return Response(message="Error: REPLICATE_API_TOKEN not configured", break_loop=False)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.replicate_token}",
                "Content-Type": "application/json",
                "Prefer": "wait"
            }
            
            payload = {
                "version": "62871fb59889b2d7c13777f08deb3b36bdff88f7e1d53a50ad7694548a41b484",
                "input": {
                    "video": video_url,
                    "prompt": prompt,
                    "seed": -1
                }
            }
            
            self.set_progress("Adding audio to video...")
            
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json=payload,
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status")
            prediction_id = result.get("id")
            
            if status == "succeeded":
                output = result.get("output")
            else:
                output = await self._poll_prediction(prediction_id)
            
            return Response(
                message=f"""✅ **Audio Added to Video!**

**Video:** {video_url}
**Audio Prompt:** {prompt}
**Model:** MMAudio

**Output:** {output}""",
                break_loop=False
            )
            
        except requests.exceptions.RequestException as e:
            return Response(message=f"Audio generation error: {str(e)}", break_loop=False)

    async def _poll_prediction(self, prediction_id: str, max_attempts: int = 60) -> str:
        """Poll Replicate for prediction completion."""
        headers = {
            "Authorization": f"Bearer {self.replicate_token}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(max_attempts):
            time.sleep(5)
            
            response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status")
            
            if status == "succeeded":
                return result.get("output")
            elif status in ["failed", "canceled"]:
                raise Exception(f"Prediction {status}: {result.get('error', 'Unknown error')}")
            
            self.set_progress(f"Processing... ({attempt + 1}/{max_attempts})")
        
        raise Exception("Prediction timed out")

    async def list_models(self) -> Response:
        """List available models."""
        return Response(
            message="""**Available Multimodal Models:**

**Image Analysis:**
- `google/gemini-2.5-flash-image` (OpenRouter) - action=analyze_image

**Image Generation:**
- `black-forest-labs/flux-2-pro` (Replicate) - action=generate_image

**Image Editing (Nano Banana Pro):** ⭐
- `google/gemini-3-pro-image-preview` (OpenRouter) - action=edit_image
  Use for: style transfer, transformations, creative edits
  ⚠️ May alter logos/text - use image_compositor for exact logos

**Image Variation (FLUX Redux):**
- `black-forest-labs/flux-redux-dev` (Replicate) - action=vary_image
  Creates variations while preserving key elements
  ⚠️ Not for exact logo preservation

**Video Generation:**
- `wan-video/wan-2.2-t2v-fast` - Fast, normal quality
- `bytedance/seedance-1.5-pro` - Premium quality  
- `kwaivgi/kling-v2.5-turbo-pro` - Premium alternative

**Audio Generation:**
- `hkchengrex/mmaudio` - Add audio to video

---
**🏷️ FOR EXACT LOGO PLACEMENT:**
Use the `image_compositor` tool instead of AI models!
```
image_compositor action=overlay base_image=<banner> overlay_image=<logo> position=top-left scale=0.15
```""",
            break_loop=False
        )
