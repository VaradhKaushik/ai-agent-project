#!/usr/bin/env python3
"""
Site Feasibility Agent Demo
Simple demonstration of the agent capabilities with example queries.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.graph_agent import run_site_agent

def main():
    """Run demo with example queries."""
    print("🌞 Site Feasibility Agent - Demo")
    print("=" * 50)
    
    # Example queries from the specification
    demo_queries = [
        {
            "query": "Is it feasible to build a 20 MW solar farm at 37.2 N, -121.9 W?",
            "description": "Feasibility Analysis"
        },
        {
            "query": "What would it cost to deliver that power to San José, CA (37.3 N, -122.0 W)?",
            "description": "Transmission Cost Analysis"
        },
        {
            "query": "Tell me about California ISO interconnection queue",
            "description": "Knowledge Base Query (RAG)"
        }
    ]
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n{'='*60}")
        print(f"Demo {i}: {demo['description']}")
        print(f"{'='*60}")
        print(f"🤔 Question: {demo['query']}")
        print(f"{'🔍 Processing...'}")
        print("-" * 60)
        
        try:
            response = run_site_agent(demo['query'])
            print(f"🤖 Agent Response:\n{response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*60)
        
        # Pause between demos
        input("Press Enter to continue to next demo...")

if __name__ == "__main__":
    main() 