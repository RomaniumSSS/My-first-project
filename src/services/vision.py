import base64
import io
from typing import List, Dict, Any

from aiogram import Bot


async def download_telegram_photo(bot: Bot, file_id: str) -> io.BytesIO:
    """
    Downloads a photo from Telegram and returns it as BytesIO.
    """
    file = await bot.get_file(file_id)

    # Create a BytesIO object to hold the file
    output = io.BytesIO()
    # Download the file to the BytesIO object
    await bot.download(file, output)
    # Reset cursor to start of file
    output.seek(0)
    return output


def encode_image_to_base64(image_data: io.BytesIO) -> str:
    """Converts BytesIO image data to base64 string."""
    return base64.b64encode(image_data.read()).decode("utf-8")


def prepare_vision_payload(text: str, base64_images: List[str]) -> List[Dict[str, Any]]:
    """
    Prepares the message payload for GPT Vision.
    Structure:
    [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "description"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,..."}
                }
            ]
        }
    ]
    """
    content: List[Dict[str, Any]] = [{"type": "text", "text": text}]

    for img_b64 in base64_images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
            }
        )

    return [{"role": "user", "content": content}]
