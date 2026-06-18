"""
WhatsApp Business API Client
Sends and receives messages via Meta WhatsApp Business API
"""
import httpx
import asyncio
from typing import Dict, Optional, List
from app.config import settings
from app.utils import logger


class WhatsAppClient:
    """WhatsApp Business API client"""
    
    def __init__(self):
        self.token = settings.WHATSAPP_TOKEN
        self.phone_id = settings.WHATSAPP_PHONE_ID
        self.api_version = settings.WHATSAPP_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_id}"
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def send_text(self, to_number: str, message: str) -> Dict:
        """
        Send text message to WhatsApp number.
        
        Args:
            to_number: Recipient phone number (e.g., '919876543210')
            message: Text message (max 4096 chars)
            
        Returns:
            API response
        """
        # WhatsApp has 4096 char limit
        if len(message) > 4000:
            message = message[:3990] + "...\n\n[Message truncated]"
        
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Message sent to {to_number}: {message[:50]}...")
                    return {"success": True, "data": result}
                else:
                    logger.error(f"WhatsApp send failed: {response.status_code} - {response.text}")
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"WhatsApp send exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_typing_indicator(self, to_number: str) -> Dict:
        """Show typing indicator to user (improves UX)"""
        # Note: WhatsApp doesn't have official typing indicator API
        # We'll use a quick "..." message that gets edited
        return await self.send_text(to_number, "⏳ Processing...")
    
    async def mark_message_read(self, message_id: str) -> Dict:
        """Mark message as read (blue ticks)"""
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                return {"success": response.status_code == 200}
        except Exception as e:
            logger.warning(f"Mark read failed: {e}")
            return {"success": False}
    
    async def download_media(self, media_id: str) -> Optional[bytes]:
        """
        Download media file from WhatsApp.
        
        Returns:
            File bytes or None if failed
        """
        try:
            # Step 1: Get media URL
            url = f"https://graph.facebook.com/{self.api_version}/{media_id}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Get media metadata
                response = await client.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    logger.error(f"Failed to get media URL: {response.text}")
                    return None
                
                media_data = response.json()
                media_url = media_data.get("url")
                
                if not media_url:
                    logger.error("No URL in media response")
                    return None
                
                # Step 2: Download actual file
                file_response = await client.get(
                    media_url,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if file_response.status_code == 200:
                    logger.info(f"Downloaded media {media_id}: {len(file_response.content)} bytes")
                    return file_response.content
                else:
                    logger.error(f"Media download failed: {file_response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Media download exception: {e}")
            return None
    
    async def send_template(self, to_number: str, template_name: str, language: str = "en_US") -> Dict:
        """Send pre-approved template message (for initial contact)"""
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language}
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def format_for_whatsapp(self, text: str) -> str:
        """
        Format text for WhatsApp display.
        WhatsApp supports limited markdown:
        - *bold*
        - _italic_
        - ~strikethrough~
        - ```code```
        """
        # WhatsApp uses different syntax
        # Convert common markdown
        formatted = text
        
        # Headers to bold
        formatted = formatted.replace('### ', '*')
        formatted = formatted.replace('## ', '*')
        formatted = formatted.replace('# ', '*')
        
        # Ensure proper line breaks
        formatted = formatted.replace('\n\n\n', '\n\n')
        
        return formatted.strip()


# Global instance
whatsapp = WhatsAppClient()
