#!/usr/bin/env python3
"""Markdown Engine - CLI entry point."""

import sys
from pathlib import Path

from .markdown_engine import MarkdownCommandExecutor

def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Markdown Engine - Command execution for agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m system.markdown_engine --agent greeting_agent --actions
  python -m system.markdown_engine --search "python" calculator
  python -m system.markdown_engine --display quant_agent
  python -m system.markdown_engine --manifest bridge_agent
        """
    )
    
    parser.add_argument(
        "--agent", 
        type=str,
        required=True,
        help="Agent name to process"
    )
    parser.add_argument(
        "--actions",
        action="store_true",
        help="Show actions from markdown"
    )
    parser.add_argument(
        "--tasks",
        action="store_true",
        help="Show tasks from markdown"
    )
    parser.add_argument(
        "--code-blocks",
        action="store_true",
        help="Show code blocks from markdown"
    )
    parser.add_argument(
        "--search",
        type=str,
        default="",
        help="Search for commands"
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display full markdown content"
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Generate agent manifest"
    )
    
    args = parser.parse_args()
    
    executor = MarkdownCommandExecutor()
    
    if args.search:
        executor.show_search_results(args.agent, args.search)
    elif args.actions:
        executor.show_actions(args.agent)
    elif args.tasks:
        executor.show_tasks(args.agent)
    elif args.code_blocks:
        executor.show_code_blocks(args.agent)
    elif args.display:
        executor.display_markdown(args.agent)
    elif args.manifest:
        manifest = executor.engine.generate_agent_manifest(args.agent)
        print("\n".join([f"  {k}: {v}" for k, v in manifest.items()]))
    
    if not args.search and not args.actions and not args.tasks and not args.code_blocks and not args.display and not args.manifest:
        parser.print_help()

if __name__ == "__main__":
    main()
