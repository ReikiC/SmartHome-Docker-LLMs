import os
import re
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class LLMIoTExtractor:
    """Enhanced LLM-based IoT command extractor with comprehensive understanding"""
    
    def __init__(self, ollama_endpoint: str, model_name: str, api_headers: dict = None):
        self.ollama_endpoint = ollama_endpoint
        self.model_name = model_name
        self.api_headers = api_headers or {}
        
        # Define device-room mappings for validation
        self.room_devices = {
            "living_room": ["ceiling_light", "fan", "ac", "curtain"],
            "bedroom": ["ceiling_light", "desk_lamp", "fan", "ac", "curtain"],
            "kitchen": ["ceiling_light", "exhaust_fan"],
            "study": ["ceiling_light", "desk_lamp", "fan", "curtain"],
            "bathroom": ["ceiling_light", "exhaust_fan"]
        }
        
        # Define semantic mappings
        self.device_synonyms = {
            "lights": ["ceiling_light", "desk_lamp"],  # "lights" can mean multiple devices
            "light": ["ceiling_light"],
            "lamp": ["desk_lamp", "ceiling_light"],
            "fan": ["fan", "exhaust_fan"],  # Context will determine which
            "air": ["ac"],
            "ac": ["ac"],
            "curtains": ["curtain"],
            "blinds": ["curtain"]
        }
        
    def extract_iot_commands_with_llm(self, text_input: str, location: str = "living_room") -> List[Dict[str, Any]]:
        """Extract IoT commands using enhanced LLM understanding"""
        
        # Quick pre-check for non-IoT queries
        if self._is_definitely_non_iot(text_input):
            logger.info(f"Detected non-IoT query, skipping extraction: {text_input[:50]}...")
            return []
        
        # Build comprehensive extraction prompt
        extraction_prompt = self._build_extraction_prompt(text_input, location)
        
        try:
            # Get LLM response
            llm_response = self._query_llm(extraction_prompt)
            
            # Parse and validate commands
            commands = self._parse_llm_response(llm_response)
            
            # Post-process with semantic understanding
            validated_commands = self._validate_and_expand_commands(commands, text_input, location)
            
            if validated_commands:
                logger.info(f"Successfully extracted {len(validated_commands)} commands")
                for cmd in validated_commands:
                    logger.debug(f"  - {cmd['device']} ({cmd['location']}): {cmd['action']}")
            
            return validated_commands
            
        except Exception as e:
            logger.error(f"Error in LLM IoT extraction: {str(e)}")
            return []
    
    def _is_definitely_non_iot(self, text: str) -> bool:
        """Quick check for definitely non-IoT queries"""
        lower_text = text.lower().strip()
        
        # System questions
        if re.search(r'\b(how|what|why|who|when) .*(system|work|created|made)', lower_text):
            return True
        
        # Pure greetings
        if lower_text in ["hello", "hi", "thanks", "thank you", "goodbye"]:
            return True
            
        return False
    
    def _build_extraction_prompt(self, text_input: str, default_location: str) -> str:
        """Build a comprehensive prompt for accurate command extraction"""
        
        # Get available devices for context
        all_devices = set()
        for devices in self.room_devices.values():
            all_devices.update(devices)
        
        prompt = f"""You are an advanced IoT command extraction system. Extract device control commands from natural language.

USER INPUT: "{text_input}"
DEFAULT LOCATION: {default_location}

EXTRACTION PROCESS:
1. Analyze the user's intent - what do they want to happen?
2. Identify target devices (explicit or implied)
3. Determine the action requested
4. Identify locations (explicit, implied, or all)
5. Extract any parameters (brightness, temperature, etc.)

UNDERSTANDING CONTEXT:
- Past tense ("turned on") should be treated as commands
- "Dim" means reduce brightness (action: "dim"), NOT turn on
- "Brighten" means increase brightness (action: "brighten")
- "All" or "whole home" or "everywhere" means every applicable room
- Implied actions: "lights in bedroom" likely means "turn on"

DEVICE MAPPING:
- "lights" (plural) → both ceiling_light AND desk_lamp where available
- "light" (singular) → typically ceiling_light
- "fan" → regular fan in bedrooms/living room, exhaust_fan in kitchen/bathroom
- Common synonyms: lamp→light, AC→air conditioner, blinds→curtains

ROOM COVERAGE:
{json.dumps(self.room_devices, indent=2)}

SCOPE INTERPRETATION:
- Specific room mentioned → use that room only
- "here" or no room → use default location ({default_location})
- "all", "every", "whole house", "everywhere" → all applicable rooms
- Multiple rooms mentioned → extract commands for each

ACTION MAPPING:
- Turn on/off → "on"/"off"
- Dim/brighten → "dim"/"brighten" (NOT on/off)
- Set to X% → "set_brightness" with parameters
- Increase/decrease → "brighten"/"dim"
- Open/close (curtains) → "on"/"off" or "set_position"

CRITICAL UNDERSTANDING RULES:
1. When user says "all lights", generate commands for EVERY light in EVERY room that has lights
2. Understand device context (kitchen fan = exhaust_fan)
3. Don't assume single device when plural is used
4. Respect the user's actual intent (dim ≠ turn on)
5. Include all implied devices

EXAMPLES WITH REASONING:

Input: "Dim bedroom lights"
Reasoning: User wants to reduce brightness of lights in bedroom. "Lights" is plural but bedroom only has ceiling_light as main light.
Output: [{{"device": "ceiling_light", "action": "dim", "location": "bedroom", "parameters": {{}}}}]

Input: "Turn on all lights in the house"
Reasoning: "All lights" + "in the house" = every light device in every room. Must include ceiling_light in all rooms + desk_lamp where available.
Output: [
  {{"device": "ceiling_light", "action": "on", "location": "living_room", "parameters": {{}}}},
  {{"device": "ceiling_light", "action": "on", "location": "bedroom", "parameters": {{}}}},
  {{"device": "desk_lamp", "action": "on", "location": "bedroom", "parameters": {{}}}},
  {{"device": "ceiling_light", "action": "on", "location": "kitchen", "parameters": {{}}}},
  {{"device": "ceiling_light", "action": "on", "location": "study", "parameters": {{}}}},
  {{"device": "desk_lamp", "action": "on", "location": "study", "parameters": {{}}}},
  {{"device": "ceiling_light", "action": "on", "location": "bathroom", "parameters": {{}}}}
]

Input: "Kitchen is smoky, fan please"
Reasoning: Kitchen + fan context = exhaust_fan. Implied action is "turn on".
Output: [{{"device": "exhaust_fan", "action": "on", "location": "kitchen", "parameters": {{}}}}]

Input: "Too bright here"
Reasoning: Complaint about brightness → dim action. "Here" = default location.
Output: [{{"device": "ceiling_light", "action": "dim", "location": "{default_location}", "parameters": {{}}}}]

Input: "Set bedroom lightness to 40%"
Reasoning: Percentage without device or lightness usually means lights. Bedroom context.
Output: [{{"device": "ceiling_light", "action": "set_brightness", "location": "bedroom", "parameters": {{"brightness": 40}}}}]

Input: "I turned off the living room lights"
Reasoning: Past tense but still a command intent. "Lights" typically means ceiling_light.
Output: [{{"device": "ceiling_light", "action": "off", "location": "living_room", "parameters": {{}}}}]

DO NOT extract commands from:
- Questions about how things work
- System inquiries
- General conversation
- Weather, time, news requests

OUTPUT: Only a JSON array of commands. Empty array [] if no commands found.
Think step by step about the user's intent before generating commands."""
        
        return prompt
    
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the extraction prompt"""
        
        if self.api_headers.get("Authorization"):  # Remote API mode
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a precise IoT command extraction system. Analyze user intent step by step. Extract all implied commands. Output only valid JSON arrays."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,  # Low temperature for consistency
                "max_tokens": 1000,
                "stream": False
            }
            
            response = requests.post(
                self.ollama_endpoint,
                json=payload,
                headers=self.api_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_json = response.json()
                return response_json["choices"][0]["message"]["content"]
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                return "[]"
                
        else:  # Local Ollama mode
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,
                "options": {
                    "num_predict": 1000
                }
            }
            
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "[]")
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return "[]"
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse and clean LLM response"""
        try:
            # Clean response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            # Find JSON array
            start_idx = response.find('[')
            end_idx = response.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                response = response[start_idx:end_idx+1]
            
            # Parse JSON
            commands = json.loads(response)
            
            if isinstance(commands, list):
                return commands
            else:
                logger.warning(f"LLM returned non-list: {type(commands)}")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return []
    
    def _validate_and_expand_commands(self, commands: List[Dict[str, Any]], 
                                    original_text: str, 
                                    default_location: str) -> List[Dict[str, Any]]:
        """Validate, normalize, and expand commands based on semantic understanding"""
        
        valid_devices = {"ceiling_light", "desk_lamp", "fan", "exhaust_fan", "ac", "curtain"}
        valid_actions = {"on", "off", "toggle", "set_brightness", "set_temperature", 
                        "set_speed", "set_position", "set_color_temp", "brighten", "dim"}
        valid_locations = set(self.room_devices.keys())
        
        validated_commands = []
        
        for cmd in commands:
            try:
                device = cmd.get("device", "").lower().strip()
                action = cmd.get("action", "").lower().strip()
                location = cmd.get("location", default_location).lower().strip()
                parameters = cmd.get("parameters", {})
                
                # Skip if missing required fields
                if not device or not action:
                    continue
                
                # Normalize location
                location = location.replace(" ", "_")
                if location not in valid_locations:
                    location = default_location
                
                # Validate device exists in room
                if device in valid_devices:
                    if device in self.room_devices.get(location, []):
                        validated_commands.append({
                            "device": device,
                            "action": action,
                            "location": location,
                            "parameters": self._normalize_parameters(action, parameters)
                        })
                    else:
                        logger.warning(f"Device {device} not available in {location}")
                        
            except Exception as e:
                logger.error(f"Error validating command: {e}")
                continue
        
        return validated_commands
    
    def _normalize_parameters(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parameters based on action type"""
        
        normalized = {}
        
        if action == "set_brightness" and "brightness" in parameters:
            brightness = parameters["brightness"]
            if isinstance(brightness, (int, float)):
                normalized["brightness"] = max(0, min(100, int(brightness)))
                
        elif action == "set_temperature" and "temperature" in parameters:
            temp = parameters["temperature"]
            if isinstance(temp, (int, float)):
                normalized["temperature"] = max(16, min(32, int(temp)))
                
        elif action == "set_speed" and "speed" in parameters:
            speed = parameters["speed"]
            if isinstance(speed, (int, float)):
                normalized["speed"] = max(1, min(5, int(speed)))
                
        elif action == "set_position" and "position" in parameters:
            position = parameters["position"]
            if isinstance(position, (int, float)):
                normalized["position"] = max(0, min(100, int(position)))
                
        return normalized

# Backward compatibility functions
def create_llm_extractor(ollama_endpoint: str, model_name: str, api_headers: dict = None):
    """Create LLM extractor instance"""
    return LLMIoTExtractor(ollama_endpoint, model_name, api_headers)

def extract_iot_commands_enhanced_llm(text_input: str, location: str, 
                                     ollama_endpoint: str, model_name: str, 
                                     api_headers: dict = None) -> List[Dict[str, Any]]:
    """Backward compatible function signature"""
    extractor = LLMIoTExtractor(ollama_endpoint, model_name, api_headers)
    return extractor.extract_iot_commands_with_llm(text_input, location)