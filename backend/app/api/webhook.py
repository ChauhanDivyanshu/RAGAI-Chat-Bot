"""
WhatsApp Webhook Endpoint
Receives messages from WhatsApp and processes them
"""
import time
import hashlib
import hmac
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Optional

from app.config import settings
from app.utils import logger
from app.services.common.whatsapp import whatsapp

router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])

# Upload directory for WhatsApp media
WHATSAPP_UPLOAD_DIR = Path("./uploads/whatsapp")
WHATSAPP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/whatsapp", summary="WhatsApp webhook verification")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    WhatsApp webhook verification endpoint.
    Meta sends GET request to verify webhook URL.
    """
    logger.info(f"Webhook verification: mode={hub_mode}, token={hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning("Webhook verification failed - token mismatch")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp", summary="Receive WhatsApp messages")
async def receive_message(request: Request):
    """
    Receive incoming WhatsApp messages.
    
    Handles:
    - Text messages → Process via RAG
    - Documents (PDF, DOCX, etc.) → Upload to knowledge base
    - Images → OCR + Upload
    - Status updates (delivered, read) → Log
    """
    try:
        body = await request.json()
        logger.info(f"Webhook received: {body.get('object', 'unknown')}")
        
        # Process webhook data
        if body.get("object") != "whatsapp_business_account":
            return JSONResponse(content={"status": "ignored"})
        
        # Process entries
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Handle messages
                messages = value.get("messages", [])
                for message in messages:
                    await process_message(message, value)
                
                # Handle status updates
                statuses = value.get("statuses", [])
                for status in statuses:
                    logger.debug(f"Status update: {status.get('status')} for {status.get('id')}")
        
        return JSONResponse(content={"status": "received"})
        
    except Exception as e:
        logger.exception(f"Webhook processing failed: {e}")
        # Always return 200 to WhatsApp to avoid retries
        return JSONResponse(content={"status": "error", "message": str(e)})


async def process_message(message: dict, context: dict):
    """Process individual WhatsApp message"""
    try:
        msg_type = message.get("type")
        from_number = message.get("from")
        message_id = message.get("id")
        
        logger.info(f"Message from {from_number}: type={msg_type}")
        
        # Mark as read
        await whatsapp.mark_message_read(message_id)
        
        # Route by message type
        if msg_type == "text":
            await handle_text_message(message, from_number)
        
        elif msg_type == "document":
            await handle_document_message(message, from_number)
        
        elif msg_type == "image":
            await handle_image_message(message, from_number)
        
        elif msg_type == "audio" or msg_type == "voice":
            await whatsapp.send_text(
                from_number,
                "🎙️ Voice messages will be supported soon! Please send text or documents."
            )
        
        elif msg_type == "video":
            await whatsapp.send_text(
                from_number,
                "🎥 Video messages are not supported. Please send documents or images."
            )
        
        else:
            await whatsapp.send_text(
                from_number,
                f"Sorry, I don't support {msg_type} messages yet. Please send text or documents."
            )
            
    except Exception as e:
        logger.exception(f"Message processing failed: {e}")


async def handle_text_message(message: dict, from_number: str):
    """Handle text message - run RAG query"""
    try:
        text = message.get("text", {}).get("body", "").strip()
        
        if not text:
            return
        
        logger.info(f"Text query from {from_number}: {text[:100]}")
        
        # Handle special commands
        text_lower = text.lower()
        
        if text_lower in ["hi", "hello", "hey", "start", "/start", "namaste", "hii"]:
            welcome_msg = """👋 *Welcome to RAG Assistant!*

I can help you find information from your documents.

📤 *Send me:*
• PDF documents
• Word files (DOCX)
• Excel/CSV files
• Images (with text)
• Plain text files

💬 *Then ask me anything!*

Languages supported:
🇬🇧 English
🇮🇳 Hindi (हिंदी)
🇮🇳 Hinglish

Try sending: _"What is RAG?"_ or _"Help"_"""
            
            await whatsapp.send_text(from_number, welcome_msg)
            return
        
        if text_lower in ["help", "/help", "madad"]:
            help_msg = """*📚 How to use this bot:*

