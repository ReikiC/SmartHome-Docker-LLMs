# Smart Home System Test Questions

## System Questions (10 Questions for Visitors)

1. "Who are the creaters of this project?"
2. "Do you think you are smarter than Alexa? If so, what makes you smarter?"
3. "Why you can understand my intentions (commands)?"
4. "How do the system works?"
5. "Can you work without internet?"
6. "You said you can work without internet, how about the remote API mode?"
7. "What's your advantage compare with traditional methods?"
8. “What's technologies been applied for this project?”
9. "Tell me something about your hardware."
10. "What's the framework of this project?"


## Device Control Commands (15 Commands for Lights & Fans)

1. "Turn on the lights"
2. "Living room fan on"
3. "Dim bedroom lights"
4. "Whole home All lights off"
5. "Set Kitchen fan speed 3"
6. "Brighten study lights"
7. "Bathroom exhaust on"
8. "Bedroom lights 40%"
9. "Turn off all fans in the home"
10. "Maximum fan speed"
11. "Lights on everywhere"
12. "Living room lights and fan"
13. "Half brightness please"
14. "Kitchen lights off"
15. "Bedroom fan slow"

---

## Testing Notes

### Key Features to Demonstrate:
- **Semantic Understanding**: The system understands intent, not just keywords
- **Two-stage LLM Processing**: First extracts intent, then generates natural response
- **Edge Computing**: All processing happens locally for privacy and speed
- **Multi-room Control**: Can control devices across all rooms
- **Natural Language**: Understands various ways of expressing the same command

### Expected Behaviors:
- System questions should trigger informative responses about architecture
- Device commands should result in acknowledgment of actions taken
- Mixed commands (lights + fans) should handle both devices correctly
- Ambiguous commands should still work through semantic understanding