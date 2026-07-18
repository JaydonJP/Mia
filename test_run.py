import yaml
import sys
import os

# Add the src directory to path so imports work
sys.path.insert(0, os.path.abspath('src'))

from mia.core.agent import Agent

print("Loading config...")
with open("config/mia.yaml", "r") as f:
    config = yaml.safe_load(f)

print("Initializing agent...")
agent = Agent(config)

print("Sending request to Mia...")
try:
    result = agent.process("List the files in the current directory.")
    print(f"\nFinal Result:\n{result}")
except Exception as e:
    print(f"\nError occurred: {e}")
