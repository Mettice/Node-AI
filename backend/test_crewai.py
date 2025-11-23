"""
Simple test script for CrewAI Agent Node
Run this to test CrewAI functionality directly
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.nodes.agent.crewai_agent import CrewAIAgentNode
from backend.config import settings


async def test_crewai_simple():
    """Test CrewAI with a simple research and write task."""
    print("🧪 Testing CrewAI Agent Node...")
    print("=" * 60)
    
    # Check API key
    if not settings.openai_api_key:
        print("❌ ERROR: OPENAI_API_KEY not set!")
        print("   Set it in your .env file or environment variables")
        return
    
    # Create node
    node = CrewAIAgentNode()
    
    # Test configuration
    config = {
        "provider": "openai",
        "openai_model": "gpt-4",
        "temperature": 0.7,
        "max_iterations": 3,
        "process": "sequential",
        "agents": [
            {
                "role": "Researcher",
                "goal": "Research the topic thoroughly and gather comprehensive information",
                "backstory": "You are an expert researcher with 10 years of experience in technology and AI."
            },
            {
                "role": "Writer",
                "goal": "Write a clear, comprehensive report based on research findings",
                "backstory": "You are a skilled technical writer who creates engaging, informative content."
            }
        ],
        "tasks": [
            {
                "description": "Research the latest AI trends in 2024, including key developments and breakthroughs",
                "agent": "Researcher"
            },
            {
                "description": "Write a comprehensive report based on the research findings, including an executive summary and key trends",
                "agent": "Writer"
            }
        ]
    }
    
    # Test inputs
    inputs = {
        "text": "Research the latest AI trends in 2024 and write a comprehensive report"
    }
    
    print("\n📋 Configuration:")
    print(f"   Provider: {config['provider']}")
    print(f"   Model: {config['openai_model']}")
    print(f"   Agents: {len(config['agents'])}")
    print(f"   Tasks: {len(config['tasks'])}")
    print(f"\n📝 Task: {inputs['text']}")
    print("\n🚀 Executing CrewAI workflow...\n")
    
    try:
        # Execute
        result = await node.execute(inputs, config)
        
        print("=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"\n📊 Output:\n{result.get('output', 'No output')}")
        print(f"\n👥 Agents Used: {result.get('agents', [])}")
        print(f"📋 Tasks Completed: {result.get('tasks', [])}")
        print(f"💰 Estimated Cost: ${result.get('cost', 0):.4f}")
        print(f"🤖 Provider: {result.get('provider', 'unknown')}")
        print(f"🧠 Model: {result.get('model', 'unknown')}")
        
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR!")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        print(f"\nType: {type(e).__name__}")
        import traceback
        traceback.print_exc()


async def test_crewai_with_tools():
    """Test CrewAI with tools (requires tool nodes to be connected)."""
    print("\n🧪 Testing CrewAI with Tools...")
    print("=" * 60)
    print("⚠️  Note: This requires Tool nodes to be connected in a workflow")
    print("   For now, this is a placeholder for workflow testing")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CrewAI Agent Node Test Suite")
    print("=" * 60 + "\n")
    
    # Run simple test
    asyncio.run(test_crewai_simple())
    
    # Run tools test (placeholder)
    # asyncio.run(test_crewai_with_tools())
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60 + "\n")

