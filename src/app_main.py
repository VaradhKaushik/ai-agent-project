import argparse
import sys
# Removed Path and os, and sys.path manipulations as we'll rely on `python -m`

# Use explicit relative imports when running as a module within src
from utils.logging_config import setup_logging, get_logger
from agent.agent_core import SiteFeasibilityAgent
from utils.config import get_config

# Setup logging first, as other modules might use it upon import
setup_logging() 
logger = get_logger(__name__)

def main():
    """Main entry point for the Site Feasibility Agent application."""
    logger.info("Site Feasibility Agent Application Started")
    logger.info("============================================")

    parser = argparse.ArgumentParser(description="Site Feasibility Agent CLI")
    parser.add_argument("--query", type=str, help="A single query to process.")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode.")
    parser.add_argument("--demo", action="store_true", help="Run predefined demo queries.")

    args = parser.parse_args()

    try:
        agent = SiteFeasibilityAgent()
        logger.info("SiteFeasibilityAgent initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize SiteFeasibilityAgent: {e}", exc_info=True)
        print(f"Critical Error: Could not initialize the agent. Check logs. Details: {e}")
        return

    if args.query:
        logger.info(f"Processing single query: {args.query}")
        try:
            response = agent.run(args.query)
            print(f"\nAgent Response:\n{response}")
        except Exception as e:
            logger.error(f"Error processing query '{args.query}': {e}", exc_info=True)
            print(f"Error: {e}")
    
    elif args.interactive:
        logger.info("Entering interactive mode...")
        print("Welcome to the Site Feasibility Agent (Interactive Mode)!")
        print("Type 'quit' or 'exit' to end the session.")
        while True:
            try:
                user_query = input("\nYour Query: ")
                if user_query.lower() in ["quit", "exit"]:
                    logger.info("Exiting interactive mode.")
                    break
                if not user_query.strip():
                    continue
                
                logger.info(f"Interactive query: {user_query}")
                response = agent.run(user_query)
                print(f"\nAgent Response:\n{response}")
            
            except KeyboardInterrupt:
                logger.info("Interactive mode interrupted by user (Ctrl+C).")
                break
            except Exception as e:
                logger.error(f"Error during interactive session: {e}", exc_info=True)
                print(f"An error occurred: {e}")
                
    elif args.demo:
        logger.info("Running demo queries...")
        # Example queries from the original demo or README
        demo_queries = [
            {
                "query": "Is it feasible to build a 20 MW solar farm at 37.2 N, -121.9 W?",
                "description": "Feasibility Analysis"
            },
            {
                "query": "How much would it cost to deliver power from 37.2N, -121.9W to San José, CA (37.3 N, -122.0 W)? The farm is 20MW.",
                "description": "Transmission Cost Analysis"
            },
            {
                "query": "Tell me about California ISO interconnection queue",
                "description": "Knowledge Base Query (RAG)"
            },
            {
                "query": "What is the capex for a 50MW solar project?",
                "description": "Cost Model Query"
            }
        ]
        
        for i, demo in enumerate(demo_queries, 1):
            print(f"\n{'='*60}")
            print(f"Demo Query {i}: {demo['description']}")
            print(f"{'='*60}")
            print(f"Question: {demo['query']}")
            print(f"Processing...")
            logger.info(f"Processing demo query: {demo['query']}")
            
            try:
                response = agent.run(demo['query'])
                print(f"Agent Response:\n{response}")
            except Exception as e:
                logger.error(f"Error processing demo query '{demo['query']}': {e}", exc_info=True)
                print(f"Error: {e}")
            print("="*60)
            if i < len(demo_queries):
                try:
                    input("Press Enter to continue to next demo...")
                except KeyboardInterrupt:
                    logger.info("Demo mode interrupted by user.")
                    break
    else:
        logger.info("No specific mode selected or invalid combination. Defaulting to interactive mode.")
        print("Welcome to the Site Feasibility Agent (Interactive Mode)!")
        print("Type 'quit' or 'exit' to end the session.")
        # agent is already initialized
        while True:
            try:
                user_query = input("\nYour Query: ")
                if user_query.lower() in ["quit", "exit"]:
                    logger.info("Exiting interactive mode (default).")
                    break
                if not user_query.strip():
                    continue
                
                logger.info(f"Interactive query (default mode): {user_query}")
                response = agent.run(user_query)
                print(f"\nAgent Response:\n{response}")
            except KeyboardInterrupt:
                logger.info("Interactive mode (default) interrupted by user (Ctrl+C).")
                break
            except Exception as e:
                logger.error(f"Error during interactive session (default): {e}", exc_info=True)
                print(f"An error occurred: {e}")

    logger.info("Site Feasibility Agent Application Finished.")

if __name__ == "__main__":
    main() 