1️⃣ *Upload Documents:*
   Send any PDF, DOCX, Excel, image, or text file

2️⃣ *Ask Questions:*
   Type your question in English, Hindi, or Hinglish

3️⃣ *Get Answers:*
   I'll search through your documents and answer

*Commands:*
• `hi` - Welcome message
• `help` - This help
• `stats` - Your documents stats
• `clear` - Clear all your documents

*Examples:*
_"Summarize the document"_
_"What are the main points?"_
_"PDF mein kya likha hai?"_"""
            
            await whatsapp.send_text(from_number, help_msg)
            return
        
        if text_lower in ["stats", "/stats"]:
            from app.database import documents, chunks
            doc_count = await documents.count_documents()
            chunk_count = await chunks.count_chunks()
            
            stats_msg = f""" *System Stats*

📄 Total Documents: {doc_count}
🧩 Total Chunks: {chunk_count}

Send any document to add to knowledge base!"""
            
            await whatsapp.send_text(from_number, stats_msg)
            return
        
        # Send "processing" indicator
        await whatsapp.send_text(from_number, "⏳ Searching documents...")
        
        # Run RAG query
        from app.services.upload.embedder import embedder
        from app.services.query.llm_service import llm_service
        from app.database import chunks
        
        start_time = time.time()
        
        # Get embedding
        query_vector = embedder.embed_text(text)
        
        # Search
        retrieved_chunks = await chunks.vector_search(
            query_embedding=query_vector,
            top_k=3
        )
        
        if not retrieved_chunks:
            no_results_msg = llm_service._get_no_context_message(text)
            await whatsapp.send_text(from_number, f"❌ {no_results_msg}")
            return
        
        # Generate answer
        result = await llm_service.generate_answer(
            query=text,
            context_chunks=retrieved_chunks,
            temperature=0.1
        )
        
        elapsed = time.time() - start_time
        
        # Format response for WhatsApp
        answer = result['answer']
        sources_text = ""
        
        if result['sources']:
            sources_text = "\n\n📚 *Sources:*\n"
            for i, src in enumerate(result['sources'][:3], 1):
                doc_name = src['document_name']
                page = f" (Page {src['page_number']})" if src.get('page_number') else ""
                sources_text += f"{i}. {doc_name}{page}\n"
        
        full_response = f"{answer}{sources_text}\n\n⏱️ _{elapsed:.1f}s_"
        
        # Format for WhatsApp
        formatted = whatsapp.format_for_whatsapp(full_response)
        
        # Send response
        await whatsapp.send_text(from_number, formatted)
        
        logger.info(f"Replied to {from_number} in {elapsed:.1f}s")
        
    except Exception as e:
        logger.exception(f"Text handling failed: {e}")
        await whatsapp.send_text(
            from_number,
            "❌ Sorry, I encountered an error. Please try again."
        )


async def handle_document_message(message: dict, from_number: str):
    """Handle document message - process as upload"""
    try:
        doc = message.get("document", {})
        media_id = doc.get("id")
        filename = doc.get("filename", "document")
        mime_type = doc.get("mime_type", "")
        
        logger.info(f"Document from {from_number}: {filename} ({mime_type})")
        
        if not media_id:
            await whatsapp.send_text(from_number, "❌ Couldn't get document. Please try again.")
            return
        
        # Send processing message
        await whatsapp.send_text(
            from_number,
            f"📄 Processing *{filename}*...\nThis may take a moment."
        )
        
        # Download from WhatsApp
        content = await whatsapp.download_media(media_id)
        
        if not content:
            await whatsapp.send_text(from_number, "❌ Failed to download document.")
            return
        
        # Save and process via existing pipeline
        await process_uploaded_file(from_number, filename, content, mime_type)
        
    except Exception as e:
        logger.exception(f"Document handling failed: {e}")
        await whatsapp.send_text(from_number, f"❌ Error processing document: {str(e)}")


async def handle_image_message(message: dict, from_number: str):
    """Handle image - process with OCR"""
    try:
        img = message.get("image", {})
        media_id = img.get("id")
        mime_type = img.get("mime_type", "image/jpeg")
        caption = img.get("caption", "")
        
        logger.info(f"Image from {from_number}: caption={caption}")
        
        if not media_id:
            await whatsapp.send_text(from_number, "❌ Couldn't get image. Please try again.")
            return
        
        # Send processing message
        await whatsapp.send_text(
            from_number,
            "🖼️ Processing image with OCR...\nThis may take 30-60 seconds."
        )
        
        # Download
        content = await whatsapp.download_media(media_id)
        
        if not content:
            await whatsapp.send_text(from_number, "❌ Failed to download image.")
            return
        
        # Determine extension
        ext = "jpg" if "jpeg" in mime_type else "png"
        filename = f"whatsapp_image_{int(time.time())}.{ext}"
        
        # Process
        await process_uploaded_file(from_number, filename, content, mime_type)
        
        # If caption provided, also run as query
        if caption and len(caption) > 3:
            await whatsapp.send_text(from_number, f"💭 Now answering: _{caption}_")
            
            # Wait a sec for indexing
            import asyncio
            await asyncio.sleep(2)
            
            # Run query on the new content
            fake_message = {"text": {"body": caption}}
            await handle_text_message(fake_message, from_number)
            
    except Exception as e:
        logger.exception(f"Image handling failed: {e}")
        await whatsapp.send_text(from_number, f"❌ Error processing image: {str(e)}")


async def process_uploaded_file(from_number: str, filename: str, content: bytes, mime_type: str):
    """Common file processing pipeline"""
    try:
        from app.services.upload.file_detector import file_detector
        from app.services.upload.document_processor import document_processor
        from app.services.upload.embedder import embedder
        from app.database import documents, chunks
        from app.utils import generate_file_hash, format_file_size, word_count
        from app.services.upload.chunker import chunker
        
        file_size = len(content)
        
        # Detect type
        detection = file_detector.detect(filename, content, mime_type)
        file_type = detection['file_type']
        
        # Check duplicate
        file_hash = generate_file_hash(content)
        existing = await documents.get_by_hash(file_hash)
        
        if existing:
            await whatsapp.send_text(
                from_number,
                f" Already in knowledge base!\n _{existing['original_name']}_\n\nAsk me anything about it!"
            )
            return
        
        # Save file
        file_path = WHATSAPP_UPLOAD_DIR / f"{file_hash}.{detection['extension']}"
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Extract content
        extraction = document_processor.process(str(file_path), file_type)
        
        if not extraction['full_text'] or len(extraction['full_text'].strip()) < 10:
            await whatsapp.send_text(
                from_number,
                " Couldn't extract text from this file. Try a different file."
            )
            return
        
        # Create document
        doc_id = await documents.create_document(
            original_name=filename,
            file_type=file_type,
            mime_type=detection['mime_type'],
            file_size=file_size,
            file_hash=file_hash,
            page_count=extraction['total_pages'],
            word_count=word_count(extraction['full_text']),
            status="processing"
        )
        
        # Chunk
        if extraction.get('pages') and extraction.get('has_pages'):
            text_chunks = chunker.chunk_pages(extraction['pages'])
        else:
            text_chunks = chunker.chunk_text(extraction['full_text'])
            for i, c in enumerate(text_chunks):
                c['chunk_index'] = i
        
        # Embed
        texts = [c['content'] for c in text_chunks]
        embeddings = embedder.embed_batch(texts)
        
        # Save
        saved = await chunks.insert_chunks_batch(doc_id, text_chunks, embeddings)
        await documents.update_status(doc_id, "completed")
        
        # Send success message
        success_msg = f""" *Document Processed!*

 *{filename}*
 Size: {format_file_size(file_size)}
 Pages: {extraction['total_pages']}
 Chunks: {saved}
 Words: {word_count(extraction['full_text'])}

💬 Now you can ask me anything about this document!

Example:
_"Summarize this document"_
_"What are the key points?"_"""
        
        await whatsapp.send_text(from_number, success_msg)
        
    except Exception as e:
        logger.exception(f"File processing failed: {e}")
        await whatsapp.send_text(
            from_number,
            f"❌ Failed to process file: {str(e)}"
        )
