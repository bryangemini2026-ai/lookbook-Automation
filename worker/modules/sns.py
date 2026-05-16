from PIL import Image, ImageDraw, ImageFont
import io


# Platform image specifications
PLATFORM_SPECS = {
    "instagram": {"width": 1080, "height": 1080},
    "instagram_portrait": {"width": 1080, "height": 1350},
    "tiktok":    {"width": 1080, "height": 1920},
    "twitter":   {"width": 1200, "height": 675},
}


class SNSModule:
    """Handles SNS platform formatting and branding."""

    def __init__(self, brand_dir: str = "/srv/lookbook/brand"):
        self.brand_dir = brand_dir

    def format_for_platform(self, image_bytes: bytes, platform: str) -> bytes:
        """Resize/crop image to platform specifications."""
        spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["instagram"])
        img = Image.open(io.BytesIO(image_bytes))

        # Center crop to target aspect ratio, then resize
        target_ratio = spec["width"] / spec["height"]
        w, h = img.size
        current_ratio = w / h

        if current_ratio > target_ratio:
            # Too wide — crop sides
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        elif current_ratio < target_ratio:
            # Too tall — crop top/bottom
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))

        img = img.resize((spec["width"], spec["height"]), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()

    def add_watermark(self, image_bytes: bytes, logo_filename: str = "logo.png",
                      position: str = "bottom-right", opacity: int = 128) -> bytes:
        """Add watermark/logo overlay to image."""
        import os
        logo_path = os.path.join(self.brand_dir, logo_filename)
        if not os.path.exists(logo_path):
            print(f"  Watermark: logo not found at {logo_path}, skipping")
            return image_bytes

        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")

        # Resize logo to ~15% of image width
        logo_w = int(img.width * 0.15)
        logo_h = int(logo.height * (logo_w / logo.width))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

        # Apply opacity
        logo.putalpha(Image.blend(logo.split()[3], Image.new("L", logo.size, 0), 1 - opacity / 255))

        # Calculate position
        padding = 20
        if position == "bottom-right":
            pos = (img.width - logo_w - padding, img.height - logo_h - padding)
        elif position == "bottom-left":
            pos = (padding, img.height - logo_h - padding)
        elif position == "top-right":
            pos = (img.width - logo_w - padding, padding)
        else:
            pos = (padding, padding)

        # Composite
        img.paste(logo, pos, logo)
        img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()

    def export_for_platforms(self, images: list[bytes], video_path: str | None,
                             platforms: list[str]) -> dict[str, bytes]:
        """Export images for multiple SNS platforms."""
        exports = {}
        for platform in platforms:
            for i, img in enumerate(images):
                formatted = self.format_for_platform(img, platform)
                exports[f"{platform}_{i:03d}.jpg"] = formatted
        return exports
