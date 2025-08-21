#!/usr/bin/env python3
"""
Smart Home Intent Test Cases Generator
Generates categorized test cases for intent recognition accuracy testing
"""

import json
import random
from typing import List, Dict
import os
from datetime import datetime

class TestCaseGenerator:
    def __init__(self):
        # Define rooms
        self.rooms = ["living_room", "bedroom", "kitchen", "study", "bathroom"]
        
        # Define devices per room - 根据实际项目配置
        self.devices = {
            "living_room": ["ceiling_light", "ac", "fan", "curtain"],
            "bedroom": ["ceiling_light", "ac", "fan", "curtain"],
            "kitchen": ["ceiling_light", "exhaust_fan"],
            "study": ["ceiling_light", "desk_lamp", "ac", "curtain"],
            "bathroom": ["ceiling_light", "exhaust_fan"]
        }
        
        # Define possible actions per device
        self.device_actions = {
            "ceiling_light": ["on", "off", "dim", "brighten", "set"],
            "desk_lamp": ["on", "off", "dim", "brighten", "set"],
            "ac": ["on", "off", "set_temperature", "increase", "decrease"],
            "fan": ["on", "off", "increase", "decrease", "set"],
            "exhaust_fan": ["on", "off"],
            "curtain": ["open", "close", "set"]
        }
        
        # Temperature settings for air conditioner
        self.temperatures = list(range(18, 31))
        
        # Brightness levels
        self.brightness_levels = ["10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"]
        
    def generate_simple_light_commands(self, count: int = 100) -> List[Dict]:
        """Generate simple light control commands"""
        test_cases = []
        templates = [
            "Turn {action} the {room} {device}",
            "Switch {action} the {device} in the {room}",
            "{action_verb} the {room} {device}",
            "Please {action_verb} the {device} in the {room}",
            "Can you {action_verb} the {room} {device}?",
            "I'd like to {action_verb} the {device} in the {room}",
            "{room} {device} {action}",
            "Make the {room} {device} {action}",
            "Set the {room} {device} {action}",
            "Could you please {action_verb} the {room} {device}?"
        ]
        
        for i in range(count):
            room = random.choice(self.rooms)
            devices = [d for d in self.devices[room] if "light" in d or "lamp" in d]
            if not devices:
                continue
                
            device = random.choice(devices)
            action = random.choice(["on", "off"])
            
            template = random.choice(templates)
            
            # Format the command
            if action == "on":
                action_verb = "turn on"
            else:
                action_verb = "turn off"
                
            room_name = room.replace("_", " ")
            device_name = device.replace("_", " ")
            
            command = template.format(
                action=action,
                action_verb=action_verb,
                room=room_name,
                device=device_name
            )
            
            test_cases.append({
                "id": f"simple_light_{i+1:03d}",
                "input": command,
                "expected_devices": [device],
                "expected_locations": [room],
                "expected_actions": [action],
                "category": "simple_light_control",
                "description": f"Simple {action} command for {device} in {room}"
            })
        
        return test_cases
    
    def generate_brightness_commands(self, count: int = 100) -> List[Dict]:
        """Generate brightness control commands"""
        test_cases = []
        templates = [
            "Dim the {room} {device}",
            "Brighten the {room} {device}",
            "Make the {room} {device} dimmer",
            "Make the {room} {device} brighter",
            "Increase the brightness of the {room} {device}",
            "Decrease the brightness of the {room} {device}",
            "Set the {room} {device} to {level} brightness",
            "Adjust the {room} {device} to {level}",
            "Turn the {room} {device} brightness to {level}",
            "Change the {room} {device} brightness to {level}"
        ]
        
        for i in range(count):
            room = random.choice(self.rooms)
            devices = [d for d in self.devices[room] if "light" in d or "lamp" in d]
            if not devices:
                continue
                
            device = random.choice(devices)
            template = random.choice(templates)
            
            # Determine action and parameters
            if "{level}" in template:
                level = random.choice(self.brightness_levels)
                action = "set"
                command = template.format(
                    room=room.replace("_", " "),
                    device=device.replace("_", " "),
                    level=level
                )
                parameters = {"brightness": level}
            else:
                if "dim" in template.lower() or "decrease" in template.lower():
                    action = "dim"
                else:
                    action = "brighten"
                command = template.format(
                    room=room.replace("_", " "),
                    device=device.replace("_", " ")
                )
                parameters = {}
            
            test_cases.append({
                "id": f"brightness_{i+1:03d}",
                "input": command,
                "expected_devices": [device],
                "expected_locations": [room],
                "expected_actions": [action],
                "expected_parameters": parameters,
                "category": "brightness_control",
                "description": f"Brightness control for {device} in {room}"
            })
        
        return test_cases
    
    def generate_temperature_commands(self, count: int = 100) -> List[Dict]:
        """Generate temperature/HVAC control commands"""
        test_cases = []
        templates = [
            "Set the {room} temperature to {temp} degrees",
            "Turn on the {room} air conditioner",
            "Turn off the {room} AC",
            "Make the {room} cooler",
            "Make the {room} warmer",
            "Set the {room} AC to {temp} degrees",
            "Adjust the {room} temperature to {temp}",
            "Change the {room} air conditioning to {temp} degrees",
            "I want the {room} to be {temp} degrees",
            "Cool down the {room}",
            "Warm up the {room}",
            "The {room} is too hot",
            "The {room} is too cold",
            "It's getting warm in the {room}",
            "Start the {room} air conditioner at {temp} degrees"
        ]
        
        for i in range(count):
            room = random.choice([r for r in self.rooms if "ac" in self.devices[r]])
            template = random.choice(templates)
            
            # Determine action and parameters
            if "{temp}" in template:
                temp = random.choice(self.temperatures)
                action = "set_temperature"
                command = template.format(
                    room=room.replace("_", " "),
                    temp=temp
                )
                parameters = {"temperature": temp}
            elif "turn on" in template.lower() or "start" in template.lower():
                action = "on"
                command = template.format(room=room.replace("_", " "))
                parameters = {}
            elif "turn off" in template.lower():
                action = "off"
                command = template.format(room=room.replace("_", " "))
                parameters = {}
            elif "cooler" in template.lower() or "cool down" in template.lower() or "too hot" in template.lower():
                action = "decrease"
                command = template.format(room=room.replace("_", " "))
                parameters = {}
            elif "warmer" in template.lower() or "warm up" in template.lower() or "too cold" in template.lower():
                action = "increase"
                command = template.format(room=room.replace("_", " "))
                parameters = {}
            else:
                action = "on"
                command = template.format(room=room.replace("_", " "))
                parameters = {}
            
            test_cases.append({
                "id": f"temperature_{i+1:03d}",
                "input": command,
                "expected_devices": ["ac"],
                "expected_locations": [room],
                "expected_actions": [action],
                "expected_parameters": parameters,
                "category": "temperature_control",
                "description": f"Temperature control for {room}"
            })
        
        return test_cases
    
    def generate_multi_device_commands(self, count: int = 100) -> List[Dict]:
        """Generate commands that control multiple devices"""
        test_cases = []
        templates = [
            "Turn on the {room} lights and air conditioner",
            "Turn off all the lights in the {room}",
            "Switch on both the {device1} and {device2} in the {room}",
            "Turn off the {room} {device1} and turn on the {device2}",
            "Set the {room} lights to dim and close the curtains",
            "Open the {room} curtains and turn on the lights",
            "Turn everything off in the {room}",
            "Prepare the {room} for sleep",
            "Set up the {room} for reading",
            "Make the {room} comfortable"
        ]
        
        for i in range(count):
            room = random.choice(self.rooms)
            available_devices = self.devices[room]
            
            # Choose template and determine devices/actions
            template = random.choice(templates)
            
            if "all the lights" in template:
                devices = [d for d in available_devices if "light" in d or "lamp" in d]
                actions = ["off"] * len(devices)
                locations = [room] * len(devices)
                command = template.format(room=room.replace("_", " "))
            elif "everything" in template:
                devices = available_devices.copy()
                actions = ["off"] * len(devices)
                locations = [room] * len(devices)
                command = template.format(room=room.replace("_", " "))
            elif "lights and air conditioner" in template:
                devices = []
                actions = []
                locations = []
                if "ceiling_light" in available_devices:
                    devices.append("ceiling_light")
                    actions.append("on")
                    locations.append(room)
                if "ac" in available_devices:
                    devices.append("ac")
                    actions.append("on")
                    locations.append(room)
                command = template.format(room=room.replace("_", " "))
            elif "for sleep" in template:
                devices = []
                actions = []
                locations = []
                if "ceiling_light" in available_devices:
                    devices.append("ceiling_light")
                    actions.append("off")
                    locations.append(room)
                if "air_conditioner" in available_devices:
                    devices.append("air_conditioner")
                    actions.append("set")
                    locations.append(room)
                if "curtain" in available_devices:
                    devices.append("curtain")
                    actions.append("close")
                    locations.append(room)
                command = template.format(room=room.replace("_", " "))
            elif "{device1}" in template and "{device2}" in template:
                if len(available_devices) >= 2:
                    device1, device2 = random.sample(available_devices, 2)
                    if "turn off" in template and "turn on" in template:
                        devices = [device1, device2]
                        actions = ["off", "on"]
                    else:
                        devices = [device1, device2]
                        actions = ["on", "on"]
                    locations = [room, room]
                    command = template.format(
                        room=room.replace("_", " "),
                        device1=device1.replace("_", " "),
                        device2=device2.replace("_", " ")
                    )
                else:
                    continue
            else:
                # Default case
                if len(available_devices) >= 2:
                    devices = random.sample(available_devices, 2)
                    actions = [random.choice(["on", "off"]) for _ in devices]
                    locations = [room] * len(devices)
                    command = f"Control multiple devices in the {room.replace('_', ' ')}"
                else:
                    continue
            
            test_cases.append({
                "id": f"multi_device_{i+1:03d}",
                "input": command,
                "expected_devices": devices,
                "expected_locations": locations,
                "expected_actions": actions,
                "category": "multi_device_control",
                "description": f"Multiple device control in {room}"
            })
        
        return test_cases
    
    def generate_scene_commands(self, count: int = 100) -> List[Dict]:
        """Generate scene-based commands"""
        test_cases = []
        
        # Define scenes with their expected device states - 根据实际设备配置
        scenes = {
            "movie": {
                "devices": ["ceiling_light", "curtain"],
                "actions": ["dim", "close"],
                "templates": [
                    "Movie mode",
                    "Set up movie mode",
                    "I want to watch a movie",
                    "Time for a movie",
                    "Movie time",
                    "Set the room for watching movies",
                    "Prepare for movie watching",
                    "Cinema mode",
                    "Theater mode",
                    "Let's watch a film"
                ]
            },
            "sleep": {
                "devices": ["ceiling_light", "ac", "curtain"],
                "actions": ["off", "set_temperature", "close"],
                "parameters": [
                    {},
                    {"temperature": 23},
                    {}
                ],
                "templates": [
                    "Good night",
                    "I'm going to sleep",
                    "Sleep mode",
                    "Bedtime",
                    "Time for bed",
                    "Set up for sleeping",
                    "Prepare the room for sleep",
                    "Night mode",
                    "I'm going to bed",
                    "Lights out"
                ]
            },
            "wake": {
                "devices": ["ceiling_light", "curtain"],
                "actions": ["on", "open"],
                "templates": [
                    "Good morning",
                    "Wake up mode",
                    "Time to wake up",
                    "Morning mode",
                    "Start the day",
                    "I'm awake",
                    "Rise and shine",
                    "Open everything up",
                    "Let the sunshine in",
                    "Brighten up the room"
                ]
            },
            "work": {
                "devices": ["ceiling_light", "desk_lamp", "ac"],
                "actions": ["on", "on", "set_temperature"],
                "parameters": [
                    {},
                    {},
                    {"temperature": 24}
                ],
                "templates": [
                    "Work mode",
                    "Time to work",
                    "Study mode",
                    "I need to focus",
                    "Set up for working",
                    "Productivity mode",
                    "Office mode",
                    "Focus time",
                    "Let's get some work done",
                    "Prepare the room for work"
                ]
            },
            "cooking": {
                "devices": ["ceiling_light", "exhaust_fan"],
                "actions": ["on", "on"],
                "templates": [
                    "Cooking mode",
                    "Time to cook",
                    "I'm cooking",
                    "Prepare the kitchen",
                    "Kitchen mode",
                    "Making dinner",
                    "Start cooking",
                    "Chef mode",
                    "Meal prep time",
                    "Let's cook something"
                ]
            },
            "relax": {
                "devices": ["ceiling_light", "ac"],
                "actions": ["dim", "set_temperature"],
                "parameters": [
                    {},
                    {"temperature": 25}
                ],
                "templates": [
                    "Relax mode",
                    "Time to relax",
                    "Chill mode",
                    "I want to relax",
                    "Relaxation time",
                    "Set a relaxing atmosphere",
                    "Comfort mode",
                    "Lounge mode",
                    "Wind down time",
                    "Create a cozy atmosphere"
                ]
            }
        }
        
        for i in range(count):
            # Choose a scene
            scene_name = random.choice(list(scenes.keys()))
            scene = scenes[scene_name]
            
            # Choose appropriate room based on scene
            if scene_name == "cooking":
                room = "kitchen"
            elif scene_name == "work":
                room = "study"
            elif scene_name == "sleep" or scene_name == "wake":
                suitable_rooms = ["bedroom", "living_room"]
                room = random.choice(suitable_rooms)
            else:
                suitable_rooms = ["living_room", "bedroom"]
                room = random.choice(suitable_rooms)
            
            # Filter devices based on what's available in the room
            devices = []
            actions = []
            locations = []
            
            for j, device in enumerate(scene["devices"]):
                if device in self.devices[room]:
                    devices.append(device)
                    actions.append(scene["actions"][j])
                    locations.append(room)
            
            # Skip if no devices available for this scene in this room
            if not devices:
                continue
            
            # Choose a template
            template = random.choice(scene["templates"])
            
            # Some templates might include room reference
            if random.random() < 0.3:  # 30% chance to include room
                command = f"{template} in the {room.replace('_', ' ')}"
            else:
                command = template
            
            test_cases.append({
                "id": f"scene_{i+1:03d}",
                "input": command,
                "expected_devices": devices,
                "expected_locations": locations,
                "expected_actions": actions,
                "category": "scene_control",
                "scene_type": scene_name,
                "description": f"{scene_name.capitalize()} scene in {room}"
            })
        
        return test_cases[:count]  # Ensure we return exactly 'count' items
    
    def generate_contextual_commands(self, count: int = 100) -> List[Dict]:
        """Generate contextual/implicit commands"""
        test_cases = []
        
        contexts = [
            # Temperature related
            {
                "templates": [
                    "It's too hot in here",
                    "The room is getting warm",
                    "I'm feeling hot",
                    "It's quite warm",
                    "Can we cool down the room?",
                    "This room is boiling",
                    "It's like a sauna in here",
                    "The temperature is too high",
                    "I'm sweating",
                    "Need some cooling"
                ],
                "device": "ac",
                "action": "on"
            },
            {
                "templates": [
                    "It's too cold in here",
                    "The room is freezing",
                    "I'm feeling cold",
                    "It's quite chilly",
                    "Can we warm up the room?",
                    "This room is like an icebox",
                    "The temperature is too low",
                    "I'm shivering",
                    "Need some warmth",
                    "It's arctic in here"
                ],
                "device": "ac",
                "action": "increase"
            },
            # Lighting related
            {
                "templates": [
                    "It's too dark in here",
                    "I can't see anything",
                    "Need more light",
                    "It's quite dim",
                    "Can't see properly",
                    "Too dark to read",
                    "Where's the light?",
                    "It's pitch black",
                    "Need illumination",
                    "Can barely see"
                ],
                "device": "ceiling_light",
                "action": "on"
            },
            {
                "templates": [
                    "It's too bright in here",
                    "The light is hurting my eyes",
                    "Too much light",
                    "It's glaring",
                    "The light is blinding",
                    "My eyes hurt",
                    "Too bright to sleep",
                    "The light is too intense",
                    "Need less light",
                    "It's like daylight in here"
                ],
                "device": "ceiling_light",
                "action": "dim"
            },
            # Air quality related
            {
                "templates": [
                    "The air is stuffy",
                    "Need fresh air",
                    "It's getting stuffy in here",
                    "The air feels stale",
                    "Can't breathe properly",
                    "Need ventilation",
                    "The room needs air",
                    "It smells in here",
                    "Air quality is poor",
                    "Need to air out the room"
                ],
                "device": "fan",
                "action": "on"
            }
        ]
        
        for i in range(count):
            context = random.choice(contexts)
            template = random.choice(context["templates"])
            
            # Choose a room that has the required device
            suitable_rooms = [room for room in self.rooms if context["device"] in self.devices[room]]
            
            if not suitable_rooms:
                # If no room has the device, use living room as default
                room = "living_room"
            else:
                room = random.choice(suitable_rooms)
            
            # Some commands might specify the room
            if random.random() < 0.2:  # 20% chance
                command = f"{template} in the {room.replace('_', ' ')}"
            else:
                command = template
            
            test_cases.append({
                "id": f"contextual_{i+1:03d}",
                "input": command,
                "expected_devices": [context["device"]],
                "expected_locations": [room],
                "expected_actions": [context["action"]],
                "category": "contextual_control",
                "context_type": context["device"],
                "description": f"Implicit {context['device']} control in {room}"
            })
        
        return test_cases
    
    def generate_negative_commands(self, count: int = 100) -> List[Dict]:
        """Generate commands that should NOT trigger any device control"""
        test_cases = []
        
        templates = [
            # Questions about status
            "What's the temperature in the {room}?",
            "Is the {device} on?",
            "How bright is the {room} light?",
            "What's the current setting of the air conditioner?",
            "Are all the lights off?",
            "What's the status of the {device}?",
            "Tell me about the room conditions",
            "How many lights are on?",
            "What devices are currently active?",
            "Check the {device} status",
            
            # General questions
            "What's the weather like?",
            "What time is it?",
            "How are you?",
            "Tell me a joke",
            "What can you do?",
            "Hello there",
            "Good afternoon",
            "Thank you",
            "That's great",
            "I appreciate it",
            
            # Information requests
            "How does the air conditioner work?",
            "What's the best temperature for sleeping?",
            "Tell me about energy saving",
            "What's the recommended humidity level?",
            "How much electricity does the {device} use?",
            "When should I change the air filter?",
            "What's the warranty on the {device}?",
            "How do I clean the {device}?",
            "What's the model number of the {device}?",
            "Who installed the {device}?",
            
            # Comments without commands
            "The room looks nice",
            "I like this temperature",
            "The lighting is perfect",
            "Everything is fine",
            "No changes needed",
            "Keep everything as is",
            "Don't change anything",
            "I'm comfortable",
            "The room feels good",
            "Nice atmosphere"
        ]
        
        for i in range(count):
            template = random.choice(templates)
            
            # Fill in placeholders if needed
            if "{room}" in template:
                room = random.choice(self.rooms)
                command = template.format(room=room.replace("_", " "))
            elif "{device}" in template:
                room = random.choice(self.rooms)
                device = random.choice(self.devices[room])
                command = template.format(device=device.replace("_", " "))
            else:
                command = template
            
            test_cases.append({
                "id": f"negative_{i+1:03d}",
                "input": command,
                "expected_devices": [],
                "expected_locations": [],
                "expected_actions": [],
                "category": "non_control_commands",
                "description": "Should not trigger any device control"
            })
        
        return test_cases
    
    def generate_complex_conditional_commands(self, count: int = 100) -> List[Dict]:
        """Generate complex commands with conditions or specific requirements"""
        test_cases = []
        
        templates = [
            # Time-based conditions
            "Turn on the {room} lights if it's dark outside",
            "Set the {room} to sleep mode in 30 minutes",
            "Turn off everything in an hour",
            "Wake me up at 7 AM with lights and open curtains",
            
            # Sequential commands
            "First turn on the lights, then adjust the temperature to {temp}",
            "Close the curtains before turning on the lights",
            "After I leave, turn everything off",
            "When I come back, turn on the lights and AC",
            
            # Conditional based on other devices
            "If the AC is on, close the windows",
            "Turn on the fan if the AC is off",
            "Dim the lights when the TV is on",
            "Open curtains unless the lights are on",
            
            # Specific device settings
            "Set the {room} light to 50% brightness and warm white",
            "Turn on the AC with eco mode",
            "Set the fan to oscillate at medium speed",
            "Adjust the {device} to the previous setting",
            
            # Location-specific all-room commands
            "Turn on all bedroom and living room lights",
            "Set all ACs to 24 degrees",
            "Dim all the lights except the kitchen",
            "Turn off everything except the {room}",
            
            # Activity-based
            "Set up the {room} for a video call",
            "Prepare the {room} for guests",
            "Configure the {room} for a party",
            "Set the {room} for meditation"
        ]
        
        for i in range(count):
            template = random.choice(templates)
            
            # Process based on template type
            if "sleep mode" in template:
                room = random.choice([r for r in self.rooms if "bedroom" in r or r == "bedroom"] or self.rooms)
                command = template.format(room=room.replace("_", " "))
                devices = []
                actions = []
                locations = []
                if "ceiling_light" in self.devices[room]:
                    devices.append("ceiling_light")
                    actions.append("off")
                    locations.append(room)
                if "ac" in self.devices[room]:
                    devices.append("ac")
                    actions.append("set_temperature")
                    locations.append(room)
            elif "{temp}" in template:
                room = random.choice([r for r in self.rooms if "ac" in self.devices[r]])
                temp = random.choice(self.temperatures)
                command = template.format(room=room.replace("_", " "), temp=temp)
                devices = ["ceiling_light", "ac"]
                actions = ["on", "set_temperature"]
                locations = [room, room]
            elif "all bedroom and living room" in template:
                devices = ["ceiling_light", "ceiling_light"]
                actions = ["on", "on"]
                locations = ["bedroom", "living_room"]
                command = template
            elif "Set all ACs" in template:
                # Find all rooms with AC
                ac_rooms = [r for r in self.rooms if "ac" in self.devices[r]]
                devices = ["ac"] * len(ac_rooms)
                actions = ["set_temperature"] * len(ac_rooms)
                locations = ac_rooms
                command = template
            elif "everything except" in template:
                room = random.choice(self.rooms)
                command = template.format(room=room.replace("_", " "))
                devices = []
                actions = []
                locations = []
                for r in self.rooms:
                    if r != room:
                        for device in self.devices[r]:
                            devices.append(device)
                            actions.append("off")
                            locations.append(r)
            else:
                # Generic case
                room = random.choice(self.rooms)
                device = random.choice(self.devices[room])
                command = template.format(
                    room=room.replace("_", " "),
                    device=device.replace("_", " ")
                )
                devices = [device]
                actions = ["on"]
                locations = [room]
            
            test_cases.append({
                "id": f"complex_{i+1:03d}",
                "input": command,
                "expected_devices": devices,
                "expected_locations": locations,
                "expected_actions": actions,
                "category": "complex_conditional",
                "description": f"Complex command with conditions"
            })
        
        return test_cases

