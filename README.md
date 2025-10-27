# Veteran Gaming Assistant

A voice-activated cognitive prosthetic designed specifically for veterans with ADHD, PTSD, and TBI who play complex strategy games. Acts as an external memory aid to prevent forgotten critical tasks that can ruin long gaming sessions.

## 🎯 Features

- **Voice Commands**: Set reminders without breaking game immersion
- **Timer Alerts**: "In 15 minutes remind me to check food stores"
- **Resource Tracking**: "Remind me to build 3 mines after getting Bronze Working"
- **Steam Integration**: Auto-detects Civilization VI
- **Accessible UI**: Designed for executive dysfunction
- **Persistent Memory**: Saves reminders between sessions

## 🎮 Why This Helps Veterans

Built by a disabled Marine vet, for vets. Games are therapy, community, and mental exercise.

- **Voice-First**: Speaking is faster than typing, maintains game immersion
- **Audio Cues**: Breaks through "bread brain" fog
- **Simple Commands**: Reduces cognitive load
- **Visual + Audio**: Redundant alerts ensure you catch important reminders
- **Persistent Storage**: External memory that survives crashes or distractions

## ⚙️ Installation

### Prerequisites

- Python 3.7 or higher
- Working microphone
- Speakers/headphones
- Windows, Mac, or Linux
- Internet (only for Steam features)

### Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/wyldephyre/veteran-gaming-assistant.git
   cd veteran-gaming-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   **Platform-specific PyAudio notes:**
   - **Windows**: If pip fails, download wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
   - **Mac**: `brew install portaudio` then `pip install pyaudio`
   - **Linux**: `sudo apt-get install python3-pyaudio portaudio19-dev`

3. Run the app:
   ```bash
   python gaming_assistant.py
   ```

## 🎤 Voice Commands

Click the "HOLD TO SPEAK" button and say:

### Time-Based (Auto-triggered)
- "Remind me in 15 minutes to check food stores"
- "In 20 minutes remind me to scout north"
- "Remind me in 5 minutes to build a settler"

### Resource-Based
- "Remind me to build a forge when I have 500 gold"
- "Remind me to research sailing after Bronze Working"

### Event-Based
- "Remind me to defend the eastern border after turn 50"
- "Remind me to build 3 mines in the hills"

### List & Clear
- "List my reminders"
- "Clear all"
- "Clear reminder about mines"

## 🎮 Steam Integration

1. Get your [Steam API Key](https://steamcommunity.com/dev/apikey)
2. Find your [Steam ID](https://steamid.io/)
3. Enter both in the app's Steam Setup section
4. App will detect when Civilization VI is running

## 🔧 Troubleshooting

### Audio Issues
- Ensure mic is set as default input device
- Check system permissions for mic access
- Try running mic test: `python -m speech_recognition`

### Steam Detection
- Verify API key and Steam ID are correct
- Make sure Steam profile is public
- Check internet connection

### Dependencies
- Run `pip install --upgrade -r requirements.txt`
- For PyAudio issues, use platform-specific instructions above

## 🛣️ Roadmap

1. **Phase 2**
   - Offline voice recognition
   - Support for more games (Stellaris, Total War)
   - Custom reminder templates

2. **Phase 3**
   - Game log parsing
   - Automatic resource triggers
   - Advanced Civ VI integration

3. **Phase 4**
   - Multi-game profiles
   - Cloud sync
   - Mobile companion app

## 🎖️ For Veterans

This tool is built by a disabled Marine vet, for vets. The goal is affordable cognitive prosthetics that make gaming accessible again.

No moralizing, just function. This is a tool - use it how it helps you.

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

## 🔒 License

For personal testing use. Commercial distribution TBD (veterans will get discounts).

## 💬 Support

- Check troubleshooting section above
- Review console output for errors
- Test with simple commands first
- Submit issues via GitHub

---

Game on, and let the assistant handle the memory work! 🎮