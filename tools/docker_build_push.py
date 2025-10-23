#!/usr/bin/env python3
"""
Cross-platform script to build and push Docker image to Docker Hub.
Tags the image with the current Git branch name.

Usage:
    python build_and_push.py [options]

Requirements:
    - Docker must be installed and running
    - Git must be installed
    - Must be logged into Docker Hub (docker login)

Examples:
    python build_and_push.py
    python build_and_push.py --dry-run
    python build_and_push.py --repo myuser/myimage
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and return the result."""
    print(f"🔧 Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")

    try:
        if capture_output:
            result = subprocess.run(
                cmd, shell=isinstance(cmd, str), check=check, capture_output=True, text=True
            )
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=isinstance(cmd, str), check=check)
            return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if capture_output and e.stdout:
            print(f"   stdout: {e.stdout.strip()}")
        if capture_output and e.stderr:
            print(f"   stderr: {e.stderr.strip()}")
        sys.exit(1)


def get_git_branch():
    """Get the current Git branch name and sanitize it for Docker tag."""
    try:
        branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
        # Sanitize branch name for Docker tag (replace invalid characters with hyphens)
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "-", branch)
        return sanitized
    except Exception:
        print("❌ Failed to get Git branch. Are you in a Git repository?")
        sys.exit(1)


def check_docker():
    """Check if Docker is available and running."""
    try:
        run_command(["docker", "version"], capture_output=True)
        print("✅ Docker is available and running")
    except Exception:
        print("❌ Docker is not available or not running")
        print("   Please install Docker and ensure it's running")
        sys.exit(1)


def check_git():
    """Check if Git is available."""
    try:
        run_command(["git", "--version"], capture_output=True)
        print("✅ Git is available")
    except Exception:
        print("❌ Git is not available")
        print("   Please install Git")
        sys.exit(1)


def find_dockerfile():
    """Find the Dockerfile in the current directory or parent directories."""
    current_dir = Path.cwd()

    # Check current directory first
    dockerfile_path = current_dir / "Dockerfile"
    if dockerfile_path.exists():
        return dockerfile_path

    # Check parent directories up to 3 levels
    for parent in current_dir.parents[:3]:
        dockerfile_path = parent / "Dockerfile"
        if dockerfile_path.exists():
            return dockerfile_path

    print("❌ Dockerfile not found in current directory or parent directories")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Build and push Docker image with Git branch as tag",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--repo",
        default="canmet/h2k-hpxml",
        help="Docker repository name (default: canmet/h2k-hpxml)",
    )

    parser.add_argument("--dockerfile", help="Path to Dockerfile (default: auto-detect)")

    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without actually doing it"
    )

    parser.add_argument(
        "--latest", action="store_true", help="Also tag as 'latest' if on main/master branch"
    )

    args = parser.parse_args()

    print("🐳 H2K-HPXML Docker Build and Push Script")
    print("=" * 50)

    # Check prerequisites
    check_docker()
    check_git()

    # Get branch and dockerfile
    branch = get_git_branch()
    dockerfile_path = Path(args.dockerfile) if args.dockerfile else find_dockerfile()

    # Prepare tags
    primary_tag = f"{args.repo}:{branch}"
    tags = [primary_tag]

    # Add latest tag if on main/master branch
    if args.latest and branch.lower() in ["main", "master"]:
        latest_tag = f"{args.repo}:latest"
        tags.append(latest_tag)

    print(f"📁 Dockerfile: {dockerfile_path}")
    print(f"🌿 Git branch: {branch}")
    print(f"🏷️  Docker tags: {', '.join(tags)}")

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - Commands that would be executed:")
        print(f"   docker build -t {primary_tag} -f {dockerfile_path} {dockerfile_path.parent}")
        for tag in tags:
            print(f"   docker push {tag}")
        return

    # Build the image
    print(f"\n🔨 Building Docker image...")
    build_cmd = [
        "docker",
        "build",
        "-t",
        primary_tag,
        "-f",
        str(dockerfile_path),
        str(dockerfile_path.parent),
    ]
    run_command(build_cmd)

    # Tag additional tags
    for tag in tags[1:]:  # Skip the first tag as it's already applied
        print(f"🏷️  Adding tag: {tag}")
        run_command(["docker", "tag", primary_tag, tag])

    # Push all tags
    for tag in tags:
        print(f"📤 Pushing {tag}...")
        run_command(["docker", "push", tag])

    print(f"\n✅ Successfully built and pushed:")
    for tag in tags:
        print(f"   📦 {tag}")

    print(f"\n🎉 Done! You can now pull with:")
    print(f"   docker pull {primary_tag}")


if __name__ == "__main__":
    main()