def generate_all_test_cases():
    """Generate all categories of test cases"""
    generator = TestCaseGenerator()
    
    print("Generating test cases...")
    
    # Generate all categories
    all_test_cases = {
        "simple_light_control": generator.generate_simple_light_commands(100),
        "brightness_control": generator.generate_brightness_commands(100),
        "temperature_control": generator.generate_temperature_commands(100),
        "multi_device_control": generator.generate_multi_device_commands(100),
        "scene_control": generator.generate_scene_commands(100),
        "contextual_control": generator.generate_contextual_commands(100),
        "non_control_commands": generator.generate_negative_commands(100),
        "complex_conditional": generator.generate_complex_conditional_commands(100)
    }
    
    # Create output directory
    output_dir = "test_cases"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save each category separately
    for category, test_cases in all_test_cases.items():
        filename = f"{output_dir}/{category}_test_cases.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, indent=2)
        print(f"✓ Generated {len(test_cases)} test cases for {category}")
    
    # Save all test cases combined
    all_combined = []
    for category, test_cases in all_test_cases.items():
        all_combined.extend(test_cases)
    
    with open(f"{output_dir}/all_test_cases_combined.json", 'w', encoding='utf-8') as f:
        json.dump(all_combined, f, indent=2)
    
    print(f"\n✓ Total test cases generated: {len(all_combined)}")
    print(f"✓ Test cases saved to: {output_dir}/")
    
    # Generate summary report
    summary = {
        "generation_date": datetime.now().isoformat(),
        "total_test_cases": len(all_combined),
        "categories": {
            category: {
                "count": len(test_cases),
                "description": get_category_description(category)
            }
            for category, test_cases in all_test_cases.items()
        }
    }
    
    with open(f"{output_dir}/test_cases_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    return all_test_cases

def get_category_description(category: str) -> str:
    """Get description for each category"""
    descriptions = {
        "simple_light_control": "Basic on/off commands for lights and lamps",
        "brightness_control": "Commands for dimming, brightening, and setting specific brightness levels",
        "temperature_control": "HVAC and air conditioner control including temperature settings",
        "multi_device_control": "Commands that control multiple devices simultaneously",
        "scene_control": "Predefined scenes like movie mode, sleep mode, work mode, cooking mode, etc.",
        "contextual_control": "Implicit commands that require context understanding (e.g., 'it's too hot')",
        "non_control_commands": "Commands that should NOT trigger any device control (negative test cases)",
        "complex_conditional": "Complex commands with conditions, sequences, or specific requirements"
    }
    return descriptions.get(category, "")

# 添加一些特定于你的系统的测试用例生成函数
def generate_custom_test_cases():
    """Generate custom test cases specific to your smart home setup"""
    custom_tests = []
    
    # 书房特定测试（唯一有desk_lamp的房间）
    study_tests = [
        {
            "id": "custom_study_001",
            "input": "Turn on both lights in the study",
            "expected_devices": ["ceiling_light", "desk_lamp"],
            "expected_locations": ["study", "study"],
            "expected_actions": ["on", "on"],
            "category": "multi_device_control",
            "description": "Study room with both ceiling light and desk lamp"
        },
        {
            "id": "custom_study_002",
            "input": "I need good lighting for reading",
            "expected_devices": ["ceiling_light", "desk_lamp"],
            "expected_locations": ["study", "study"],
            "expected_actions": ["on", "on"],
            "category": "contextual_control",
            "description": "Contextual command for study lighting"
        }
    ]
    
    # 厨房和浴室特定测试（有exhaust_fan）
    ventilation_tests = [
        {
            "id": "custom_kitchen_001",
            "input": "Turn on the kitchen fan",
            "expected_devices": ["exhaust_fan"],
            "expected_locations": ["kitchen"],
            "expected_actions": ["on"],
            "category": "simple_light_control",
            "description": "Kitchen exhaust fan control"
        },
        {
            "id": "custom_bathroom_001",
            "input": "It's steamy in the bathroom",
            "expected_devices": ["exhaust_fan"],
            "expected_locations": ["bathroom"],
            "expected_actions": ["on"],
            "category": "contextual_control",
            "description": "Contextual command for bathroom ventilation"
        }
    ]
    
    custom_tests.extend(study_tests)
    custom_tests.extend(ventilation_tests)
    
    return custom_tests

if __name__ == "__main__":
    generate_all_test_cases()