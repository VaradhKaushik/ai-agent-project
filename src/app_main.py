import argparse
import sys

# Use explicit relative imports when running as a module within src
from utils.logging_config import setup_logging, get_logger
from agent.agent_core import SolarFeasibilityAgent
from utils.config import get_config

# Setup logging first, as other modules might use it upon import
setup_logging() 
logger = get_logger(__name__)

def main():
    """Main entry point for the Solar Feasibility Agent application."""
    logger.info("Solar Feasibility Agent Application Started")
    logger.info("============================================")

    parser = argparse.ArgumentParser(description="Solar Feasibility Agent CLI with True LLM Tool Calling")
    parser.add_argument("--query", type=str, help="A single query to process.")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode.")
    parser.add_argument("--demo", action="store_true", help="Run predefined demo queries.")

    args = parser.parse_args()

    try:
        agent = SolarFeasibilityAgent()
        logger.info("Solar Feasibility Agent initialized successfully with LLM tool calling.")
    except Exception as e:
        logger.critical(f"Failed to initialize Solar Feasibility Agent: {e}", exc_info=True)
        print(f"Critical Error: Could not initialize the agent. Details: {e}")
        print("\nPlease ensure:")
        print("1. You have set OPENAI_API_KEY environment variable")
        print("2. You have installed required packages: pip install langchain-openai")
        print("3. You have valid OpenAI API access")
        return

    if args.query:
        logger.info(f"Processing single query: {args.query}")
        try:
            response = agent.analyze(args.query)
            print(f"\nAgent Response:\n{response}")
        except Exception as e:
            logger.error(f"Error processing query '{args.query}': {e}", exc_info=True)
            print(f"Error: {e}")
    
    elif args.interactive:
        logger.info("Entering interactive mode...")
        print("Welcome to the Solar Feasibility Agent (Interactive Mode - True LLM Tool Calling)!")
        print("The AI will intelligently select and call tools based on your queries.")
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
                response = agent.analyze(user_query)
                print(f"\nAgent Response:\n{response}")
            
            except KeyboardInterrupt:
                logger.info("Interactive mode interrupted by user (Ctrl+C).")
                break
            except Exception as e:
                logger.error(f"Error during interactive session: {e}", exc_info=True)
                print(f"An error occurred: {e}")
                
    elif args.demo:
        logger.info("Running demo queries...")
        print(f"\n=== DEMO MODE (True LLM Tool Calling) ===")
        
        # Demo queries that showcase the true LLM tool calling capabilities
        demo_queries = [
            {
                "query": "What's the solar potential for a 20MW project in Miami, Florida?",
                "description": "Location-based Analysis with AI Tool Selection"
            },
            {
                "query": "Analyze the feasibility of a 50MW solar farm at coordinates 36.1699, -115.1398",
                "description": "Coordinate-based Analysis (Las Vegas location)"
            },
            {
                "query": "Compare solar costs and incentives between California and Texas",
                "description": "Market Research and Comparison"
            },
            {
                "query": "What are the latest trends in solar technology and pricing for 2024?",
                "description": "Market Intelligence Query"
            },
            {
                "query": "Is it feasible to build a 100MW solar project in Phoenix with current market conditions?",
                "description": "Large-scale Feasibility Analysis"
            }
        ]
        
        for i, demo in enumerate(demo_queries, 1):
            print(f"\n{'='*70}")
            print(f"Demo Query {i}: {demo['description']}")
            print(f"{'='*70}")
            print(f"Question: {demo['query']}")
            print(f"Processing... (LLM is selecting and calling tools)")
            logger.info(f"Processing demo query: {demo['query']}")
            
            try:
                response = agent.analyze(demo['query'])
                print(f"Agent Response:\n{response}")
            except Exception as e:
                logger.error(f"Error processing demo query '{demo['query']}': {e}", exc_info=True)
                print(f"Error: {e}")
            print("="*70)
            if i < len(demo_queries):
                try:
                    input("Press Enter to continue to next demo...")
                except KeyboardInterrupt:
                    logger.info("Demo mode interrupted by user.")
                    break
    else:
        logger.info("No specific mode selected. Defaulting to interactive mode.")
        print("Welcome to the Solar Feasibility Agent (Interactive Mode - True LLM Tool Calling)!")
        print("The AI will intelligently select and call tools based on your queries.")
        print("Type 'quit' or 'exit' to end the session.")
        
        while True:
            try:
                user_query = input("\nYour Query: ")
                if user_query.lower() in ["quit", "exit"]:
                    break
                if not user_query.strip():
                    continue
                
                response = agent.analyze(user_query)
                print(f"\nAgent Response:\n{response}")
            except KeyboardInterrupt:
                logger.info("Interactive mode (default) interrupted by user (Ctrl+C).")
                break
            except Exception as e:
                logger.error(f"Error during interactive session (default): {e}", exc_info=True)
                print(f"An error occurred: {e}")

    logger.info("Solar Feasibility Agent Application Finished.")

if __name__ == "__main__":
    main() 