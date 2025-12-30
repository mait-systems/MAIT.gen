#!/usr/bin/env python3
"""
Test baseline checking methods directly:
def _baseline_status_exists(self)
def _get_baseline_age_days(self)
def _check_and_update_baselines(self)
in the agent
"""
import yaml
import logging
from agent_powertrain_gateway import PowertrainAgentGateway

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print("=== TESTING BASELINE CHECKING METHODS ===")

    # Initialize agent
    agent = PowertrainAgentGateway('../generator_config.yaml')

    # Test individual methods
    print("\n1. Testing _baseline_status_exists():")
    exists = agent._baseline_status_exists()
    print(f"   Result: {exists}")

    print("\n2. Testing _get_baseline_age_days():")
    age = agent._get_baseline_age_days()
    print(f"   Result: {age} days")

    print("\n3. Testing _check_and_update_baselines():")
    agent._check_and_update_baselines()
    print("   Check logs above for results")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()