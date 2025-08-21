#!/usr/bin/env python3
"""
Standalone Light Control Typo Test Generator
Generates simple_light_control_typo_test_cases.json
"""

import json
import random
import string

class StandaloneTypoTestGenerator:
    def __init__(self):
        # Define rooms (matching your smart home configuration)
        self.rooms = ["living_room", "bedroom", "kitchen", "study", "bathroom"]
        
        # Define devices per room (matching your actual configuration)
        self.devices = {
            "living_room": ["ceiling_light"],
            "bedroom": ["ceiling_light"],
            "kitchen": ["ceiling_light"],
            "study": ["ceiling_light", "desk_lamp"],
            "bathroom": ["ceiling_light"]
        }
        
        # Common typo patterns
        self.typo_patterns = {
            # Letter swapping
            "swap": lambda word: self._swap_letters(word),
            # Missing letter
            "delete": lambda word: self._delete_letter(word),
            # Double letter
            "double": lambda word: self._double_letter(word),
            # Wrong letter (nearby on keyboard)
            "wrong": lambda word: self._wrong_letter(word),
            # Insert random characters
            "insert": lambda word: self._insert_random(word)
        }
        
        # Keyboard layout for realistic typos
        self.keyboard_neighbors = {
            'a': ['q', 'w', 's', 'z'],
            'b': ['v', 'g', 'h', 'n'],
            'c': ['x', 'd', 'f', 'v'],
            'd': ['s', 'e', 'r', 'f', 'c', 'x'],
            'e': ['w', 'r', 'd', 's'],
            'f': ['d', 'r', 't', 'g', 'v', 'c'],
            'g': ['f', 't', 'y', 'h', 'b', 'v'],
            'h': ['g', 'y', 'u', 'j', 'n', 'b'],
            'i': ['u', 'o', 'k', 'j'],
            'j': ['h', 'u', 'i', 'k', 'm', 'n'],
            'k': ['j', 'i', 'o', 'l', 'm'],
            'l': ['k', 'o', 'p'],
            'm': ['n', 'j', 'k'],
            'n': ['b', 'h', 'j', 'm'],
            'o': ['i', 'p', 'l', 'k'],
            'p': ['o', 'l'],
            'q': ['w', 'a'],
            'r': ['e', 't', 'f', 'd'],
            's': ['a', 'w', 'e', 'd', 'x', 'z'],
            't': ['r', 'y', 'g', 'f'],
            'u': ['y', 'i', 'j', 'h'],
            'v': ['c', 'f', 'g', 'b'],
            'w': ['q', 'e', 's', 'a'],
            'x': ['z', 's', 'd', 'c'],
            'y': ['t', 'u', 'h', 'g'],
            'z': ['a', 's', 'x']
        }
    
    def _swap_letters(self, word):
        """Swap two adjacent letters"""
        if len(word) < 2:
            return word
        pos = random.randint(0, len(word) - 2)
        word_list = list(word)
        word_list[pos], word_list[pos + 1] = word_list[pos + 1], word_list[pos]
        return ''.join(word_list)
    
    def _delete_letter(self, word):
        """Delete a random letter"""
        if len(word) < 2:
            return word
        pos = random.randint(0, len(word) - 1)
        return word[:pos] + word[pos + 1:]
    
    def _double_letter(self, word):
        """Double a random letter"""
        if len(word) < 1:
            return word
        pos = random.randint(0, len(word) - 1)
        return word[:pos] + word[pos] + word[pos:]
    
    def _wrong_letter(self, word):
        """Replace a letter with a nearby key"""
        if len(word) < 1:
            return word
        pos = random.randint(0, len(word) - 1)
        char = word[pos].lower()
        if char in self.keyboard_neighbors:
            replacement = random.choice(self.keyboard_neighbors[char])
            if word[pos].isupper():
                replacement = replacement.upper()
            return word[:pos] + replacement + word[pos + 1:]
        return word
    
    def _insert_random(self, word):
        """Insert 1-3 random characters"""
        num_chars = random.randint(1, 3)
        # Choose position to insert
        pos = random.randint(0, len(word))
        # Generate random characters (letters, numbers, or symbols)
        chars = ''.join(random.choice(string.ascii_letters + string.digits + '!@#$%') 
                       for _ in range(num_chars))
        return word[:pos] + chars + word[pos:]
    
    def apply_typo(self, text, typo_type=None):
        """Apply typo to a text string"""
        words = text.split()
        
        # Choose which word to modify (avoid very short words)
        eligible_words = [(i, w) for i, w in enumerate(words) if len(w) > 2]
        if not eligible_words:
            # If no eligible words, try any word
            eligible_words = [(i, w) for i, w in enumerate(words)]
            if not eligible_words:
                return text
        
        idx, word = random.choice(eligible_words)
        
        # Apply typo
        if typo_type:
            if typo_type in self.typo_patterns:
                words[idx] = self.typo_patterns[typo_type](word)
        else:
            # Random typo type
            typo_func = random.choice(list(self.typo_patterns.values()))
            words[idx] = typo_func(word)
        
        return ' '.join(words)
    
    def generate_light_control_with_typos(self, count=100):
        """Generate light control commands with typos"""
        test_cases = []
        
        # Base templates for light control
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
        
        actions = ["on", "off"]
        typo_types = list(self.typo_patterns.keys())
        
        for i in range(count):
            # Choose random elements
            template = random.choice(templates)
            room = random.choice(self.rooms)
            
            # Get available devices for this room
            available_devices = [d for d in self.devices[room] if "light" in d or "lamp" in d]
            if not available_devices:
                available_devices = ["ceiling_light"]  # Default
            
            device = random.choice(available_devices)
            action = random.choice(actions)
            typo_type = random.choice(typo_types)
            
            # Format the command
            room_name = room.replace("_", " ")
            device_name = device.replace("_", " ")
            action_verb = f"turn {action}"
            
            command = template.format(
                action=action,
                action_verb=action_verb,
                room=room_name,
                device=device_name
            )
            
            # Apply typo
            command_with_typo = self.apply_typo(command, typo_type)
            
            test_cases.append({
                "id": f"simple_light_typo_{i+1:03d}",
                "input": command_with_typo,
                "original_input": command,
                "typo_type": typo_type,
                "expected_devices": [device],
                "expected_locations": [room],
                "expected_actions": [action],
                "expected_parameters": [{}],
                "category": "simple_light_control_typo",
                "description": f"Light control with {typo_type} typo - {action} {device} in {room}"
            })
        
        return test_cases


