"""
Image Compositor Tool for Pareng Boyong
Composites/overlays images (like logos) onto base images
This ACTUALLY uses the real image files, not AI generation
"""

import os
import io
import base64
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from python.helpers.tool import Tool, Response


class ImageCompositor(Tool):
    """
    Composite/overlay images together programmatically.
    This tool ACTUALLY uses the real image files - no AI hallucination.
    
    Use this when you need to:
    - Overlay a logo onto a background/banner
    - Combine multiple images
    - Add watermarks
    - Resize or position images precisely
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = "/a0/tmp/composited"
        os.makedirs(self.output_dir, exist_ok=True)

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "overlay").lower()
        
        if action == "overlay":
            return await self.overlay_image()
        elif action == "resize":
            return await self.resize_image()
        elif action == "info":
            return await self.get_image_info()
        else:
            return Response(
                message="""**Image Compositor Actions:**

- `overlay` - Overlay one image onto another (logo on banner)
  - base_image: Path/URL of background image
  - overlay_image: Path/URL of image to overlay (e.g., logo)
  - position: Where to place overlay (top-left, top-right, bottom-left, bottom-right, center)
  - scale: Scale factor for overlay (0.1 to 1.0, default 0.2)
  - padding: Pixels from edge (default 20)
  
- `resize` - Resize an image
  - image: Path/URL of image
  - width: Target width (optional)
  - height: Target height (optional)
  - maintain_aspect: Keep aspect ratio (default true)
  
- `info` - Get image dimensions and info
  - image: Path/URL of image

**Example:**
```
image_compositor action=overlay base_image=/a0/tmp/banner.png overlay_image=/root/platapay_logo.png position=top-left scale=0.15
```""",
                break_loop=False
            )

    def _load_image(self, path_or_url: str) -> Image.Image:
        """Load image from local path or URL."""
        if path_or_url.startswith(("http://", "https://")):
            response = requests.get(path_or_url, timeout=30)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        else:
            # Handle various path formats
            path = path_or_url
            if not os.path.isabs(path):
                path = os.path.join("/a0", path)
            
            # Try common locations
            paths_to_try = [
                path,
                path_or_url,
                f"/a0/{path_or_url}",
                f"/root/{path_or_url}",
                f"/a0/tmp/{path_or_url}",
            ]
            
            for p in paths_to_try:
                if os.path.exists(p):
                    return Image.open(p)
            
            raise FileNotFoundError(f"Image not found: {path_or_url}")

    async def overlay_image(self) -> Response:
        """Overlay one image onto another."""
        base_path = self.args.get("base_image", "")
        overlay_path = self.args.get("overlay_image", "")
        position = self.args.get("position", "top-left").lower()
        scale = float(self.args.get("scale", 0.2))
        padding = int(self.args.get("padding", 20))
        opacity = float(self.args.get("opacity", 1.0))
        
        if not base_path or not overlay_path:
            return Response(
                message="Error: Both base_image and overlay_image are required",
                break_loop=False
            )
        
        try:
            # Load images
            self.log.update(progress="Loading base image...")
            base = self._load_image(base_path).convert("RGBA")
            
            self.log.update(progress="Loading overlay image...")
            overlay = self._load_image(overlay_path).convert("RGBA")
            
            # Scale overlay
            new_width = int(base.width * scale)
            aspect = overlay.height / overlay.width
            new_height = int(new_width * aspect)
            overlay = overlay.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Apply opacity if needed
            if opacity < 1.0:
                alpha = overlay.split()[3]
                alpha = alpha.point(lambda p: int(p * opacity))
                overlay.putalpha(alpha)
            
            # Calculate position
            positions = {
                "top-left": (padding, padding),
                "top-right": (base.width - overlay.width - padding, padding),
                "bottom-left": (padding, base.height - overlay.height - padding),
                "bottom-right": (base.width - overlay.width - padding, base.height - overlay.height - padding),
                "center": ((base.width - overlay.width) // 2, (base.height - overlay.height) // 2),
                "top-center": ((base.width - overlay.width) // 2, padding),
                "bottom-center": ((base.width - overlay.width) // 2, base.height - overlay.height - padding),
            }
            
            x, y = positions.get(position, positions["top-left"])
            
            # Handle custom x,y
            if self.args.get("x"):
                x = int(self.args.get("x"))
            if self.args.get("y"):
                y = int(self.args.get("y"))
            
            # Composite
            self.log.update(progress="Compositing images...")
            result = base.copy()
            result.paste(overlay, (x, y), overlay)
            
            # Save result
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"composited_{timestamp}.png"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Convert to RGB if saving as JPEG
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                result = result.convert("RGB")
            
            result.save(output_path, quality=95)
            
            return Response(
                message=f"""✅ **Image Composited Successfully!**

**Base Image:** {base_path}
**Overlay Image:** {overlay_path}
**Position:** {position}
**Scale:** {scale} ({new_width}x{new_height} px)

**Output:** {output_path}

The overlay image (logo) has been placed on the base image using the ACTUAL image file - not AI-generated!

To view or use this image, reference: `{output_path}`""",
                break_loop=False
            )
            
        except FileNotFoundError as e:
            return Response(message=f"Error: {str(e)}", break_loop=False)
        except Exception as e:
            return Response(message=f"Compositing error: {str(e)}", break_loop=False)

    async def resize_image(self) -> Response:
        """Resize an image."""
        image_path = self.args.get("image", "")
        width = self.args.get("width")
        height = self.args.get("height")
        maintain_aspect = self.args.get("maintain_aspect", True)
        
        if not image_path:
            return Response(message="Error: image path is required", break_loop=False)
        
        if not width and not height:
            return Response(message="Error: Either width or height is required", break_loop=False)
        
        try:
            img = self._load_image(image_path)
            original_size = img.size
            
            if width and height and not maintain_aspect:
                new_size = (int(width), int(height))
            elif width:
                w = int(width)
                h = int(w * img.height / img.width)
                new_size = (w, h)
            else:
                h = int(height)
                w = int(h * img.width / img.height)
                new_size = (w, h)
            
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"resized_{timestamp}.png")
            resized.save(output_path, quality=95)
            
            return Response(
                message=f"""✅ **Image Resized!**

**Original:** {original_size[0]}x{original_size[1]}
**New Size:** {new_size[0]}x{new_size[1]}
**Output:** {output_path}""",
                break_loop=False
            )
            
        except Exception as e:
            return Response(message=f"Resize error: {str(e)}", break_loop=False)

    async def get_image_info(self) -> Response:
        """Get information about an image."""
        image_path = self.args.get("image", "")
        
        if not image_path:
            return Response(message="Error: image path is required", break_loop=False)
        
        try:
            img = self._load_image(image_path)
            
            info = f"""📷 **Image Information**

**Path:** {image_path}
**Dimensions:** {img.width} x {img.height} pixels
**Mode:** {img.mode}
**Format:** {img.format or 'Unknown'}
"""
            
            if hasattr(img, 'info'):
                if 'dpi' in img.info:
                    info += f"**DPI:** {img.info['dpi']}\n"
            
            return Response(message=info, break_loop=False)
            
        except Exception as e:
            return Response(message=f"Error: {str(e)}", break_loop=False)
