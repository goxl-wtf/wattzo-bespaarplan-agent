"""
Supabase storage implementation for bespaarplan files
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

class SupabaseStorage:
    """Handle Supabase storage operations for bespaarplan files."""
    
    def __init__(self):
        self.project_url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.bucket_name = os.getenv("BUCKET_NAME", "bespaarplan-reports")
        
        if not self.project_url or not self.anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        # Remove trailing slash from project URL
        self.project_url = self.project_url.rstrip('/')
        
    async def upload_bespaarplan(self, deal_id: str, html_content: str) -> Dict[str, Any]:
        """
        Upload bespaarplan HTML to Supabase storage.
        
        Args:
            deal_id: The deal ID
            html_content: The HTML content to upload
            
        Returns:
            Dict with upload details including public URL
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"deal-{deal_id}/bespaarplan-{timestamp}.html"
        
        # Prepare the upload URL
        upload_url = f"{self.project_url}/storage/v1/object/{self.bucket_name}/{filename}"
        
        # Headers for authentication
        headers = {
            "Authorization": f"Bearer {self.anon_key}",
            "Content-Type": "text/html",
            "x-upsert": "true"  # Create folders if they don't exist
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Upload the file
                response = await client.post(
                    upload_url,
                    content=html_content.encode('utf-8'),
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Upload failed: {response.status_code} - {response.text}")
                    raise Exception(f"Upload failed with status {response.status_code}")
                
                # Get the public URL
                public_url = f"{self.project_url}/storage/v1/object/public/{self.bucket_name}/{filename}"
                
                logger.info(f"Successfully uploaded bespaarplan for deal {deal_id}")
                
                return {
                    "success": True,
                    "filename": filename,
                    "public_url": public_url,
                    "uploaded_at": datetime.now().isoformat(),
                    "size_bytes": len(html_content.encode('utf-8'))
                }
                
        except Exception as e:
            logger.error(f"Failed to upload bespaarplan for deal {deal_id}: {str(e)}")
            raise
    
    async def update_deal_record(self, deal_id: str, bespaarplan_url: str) -> bool:
        """
        Update the deals table with bespaarplan information.
        
        Args:
            deal_id: The deal ID to update
            bespaarplan_url: The public URL of the uploaded bespaarplan
            
        Returns:
            True if successful, False otherwise
        """
        update_url = f"{self.project_url}/rest/v1/deals"
        
        headers = {
            "Authorization": f"Bearer {self.anon_key}",
            "apikey": self.anon_key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        # Update data
        data = {
            "bespaarplan_url": bespaarplan_url,
            "bespaarplan_generated_at": datetime.now().isoformat(),
            "bespaarplan_status": "completed"
        }
        
        # Add filter for the specific deal
        params = {
            "id": f"eq.{deal_id}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    update_url,
                    json=data,
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 204:  # No content, successful update
                    logger.info(f"Successfully updated deal record for {deal_id}")
                    return True
                else:
                    logger.error(f"Failed to update deal: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update deal record for {deal_id}: {str(e)}")
            return False
    
    async def get_bespaarplan_url(self, deal_id: str) -> Optional[str]:
        """
        Get the bespaarplan URL for a deal from the database.
        
        Args:
            deal_id: The deal ID to look up
            
        Returns:
            The bespaarplan URL if found, None otherwise
        """
        query_url = f"{self.project_url}/rest/v1/deals"
        
        headers = {
            "Authorization": f"Bearer {self.anon_key}",
            "apikey": self.anon_key
        }
        
        params = {
            "id": f"eq.{deal_id}",
            "select": "bespaarplan_url,bespaarplan_status,bespaarplan_generated_at"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    query_url,
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        return data[0].get("bespaarplan_url")
                    
                return None
                
        except Exception as e:
            logger.error(f"Failed to get bespaarplan URL for deal {deal_id}: {str(e)}")
            return None


# Singleton instance
storage = SupabaseStorage()


async def upload_and_store_bespaarplan(deal_id: str, html_content: str) -> Dict[str, Any]:
    """
    Upload bespaarplan to Supabase and update the database.
    
    This is the main function called by the storage_manager agent.
    """
    try:
        # Upload to storage bucket
        upload_result = await storage.upload_bespaarplan(deal_id, html_content)
        
        if upload_result["success"]:
            # Update the deals table
            update_success = await storage.update_deal_record(
                deal_id, 
                upload_result["public_url"]
            )
            
            if update_success:
                return {
                    "success": True,
                    "deal_id": deal_id,
                    "bespaarplan_url": upload_result["public_url"],
                    "filename": upload_result["filename"],
                    "uploaded_at": upload_result["uploaded_at"]
                }
            else:
                # Upload succeeded but database update failed
                logger.warning(f"Upload succeeded but database update failed for deal {deal_id}")
                return {
                    "success": True,
                    "deal_id": deal_id,
                    "bespaarplan_url": upload_result["public_url"],
                    "filename": upload_result["filename"],
                    "uploaded_at": upload_result["uploaded_at"],
                    "warning": "Database update failed"
                }
        else:
            return {
                "success": False,
                "deal_id": deal_id,
                "error": "Upload failed"
            }
            
    except Exception as e:
        logger.error(f"Failed to upload and store bespaarplan for deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "deal_id": deal_id,
            "error": str(e)
        }