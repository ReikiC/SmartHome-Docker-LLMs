# Universal IoT Command Format Specification

## Overview
This specification defines a standardized format for IoT device control commands in the AI Smart Home Assistant system. The format ensures consistent command parsing across different input methods and languages.

## Command Structure

### Basic Format
```json
{
  "device": "string",      // Device type identifier
  "action": "string",      // Action to perform
  "location": "string",    // Target room/location
  "parameters": {}         // Optional action-specific parameters
}
```

### Multiple Commands
Commands are always returned as an array, even for single commands:
```json
[
  {
    "device": "ceiling_light",
    "action": "on",
    "location": "living_room",
    "parameters": {}
  }
]
```

## Standardized Device Types

| Device Type | Description | Common Aliases |
|------------|-------------|----------------|
| `ceiling_light` | Main room lighting | lights, main light, overhead light |
| `desk_lamp` | Secondary lighting | table lamp, reading lamp, lamp |
| `ac` | Air conditioning | air conditioner, AC, cooling, heating |
| `fan` | Room fan | ceiling fan, room fan |
| `exhaust_fan` | Ventilation fan | bathroom fan, kitchen fan |
| `curtain` | Window coverings | blinds, shades |

## Standardized Actions

### Basic Control Actions
| Action | Description | Required Parameters | Applicable Devices |
|--------|-------------|-------------------|-------------------|
| `on` | Turn device on | None | All devices |
| `off` | Turn device off | None | All devices |
| `toggle` | Toggle state | None | All devices |

### Parametric Actions
| Action | Description | Parameters | Value Range | Applicable Devices |
|--------|-------------|------------|-------------|-------------------|
| `set_brightness` | Set brightness level | `brightness` | 0-100 | ceiling_light, desk_lamp |
| `set_temperature` | Set temperature | `temperature` | 16-32°C | ac |
| `set_speed` | Set fan speed | `speed` | 1-5 | fan, exhaust_fan |
| `set_position` | Set position | `position` | 0-100% | curtain |
| `set_color_temp` | Set color temperature | `color_temp` | 2700-6500K | ceiling_light |

### Convenience Actions
| Action | Description | Implicit Behavior | Applicable Devices |
|--------|-------------|------------------|-------------------|
| `brighten` | Increase brightness | +20% | ceiling_light, desk_lamp |
| `dim` | Decrease brightness | -20% | ceiling_light, desk_lamp |

## Location Standardization

### Standard Room Names
| Standard Format | Common Variations |
|----------------|-------------------|
| `living_room` | living room, livingroom, lounge |
| `bedroom` | bed room, master bedroom |
| `kitchen` | cooking area |
| `study` | office, study room |
| `bathroom` | bath room, restroom, washroom |

### Special Locations
| Location | Description |
|----------|-------------|
| `all` | All rooms/devices |
| `current` | User's current location |

## Command Examples

### Simple Commands
```json
// Turn on living room lights
{
  "device": "ceiling_light",
  "action": "on",
  "location": "living_room",
  "parameters": {}
}

// Set bedroom AC to 24°C
{
  "device": "ac",
  "action": "set_temperature",
  "location": "bedroom",
  "parameters": {"temperature": 24}
}

// Dim study lamp
{
  "device": "desk_lamp",
  "action": "dim",
  "location": "study",
  "parameters": {}
}
```

### Compound Commands
```json
// "Turn on kitchen lights and exhaust fan"
[
  {
    "device": "ceiling_light",
    "action": "on",
    "location": "kitchen",
    "parameters": {}
  },
  {
    "device": "exhaust_fan",
    "action": "on",
    "location": "kitchen",
    "parameters": {}
  }
]

// "Set all lights to 50% brightness"
[
  {
    "device": "ceiling_light",
    "action": "set_brightness",
    "location": "all",
    "parameters": {"brightness": 50}
  }
]
```

### Scene-like Commands
```json
// "Movie mode: dim lights and close curtains in living room"
[
  {
    "device": "ceiling_light",
    "action": "set_brightness",
    "location": "living_room",
    "parameters": {"brightness": 20}
  },
  {
    "device": "curtain",
    "action": "set_position",
    "location": "living_room",
    "parameters": {"position": 0}
  }
]
```

## Natural Language Processing

### Supported Input Patterns

#### English
- "Turn on the lights" → ceiling_light on
- "Set AC to 25 degrees" → ac set_temperature 25
- "Open bedroom curtains halfway" → curtain set_position 50
- "Dim all lights" → ceiling_light dim (all rooms)
- "Turn off everything" → all devices off (all rooms)

#### Multi-room Commands
- "Turn on kitchen lights and bedroom fan"
- "Set living room AC to 24 and bedroom AC to 22"
- "Close all curtains"

#### Contextual Understanding
- Temperature: "25", "25 degrees", "25°C", "twenty-five degrees"
- Brightness: "50%", "half brightness", "50 percent"
- Position: "fully open" (100%), "closed" (0%), "halfway" (50%)

## Error Handling

### Invalid Commands
Commands that cannot be parsed return an empty array:
```json
[]
```

### Partial Success
Valid commands are extracted even if some parts of the input cannot be parsed:
```json
// Input: "Turn on lights and do something undefined"
[
  {
    "device": "ceiling_light",
    "action": "on",
    "location": "living_room",
    "parameters": {}
  }
]
```

## Implementation Guidelines

### For Developers

1. **Validation**: Always validate commands against the schema before execution
2. **Defaults**: Use sensible defaults (e.g., current room if location not specified)
3. **Range Checking**: Ensure parameters are within acceptable ranges
4. **Graceful Degradation**: Handle missing parameters gracefully

### For LLM Prompts

1. **Clarity**: Be explicit about the expected format
2. **Examples**: Provide diverse examples covering edge cases
3. **Constraints**: Clearly state value ranges and device-action compatibility
4. **Output Format**: Emphasize JSON-only output, no explanatory text

## Future Extensions

### Planned Enhancements
- Time-based commands: "Turn on lights at 6 PM"
- Conditional commands: "Turn on AC if temperature > 28°C"
- Group controls: "Turn off all devices except security"
- Custom device types via configuration
- Multi-language support with automatic translation

### Backward Compatibility
All future extensions will maintain backward compatibility with the current format through:
- Optional fields for new features
- Default behaviors for legacy systems
- Version indicators in command metadata
