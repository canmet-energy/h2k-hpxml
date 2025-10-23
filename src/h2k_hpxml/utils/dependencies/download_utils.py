#!/usr/bin/env python3
"""
Download utilities for dependency management.

Provides file download functionality with progress indicators,
resume capability, and retry logic.
"""

import locale
import os
import platform
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import click


def download_file(url, dest_path, desc="", max_retries=3):
    """Download file with progress indicator, resume capability, and retry logic."""
    print(f"Downloading {desc or url}...")

    # Create SSL context that doesn't verify certificates (for corporate networks)
    # In production, you might want to make this configurable
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    dest_path = Path(dest_path)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    for attempt in range(max_retries + 1):
        try:
            # Check if we have a partial download to resume
            resume_byte_pos = 0
            if temp_path.exists():
                resume_byte_pos = temp_path.stat().st_size
                if resume_byte_pos > 0:
                    print(f"  Resuming download from {resume_byte_pos:,} bytes...")

            # Create request with Range header for resume
            req = urllib.request.Request(url)
            if resume_byte_pos > 0:
                req.add_header("Range", f"bytes={resume_byte_pos}-")

            # Create opener with SSL context
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))

            with opener.open(req) as response:
                # Get total file size
                content_range = response.headers.get("Content-Range")
                if content_range and resume_byte_pos > 0:
                    # Format: "bytes start-end/total"
                    total_size = int(content_range.split("/")[-1])
                else:
                    total_size = int(response.headers.get("Content-Length", 0))
                    if resume_byte_pos > 0:
                        total_size += resume_byte_pos

                # Open file in append mode if resuming, otherwise write mode
                mode = "ab" if resume_byte_pos > 0 else "wb"

                with open(temp_path, mode) as f:
                    downloaded = resume_byte_pos
                    chunk_size = 8192

                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        # Show progress
                        if total_size > 0:
                            percent = min(downloaded * 100 / total_size, 100)
                            print(f"  Progress: {percent:.1f}%", end="\r")

            # Download completed successfully - move temp file to final location
            if dest_path.exists():
                dest_path.unlink()
            temp_path.rename(dest_path)
            print(f"\n  ✓ Downloaded to {dest_path}")
            return True

        except (urllib.error.URLError, OSError, IOError) as e:
            if attempt < max_retries:
                print(f"\n  ⚠ Download failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                print(f"  Retrying in {2 ** attempt} seconds...")
                time.sleep(2**attempt)  # Exponential backoff
            else:
                print(f"\n  ✗ Download failed after {max_retries + 1} attempts: {e}")
                # Clean up temp file on final failure
                if temp_path.exists():
                    temp_path.unlink()
                return False

    return False


def safe_echo(message, **kwargs):
    """Echo with Unicode character replacement for Windows compatibility."""
    if isinstance(message, str):
        # Replace common Unicode characters with ASCII equivalents
        replacements = {
            "✅": "[OK]",
            "✓": "[OK]",
            "❌": "[ERROR]",
            "✗": "[ERROR]",
            "⚠️": "[WARNING]",
            "⚠": "[WARNING]",
            "🔍": "[SEARCH]",
            "🔄": "[PROCESSING]",
            "📥": "[DOWNLOAD]",
            "🎉": "[SUCCESS]",
            "🏠": "[HOUSE]",
            "🔧": "[TOOL]",
            "📋": "[LIST]",
            "🗑️": "[DELETE]",
            "🪟": "[WINDOWS]",
            "⏳": "[WAIT]",
            "ℹ️": "[INFO]",
        }
        for unicode_char, ascii_equiv in replacements.items():
            message = message.replace(unicode_char, ascii_equiv)
    return click.echo(message, **kwargs)


# Configure click for Unicode support on Windows
if platform.system() == "Windows":
    # Get the system's preferred encoding
    preferred_encoding = locale.getpreferredencoding()

    # If we're using a limited encoding, try to use UTF-8
    if preferred_encoding.lower() in ["cp1252", "windows-1252", "charmap"]:
        try:
            # Try to use UTF-8 for output
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            # Store original echo and replace with safe version
            if not hasattr(click, "original_echo"):
                click.original_echo = click.echo
                click.echo = safe_echo
