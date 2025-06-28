#!/usr/bin/env python3
"""
Supabase Storage MCP Server
Provides tools for uploading bespaarplan files and managing deal records
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import httpx
from pathlib import Path

from fastmcp import FastMCP
from supabase import create_client, Client

# Initialize MCP server
mcp = FastMCP("SupabaseStorage")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Demo mode flag
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
BUCKET_NAME = os.getenv("BUCKET_NAME", "bespaarplan-reports")

if not DEMO_MODE and (not SUPABASE_URL or not SUPABASE_KEY):
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set when DEMO_MODE=false")

supabase: Optional[Client] = None
if not DEMO_MODE:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Remove trailing slash from project URL
SUPABASE_URL = SUPABASE_URL.rstrip('/')


# Demo storage for testing
DEMO_STORAGE = {}


async def upload_to_storage(file_path: str, content: bytes, content_type: str = "text/html") -> Dict[str, Any]:
    """Upload file to Supabase storage using REST API"""
    if DEMO_MODE:
        # Store in memory for demo
        DEMO_STORAGE[file_path] = {
            "content": content,
            "content_type": content_type,
            "uploaded_at": datetime.now().isoformat()
        }
        return {
            "success": True,
            "path": file_path,
            "size": len(content)
        }
    
    # Real Supabase upload
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_path}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true"  # Create folders if they don't exist
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            upload_url,
            content=content,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code not in [200, 201]:
            logger.error(f"Upload failed: {response.status_code} - {response.text}")
            raise Exception(f"Upload failed with status {response.status_code}")
        
        return {
            "success": True,
            "path": file_path,
            "size": len(content)
        }


def update_deal_in_db(deal_id: str, data: Dict[str, Any]) -> bool:
    """Update deal record in database"""
    if DEMO_MODE:
        logger.info(f"Demo mode: Would update deal {deal_id} with {data}")
        return True
    
    try:
        # Update deal record
        response = supabase.table('deals') \
            .update(data) \
            .eq('id', deal_id) \
            .execute()
        
        return True
    except Exception as e:
        logger.error(f"Failed to update deal {deal_id}: {str(e)}")
        return False


def get_deal_info(deal_id: str) -> Optional[Dict[str, Any]]:
    """Get deal information from database"""
    if DEMO_MODE:
        # Return demo data
        return {
            "id": deal_id,
            "customer_last_name": "Jodhabier",
            "bespaarplan_url": None,
            "bespaarplan_status": None
        }
    
    try:
        response = supabase.table('deals') \
            .select('id, bespaarplan_url, bespaarplan_status, bespaarplan_generated_at, contacts!inner(last_name)') \
            .eq('id', deal_id) \
            .single() \
            .execute()
        
        if response.data:
            # Flatten the response to include customer_last_name at the top level
            deal_data = response.data
            deal_data['customer_last_name'] = deal_data.get('contacts', {}).get('last_name')
            # Remove the nested contacts object to keep the response clean
            if 'contacts' in deal_data:
                del deal_data['contacts']
            return deal_data
        return None
    except Exception as e:
        logger.error(f"Failed to get deal {deal_id}: {str(e)}")
        return None


@mcp.tool()
async def upload_html_file(deal_id: str, html_content: str, customer_last_name: str) -> Dict[str, Any]:
    """
    Upload bespaarplan HTML file to Supabase storage.
    
    Args:
        deal_id: The deal ID
        html_content: The HTML content to upload
        customer_last_name: Customer's last name for folder structure
    
    Returns:
        Dict with upload details including public URL
    """
    try:
        # Create file path: {last_name}-{deal_id}/bespaarplan-{deal_id}.html
        folder_name = f"{customer_last_name.lower()}-{deal_id}"
        filename = f"bespaarplan-{deal_id}.html"
        file_path = f"{folder_name}/{filename}"
        
        # Upload to storage
        content_bytes = html_content.encode('utf-8')
        upload_result = await upload_to_storage(file_path, content_bytes)
        
        if upload_result["success"]:
            # Generate public URL
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path}"
            
            logger.info(f"Successfully uploaded bespaarplan for deal {deal_id}")
            
            return {
                "success": True,
                "deal_id": deal_id,
                "file_path": file_path,
                "public_url": public_url,
                "filename": filename,
                "size_kb": len(content_bytes) / 1024,
                "uploaded_at": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Upload failed"
            }
            
    except Exception as e:
        logger.error(f"Failed to upload HTML for deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_public_url(file_path: str) -> Dict[str, Any]:
    """
    Get the public CDN URL for a file in storage.
    
    Args:
        file_path: The file path in storage
    
    Returns:
        Dict with public URL
    """
    try:
        if DEMO_MODE and file_path not in DEMO_STORAGE:
            return {
                "success": False,
                "error": "File not found in demo storage"
            }
        
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path}"
        
        return {
            "success": True,
            "public_url": public_url,
            "file_path": file_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def list_deal_files(deal_id: str) -> Dict[str, Any]:
    """
    List all files for a specific deal.
    
    Args:
        deal_id: The deal ID to list files for
    
    Returns:
        Dict with list of files
    """
    try:
        if DEMO_MODE:
            # Return demo files
            demo_files = []
            for path in DEMO_STORAGE.keys():
                if deal_id in path:
                    demo_files.append({
                        "name": path.split('/')[-1],
                        "path": path,
                        "size": len(DEMO_STORAGE[path]["content"]),
                        "uploaded_at": DEMO_STORAGE[path]["uploaded_at"]
                    })
            
            return {
                "success": True,
                "files": demo_files,
                "count": len(demo_files)
            }
        
        # Real Supabase list
        list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
        
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        
        # Search for files in folders containing the deal_id
        params = {
            "prefix": "",  # Search all folders
            "limit": 100
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                list_url,
                headers=headers,
                json=params,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"List failed with status {response.status_code}")
            
            all_files = response.json()
            
            # Filter files related to this deal
            deal_files = []
            for file in all_files:
                if deal_id in file.get("name", ""):
                    deal_files.append({
                        "name": file["name"],
                        "path": file["name"],
                        "size": file.get("metadata", {}).get("size", 0),
                        "uploaded_at": file.get("created_at", "")
                    })
            
            return {
                "success": True,
                "files": deal_files,
                "count": len(deal_files)
            }
            
    except Exception as e:
        logger.error(f"Failed to list files for deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "files": [],
            "count": 0
        }


@mcp.tool()
def update_deal_bespaarplan(deal_id: str, bespaarplan_url: str) -> Dict[str, Any]:
    """
    Update deal record with bespaarplan information.
    
    Args:
        deal_id: The deal ID to update
        bespaarplan_url: The public URL of the uploaded bespaarplan
    
    Returns:
        Dict with update status
    """
    try:
        # Prepare update data
        update_data = {
            "bespaarplan_url": bespaarplan_url,
            "bespaarplan_generated_at": datetime.now().isoformat(),
            "bespaarplan_status": "completed"
        }
        
        # Update database
        success = update_deal_in_db(deal_id, update_data)
        
        if success:
            logger.info(f"Successfully updated deal record for {deal_id}")
            return {
                "success": True,
                "deal_id": deal_id,
                "updated_fields": list(update_data.keys()),
                "updated_at": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Database update failed"
            }
            
    except Exception as e:
        logger.error(f"Failed to update deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_deal_bespaarplan_status(deal_id: str) -> Dict[str, Any]:
    """
    Check if a bespaarplan exists for a deal.
    
    Args:
        deal_id: The deal ID to check
    
    Returns:
        Dict with bespaarplan status and URL if exists
    """
    try:
        deal_info = get_deal_info(deal_id)
        
        if not deal_info:
            return {
                "success": False,
                "error": "Deal not found"
            }
        
        has_bespaarplan = bool(deal_info.get("bespaarplan_url"))
        
        return {
            "success": True,
            "deal_id": deal_id,
            "has_bespaarplan": has_bespaarplan,
            "bespaarplan_url": deal_info.get("bespaarplan_url"),
            "bespaarplan_status": deal_info.get("bespaarplan_status"),
            "generated_at": deal_info.get("bespaarplan_generated_at"),
            "customer_last_name": deal_info.get("customer_last_name")
        }
        
    except Exception as e:
        logger.error(f"Failed to get bespaarplan status for deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()