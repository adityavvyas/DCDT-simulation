import json
import random
from collections import defaultdict

class ScenarioCombinator:
    """Creates random workload plans for all machines."""
    def __init__(self, num_machines=700, scenarios_per_machine=5):
        self.num_machines = num_machines
        self.scenarios_per_machine = scenarios_per_machine
        print("Scenario Combinator initialized.")

    def generate_random_combination_plan(self):
        """Returns a list of random scenario choices (e.g., [3, 1, 5...])."""
        return [random.randint(1, self.scenarios_per_machine) for _ in range(self.num_machines)]

class DataIngestor:
    """Reads the data file and serves states based on the Combinator's plan."""
    def __init__(self, filepath='data/datacenter_full_state_list.json'):
        try:
            with open(filepath, 'r') as f:
                flat_data_list = json.load(f)
            
            grouped_scenarios = defaultdict(list)
            for record in flat_data_list:
                entity_id = record['meta_data']['entityId']
                grouped_scenarios[entity_id].append(record)

            self.scenarios = dict(grouped_scenarios)
            self.machine_ids = sorted(list(self.scenarios.keys()))
            
            print(f"Data Ingestor loaded and grouped {len(self.machine_ids)} machines successfully.")

        except FileNotFoundError:
            print(f"[bold red]Error: '{filepath}' not found.[/bold red]")
            exit()

    def get_state_from_plan(self, combination_plan):
        """Builds the full datacenter state from the combination plan."""
        datacenter_state = []
        for i, machine_id in enumerate(self.machine_ids):
            num_available = len(self.scenarios.get(machine_id, []))
            if num_available == 0:
                continue

            safe_index = (combination_plan[i] - 1) % num_available
            scenario_data = self.scenarios[machine_id][safe_index]
            
            datacenter_state.append({
                "meta_data": scenario_data['meta_data'],
                "payload": scenario_data['payload']
            })
        return datacenter_state

