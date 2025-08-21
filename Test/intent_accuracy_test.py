#!/usr/bin/env python3
"""
Smart Home Intent Recognition Accuracy Testing Script
Used to test the intent recognition accuracy of SmartHome-Docker-LLM system
"""

import requests
import json
import time
import datetime
from typing import Dict, List, Tuple
import pandas as pd
from collections import defaultdict
import argparse
import os

class IntentAccuracyTester:
    def __init__(self, coordinator_url="http://localhost:8080", output_dir="./test_results"):
        """
        Initialize the tester
        
        Args:
            coordinator_url: URL of the Coordinator service
            output_dir: Output directory for test results
        """
        self.coordinator_url = coordinator_url
        self.output_dir = output_dir
        self.results = []
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
    def load_test_cases(self, test_file_path: str) -> List[Dict]:
        """
        Load test cases
        
        Test file format (JSON):
        [
            {
                "id": "test_001",
                "input": "Turn on the living room lights",
                "expected_intents": ["turn_on_light"],
                "expected_devices": ["ceiling_light"],
                "expected_locations": ["living_room"],
                "expected_actions": ["on"],
                "description": "Simple light on command"
            },
            ...
        ]
        """
        with open(test_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_single_input(self, test_case: Dict) -> Dict:
        """
        Test a single input
        
        Args:
            test_case: Single test case
            
        Returns:
            Test result dictionary
        """
        start_time = time.time()
        
        # Send request to Coordinator
        try:
            response = requests.post(
                f"{self.coordinator_url}/process_text",
                json={"text": test_case["input"]},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract actual recognized intents and commands
                actual_commands = result.get("iot_commands", [])
                
                # Analyze results
                analysis = self.analyze_result(test_case, actual_commands)
                
                return {
                    "test_id": test_case["id"],
                    "input": test_case["input"],
                    "description": test_case.get("description", ""),
                    "expected": {
                        "intents": test_case.get("expected_intents", []),
                        "devices": test_case.get("expected_devices", []),
                        "locations": test_case.get("expected_locations", []),
                        "actions": test_case.get("expected_actions", [])
                    },
                    "actual": {
                        "commands": actual_commands,
                        "ai_response": result.get("ai_response", ""),
                        "raw_response": result
                    },
                    "analysis": analysis,
                    "response_time": response_time,
                    "success": response.status_code == 200,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            else:
                return {
                    "test_id": test_case["id"],
                    "input": test_case["input"],
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response_time,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "test_id": test_case["id"],
                "input": test_case["input"],
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def analyze_result(self, test_case: Dict, actual_commands: List[Dict]) -> Dict:
        """
        Analyze test results
        
        Returns:
            Dictionary containing accuracy metrics
        """
        # Extract actual devices, locations and actions
        actual_devices = [cmd.get("device", "") for cmd in actual_commands]
        actual_locations = [cmd.get("location", "") for cmd in actual_commands]
        actual_actions = [cmd.get("action", "") for cmd in actual_commands]
        
        # Expected values
        expected_devices = test_case.get("expected_devices", [])
        expected_locations = test_case.get("expected_locations", [])
        expected_actions = test_case.get("expected_actions", [])
        
        # Calculate accuracy
        device_accuracy = self.calculate_accuracy(expected_devices, actual_devices)
        location_accuracy = self.calculate_accuracy(expected_locations, actual_locations)
        action_accuracy = self.calculate_accuracy(expected_actions, actual_actions)
        
        # Overall accuracy (all dimensions must be correct)
        overall_correct = (
            device_accuracy["exact_match"] and 
            location_accuracy["exact_match"] and 
            action_accuracy["exact_match"]
        )
        
        return {
            "device_accuracy": device_accuracy,
            "location_accuracy": location_accuracy,
            "action_accuracy": action_accuracy,
            "overall_correct": overall_correct,
            "command_count_match": len(actual_commands) == len(expected_devices),
            "category": test_case.get("category", "unknown")
        }
    
    def calculate_accuracy(self, expected: List[str], actual: List[str]) -> Dict:
        """Calculate accuracy metrics"""
        expected_set = set(expected)
        actual_set = set(actual)
        
        # Exact match
        exact_match = expected_set == actual_set
        
        # Calculate precision and recall
        if len(actual_set) == 0:
            precision = 0.0 if len(expected_set) > 0 else 1.0
        else:
            precision = len(expected_set.intersection(actual_set)) / len(actual_set)
            
        if len(expected_set) == 0:
            recall = 1.0
        else:
            recall = len(expected_set.intersection(actual_set)) / len(expected_set)
        
        # F1 score
        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)
        
        return {
            "exact_match": exact_match,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "expected": list(expected_set),
            "actual": list(actual_set),
            "missing": list(expected_set - actual_set),
            "extra": list(actual_set - expected_set)
        }
    
    def run_tests(self, test_cases: List[Dict], delay_between_tests: float = 1.0):
        """
        Run all test cases
        
        Args:
            test_cases: List of test cases
            delay_between_tests: Delay between tests in seconds
        """
        print(f"Starting {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases):
            print(f"\n[{i+1}/{len(test_cases)}] Testing: {test_case['input']}")
            
            result = self.test_single_input(test_case)
            self.results.append(result)
            
            if result["success"]:
                if result["analysis"]["overall_correct"]:
                    print("✅ Test passed")
                else:
                    print("❌ Test failed")
                    print(f"   Device accuracy: {result['analysis']['device_accuracy']['f1_score']:.2f}")
                    print(f"   Location accuracy: {result['analysis']['location_accuracy']['f1_score']:.2f}")
                    print(f"   Action accuracy: {result['analysis']['action_accuracy']['f1_score']:.2f}")
            else:
                print(f"❌ Request failed: {result['error']}")
            
            # Avoid too frequent requests
            if i < len(test_cases) - 1:
                time.sleep(delay_between_tests)
    
    def generate_report(self):
        """Generate test report"""
        if not self.results:
            print("No test results")
            return
        
        # Calculate overall statistics
        total_tests = len(self.results)
        successful_requests = sum(1 for r in self.results if r["success"])
        overall_correct = sum(1 for r in self.results if r.get("analysis", {}).get("overall_correct", False))
        
        # Statistics by category
        category_stats = defaultdict(lambda: {
            "total": 0,
            "correct": 0,
            "device_f1_sum": 0,
            "location_f1_sum": 0,
            "action_f1_sum": 0,
            "response_time_sum": 0
        })
        
        for result in self.results:
            if result["success"] and "analysis" in result:
                category = result["analysis"].get("category", "unknown")
                stats = category_stats[category]
                stats["total"] += 1
                if result["analysis"]["overall_correct"]:
                    stats["correct"] += 1
                stats["device_f1_sum"] += result["analysis"]["device_accuracy"]["f1_score"]
                stats["location_f1_sum"] += result["analysis"]["location_accuracy"]["f1_score"]
                stats["action_f1_sum"] += result["analysis"]["action_accuracy"]["f1_score"]
                stats["response_time_sum"] += result["response_time"]
        
        # Calculate averages by category
        category_summary = {}
        for category, stats in category_stats.items():
            if stats["total"] > 0:
                category_summary[category] = {
                    "total_tests": stats["total"],
                    "correct_tests": stats["correct"],
                    "accuracy": stats["correct"] / stats["total"],
                    "avg_device_f1": stats["device_f1_sum"] / stats["total"],
                    "avg_location_f1": stats["location_f1_sum"] / stats["total"],
                    "avg_action_f1": stats["action_f1_sum"] / stats["total"],
                    "avg_response_time": stats["response_time_sum"] / stats["total"]
                }
        
        # Calculate overall averages
        all_device_f1 = []
        all_location_f1 = []
        all_action_f1 = []
        all_response_times = []
        
        for result in self.results:
            if result.get("analysis"):
                all_device_f1.append(result["analysis"]["device_accuracy"]["f1_score"])
                all_location_f1.append(result["analysis"]["location_accuracy"]["f1_score"])
                all_action_f1.append(result["analysis"]["action_accuracy"]["f1_score"])
                all_response_times.append(result["response_time"])
        
        avg_device_f1 = sum(all_device_f1) / len(all_device_f1) if all_device_f1 else 0
        avg_location_f1 = sum(all_location_f1) / len(all_location_f1) if all_location_f1 else 0
        avg_action_f1 = sum(all_action_f1) / len(all_action_f1) if all_action_f1 else 0
        avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        
        # Generate report
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_requests": successful_requests,
                "request_success_rate": successful_requests / total_tests,
                "overall_accuracy": overall_correct / successful_requests if successful_requests > 0 else 0,
                "average_device_f1": avg_device_f1,
                "average_location_f1": avg_location_f1,
                "average_action_f1": avg_action_f1,
                "average_response_time": avg_response_time,
                "test_time": datetime.datetime.now().isoformat()
            },
            "category_summary": category_summary,
            "detailed_results": self.results
        }
        
        # Print summary
        print("\n" + "="*50)
        print("Test Report Summary")
        print("="*50)
        print(f"Total tests: {total_tests}")
        print(f"Successful requests: {successful_requests} ({successful_requests/total_tests*100:.1f}%)")
        print(f"Overall accuracy: {overall_correct}/{successful_requests} ({report['summary']['overall_accuracy']*100:.1f}%)")
        print(f"Average device F1: {avg_device_f1:.3f}")
        print(f"Average location F1: {avg_location_f1:.3f}")
        print(f"Average action F1: {avg_action_f1:.3f}")
        print(f"Average response time: {avg_response_time:.2f}s")
        
        if category_summary:
            print("\n" + "-"*50)
            print("Category Statistics")
            print("-"*50)
            print(f"{'Category':<25} {'Accuracy':<10} {'Device F1':<10} {'Location F1':<10} {'Action F1':<10}")
            print("-"*50)
            for category, stats in category_summary.items():
                print(f"{category:<25} {stats['accuracy']*100:>6.1f}%   {stats['avg_device_f1']:>6.3f}    {stats['avg_location_f1']:>6.3f}    {stats['avg_action_f1']:>6.3f}")
        
        # Save detailed report
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.output_dir, f"accuracy_report_{timestamp}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nDetailed report saved to: {report_path}")
        
        # Generate CSV report for further analysis
        self.generate_csv_report(timestamp)
    
    def generate_csv_report(self, timestamp: str):
        """Generate CSV format report"""
        csv_data = []
        
        for result in self.results:
            if result["success"] and "analysis" in result:
                csv_data.append({
                    "test_id": result["test_id"],
                    "category": result["analysis"].get("category", "unknown"),
                    "input": result["input"],
                    "overall_correct": result["analysis"]["overall_correct"],
                    "device_f1": result["analysis"]["device_accuracy"]["f1_score"],
                    "location_f1": result["analysis"]["location_accuracy"]["f1_score"],
                    "action_f1": result["analysis"]["action_accuracy"]["f1_score"],
                    "response_time": result["response_time"],
                    "expected_devices": "|".join(result["expected"]["devices"]),
                    "actual_devices": "|".join([cmd.get("device", "") for cmd in result["actual"]["commands"]]),
                    "ai_response": result["actual"]["ai_response"]
                })
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_path = os.path.join(self.output_dir, f"accuracy_results_{timestamp}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"CSV report saved to: {csv_path}")


# Example test case generator
def generate_example_test_cases():
    """Generate example test cases"""
    test_cases = [
        # Simple commands
        {
            "id": "test_001",
            "input": "Turn on the living room lights",
            "expected_devices": ["ceiling_light"],
            "expected_locations": ["living_room"],
            "expected_actions": ["on"],
            "description": "Simple light on command - English"
        },
        {
            "id": "test_002",
            "input": "Close the bedroom curtains",
            "expected_devices": ["curtain"],
            "expected_locations": ["bedroom"],
            "expected_actions": ["close"],
            "description": "Curtain control command"
        },
        {
            "id": "test_003",
            "input": "Turn off the kitchen exhaust fan",
            "expected_devices": ["exhaust_fan"],
            "expected_locations": ["kitchen"],
            "expected_actions": ["off"],
            "description": "Kitchen exhaust fan command"
        },
        
        # Complex commands
        {
            "id": "test_004",
            "input": "Dim the lights and set temperature to 24 degrees in the living room",
            "expected_devices": ["ceiling_light", "air_conditioner"],
            "expected_locations": ["living_room", "living_room"],
            "expected_actions": ["dim", "set"],
            "description": "Multi-device compound command"
        },
        {
            "id": "test_005",
            "input": "Turn on all lights",
            "expected_devices": ["ceiling_light", "ceiling_light", "ceiling_light", "ceiling_light", "ceiling_light"],
            "expected_locations": ["living_room", "bedroom", "kitchen", "study", "bathroom"],
            "expected_actions": ["on", "on", "on", "on", "on"],
            "description": "Whole house control command"
        },
        
        # Scene commands
        {
            "id": "test_006",
            "input": "Good night",
            "expected_devices": ["ceiling_light", "air_conditioner", "curtain"],
            "expected_locations": ["bedroom", "bedroom", "bedroom"],
            "expected_actions": ["off", "set", "close"],
            "description": "Sleep scene"
        },
        {
            "id": "test_007",
            "input": "Movie mode",
            "expected_devices": ["ceiling_light", "curtain"],
            "expected_locations": ["living_room", "living_room"],
            "expected_actions": ["dim", "close"],
            "description": "Movie scene"
        },
        
        # Contextual commands
        {
            "id": "test_008",
            "input": "It's too hot",
            "expected_devices": ["air_conditioner"],
            "expected_locations": ["living_room"],
            "expected_actions": ["on"],
            "description": "Implicit command - turn on AC"
        },
        {
            "id": "test_009",
            "input": "I can't see",
            "expected_devices": ["ceiling_light"],
            "expected_locations": ["living_room"],
            "expected_actions": ["on"],
            "description": "Implicit command - turn on light"
        },
        
        # Non-control commands
        {
            "id": "test_010",
            "input": "What's the weather like?",
            "expected_devices": [],
            "expected_locations": [],
            "expected_actions": [],
            "description": "Non-control command"
        }
    ]
    
    return test_cases


def main():
    parser = argparse.ArgumentParser(description="Smart Home Intent Recognition Accuracy Tester")
    parser.add_argument("--coordinator-url", default="http://localhost:8080",
                       help="Coordinator service URL")
    parser.add_argument("--test-file", help="Path to test cases JSON file")
    parser.add_argument("--generate-examples", action="store_true",
                       help="Generate example test cases file")
    parser.add_argument("--output-dir", default="./test_results",
                       help="Output directory for test results")
    parser.add_argument("--delay", type=float, default=1.0,
                       help="Delay between tests in seconds")
    
    args = parser.parse_args()
    
    if args.generate_examples:
        # Generate example test cases file
        examples = generate_example_test_cases()
        with open("example_test_cases.json", 'w', encoding='utf-8') as f:
            json.dump(examples, f, ensure_ascii=False, indent=2)
        print("Example test cases generated: example_test_cases.json")
        return
    
    if not args.test_file:
        print("Please specify test file path (--test-file) or use --generate-examples to generate examples")
        return
    
    # Create tester
    tester = IntentAccuracyTester(
        coordinator_url=args.coordinator_url,
        output_dir=args.output_dir
    )
    
    # Load test cases
    test_cases = tester.load_test_cases(args.test_file)
    print(f"Loaded {len(test_cases)} test cases")
    
    # Run tests
    tester.run_tests(test_cases, delay_between_tests=args.delay)
    
    # Generate report
    tester.generate_report()


if __name__ == "__main__":
    main()