"""
MMAudio Tool for Pareng Boyong
Generate audio from video using Replicate's MMAudio model
"""

import os
import time
import requests
from python.helpers.tool import Tool, Response


class MMAudio(Tool):
    """
    Generate audio for videos using MMAudio model on Replicate.
    Creates sound effects, ambience, or music based on video content.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_token = os.environ.get("REPLICATE_API_TOKEN", "")
        self.version = "62871fb59889b2d7c13777f08deb3b36bdff88f7e1d53a50ad7694548a41b484"
        self.base_url = "https://api.replicate.com/v1/predictions"

    async def execute(self, **kwargs) -> Response:
        video_url = self.args.get("video", "")
        prompt = self.args.get("prompt", "")
        negative_prompt = self.args.get("negative_prompt", "")
        seed = int(self.args.get("seed", -1))
        duration = float(self.args.get("duration", 0))  # 0 = auto from video
        
        if not video_url:
            return Response(message="Error: video URL is required", break_loop=False)
        
        if not prompt:
            return Response(message="Error: prompt describing the audio is required", break_loop=False)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "version": self.version,
                "input": {
                    "video": video_url,
                    "prompt": prompt,
                    "seed": seed
                }
            }
            
            if negative_prompt:
                payload["input"]["negative_prompt"] = negative_prompt
            
            if duration > 0:
                payload["input"]["duration"] = duration
            
            # Start prediction
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            prediction = response.json()
            
            prediction_id = prediction.get("id")
            status = prediction.get("status")
            
            # If using "Prefer: wait", we'd get result immediately
            # Otherwise, poll for completion
            if status == "succeeded":
                output = prediction.get("output")
                return self._format_success(output, prompt, prediction_id)
            
            # Poll for result
            get_url = f"{self.base_url}/{prediction_id}"
            max_attempts = 60  # 5 minutes max
            
            for _ in range(max_attempts):
                time.sleep(5)
                
                poll_response = requests.get(get_url, headers=headers, timeout=30)
                poll_response.raise_for_status()
                prediction = poll_response.json()
                
                status = prediction.get("status")
                
                if status == "succeeded":
                    output = prediction.get("output")
                    return self._format_success(output, prompt, prediction_id)
                elif status == "failed":
                    error = prediction.get("error", "Unknown error")
                    return Response(
                        message=f"❌ MMAudio generation failed: {error}",
                        break_loop=False
                    )
                elif status == "canceled":
                    return Response(
                        message="❌ MMAudio generation was canceled",
                        break_loop=False
                    )
                
                # Still processing, continue polling
                self.set_progress(f"Processing... Status: {status}")
            
            return Response(
                message=f"⏳ Generation timed out. Check prediction ID: `{prediction_id}`",
                break_loop=False
            )
            
        except requests.exceptions.RequestException as e:
            return Response(
                message=f"MMAudio API Error: {str(e)}",
                break_loop=False
            )

    def _format_success(self, output, prompt, prediction_id):
        """Format successful result."""
        if isinstance(output, str):
            audio_url = output
        elif isinstance(output, dict):
            audio_url = output.get("audio") or output.get("output") or str(output)
        else:
            audio_url = str(output)
        
        return Response(
            message=f"""✅ **Audio generated from video!**

- **Prediction ID:** `{prediction_id}`
- **Prompt:** {prompt}
- **Audio URL:** {audio_url}

The generated audio matches the video content based on your prompt.""",
            break_loop=False
        )