def main():
    """Main function to generate test cases"""
    print("Standalone Light Control Typo Test Generator")
    print("=" * 60)
    
    # Create generator
    generator = StandaloneTypoTestGenerator()
    
    # Show examples of each typo type
    print("\nTypo Type Examples:")
    print("-" * 40)
    original = "Turn on the living room lights"
    print(f"Original: {original}")
    
    for typo_type in generator.typo_patterns.keys():
        typo_text = generator.apply_typo(original, typo_type)
        print(f"{typo_type:8s}: {typo_text}")
    
    # Generate test cases
    print("\n" + "=" * 60)
    print("Generating 100 test cases with typos...")
    
    test_cases = generator.generate_light_control_with_typos(100)
    
    # Save to file
    output_filename = "simple_light_control_typo_test_cases.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Generated {len(test_cases)} test cases")
    print(f"✅ Saved to: {output_filename}")
    
    # Show statistics
    typo_counts = {}
    for test in test_cases:
        typo_type = test["typo_type"]
        typo_counts[typo_type] = typo_counts.get(typo_type, 0) + 1
    
    print("\nTypo Type Distribution:")
    print("-" * 40)
    for typo_type, count in sorted(typo_counts.items()):
        print(f"{typo_type:8s}: {count:3d} ({count/len(test_cases)*100:.1f}%)")
    
    # Show first 5 examples
    print("\nFirst 5 test cases:")
    print("-" * 60)
    for test in test_cases[:5]:
        print(f"\nID: {test['id']}")
        print(f"Original: {test['original_input']}")
        print(f"With typo: {test['input']}")
        print(f"Typo type: {test['typo_type']}")
        print(f"Expected: {test['expected_actions'][0]} {test['expected_devices'][0]} in {test['expected_locations'][0]}")


if __name__ == "__main__":
    main()