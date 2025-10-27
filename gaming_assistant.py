#!/usr/bin/env python3
"""
Gaming Assistant - Voice-Activated Cognitive Prosthetic
For veterans with ADHD/PTSD/TBI who play complex strategy games

Features:
- Voice-activated reminders for game events and timers
- Steam integration for game detection (Civilization VI focus)
- Accessible UI designed for executive dysfunction
- Persistent memory across gaming sessions
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import speech_recognition as sr
import pyttsx3
import requests
import threading
import time
import json
import os
import re
from datetime import datetime, timedelta

# Global configuration
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "steam_api_key": "",
    "steam_id": "",
    "reminders": []
}

class Reminder:
    """Data structure for game reminders"""
    def __init__(self, text, reminder_type="event", trigger_time=None):
        self.text = text
        self.reminder_type = reminder_type  # time, resource, event
        self.trigger_time = trigger_time
        self.created_at = datetime.now()

    def to_dict(self):
        """Serialize for JSON storage"""
        return {
            "text": self.text,
            "type": self.reminder_type,
            "trigger_time": self.trigger_time.isoformat() if self.trigger_time else None,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def from_dict(data):
        """Deserialize from JSON"""
        reminder = Reminder(data["text"], data["type"])
        if data.get("trigger_time"):
            reminder.trigger_time = datetime.fromisoformat(data["trigger_time"])
        reminder.created_at = datetime.fromisoformat(data["created_at"])
        return reminder

class GamingAssistant:
    """Main application class"""

    def __init__(self, root):
        self.root = root
        self.root.title("Gaming Assistant - Voice Command Center")
        self.root.geometry("700x600")

        # Print Python version for debugging
        import sys
        print(f"Running with Python {sys.version}")

        # Initialize components
        self.config = self.load_config()
        self.reminders = []
        self.listening = False
        self.game_mode_active = False
        self.current_game = "No game running"

        # Voice components
        try:
            self.recognizer = sr.Recognizer()
            print("✓ Speech recognition initialized")
            self.tts_engine = pyttsx3.init()
            print("✓ Text-to-speech initialized")
            # Adjust TTS speed for clarity (ADHD: slower = easier to process)
            self.tts_engine.setProperty('rate', 150)
        except Exception as e:
            print(f"Audio setup error: {str(e)}")
            import traceback
            traceback.print_exc()

        # Steam polling thread control
        self.steam_poll_active = False

        # Build GUI
        self.build_gui()

        # Load saved reminders
        self.load_reminders_from_config()

        # Start Steam polling if configured
        if self.config["steam_api_key"] and self.config["steam_id"]:
            self.start_steam_polling()

        # Start timer check loop
        self.check_timers()

    def load_config(self):
        """Load or create config file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        """Persist config to disk"""
        # Save current reminders
        self.config["reminders"] = [r.to_dict() for r in self.reminders]
        
        # Write directly to file first
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Force OS to write file to disk

        print(f"Config saved to {CONFIG_FILE}")

    def load_reminders_from_config(self):
        """Restore reminders from saved config"""
        if "reminders" in self.config:
            for r_data in self.config["reminders"]:
                reminder = Reminder.from_dict(r_data)
                self.reminders.append(reminder)
            self.update_reminder_list()

    def build_gui(self):
        """Create ADHD-friendly interface: large text, minimal clutter, voice-first"""

        # Status frame at top
        status_frame = tk.Frame(self.root, bg="#2C3E50", padx=10, pady=10)
        status_frame.pack(fill=tk.X)

        self.status_label = tk.Label(
            status_frame,
            text="🎮 Ready to assist",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2C3E50"
        )
        self.status_label.pack()

        self.game_status_label = tk.Label(
            status_frame,
            text=f"Game: {self.current_game}",
            font=("Arial", 12),
            fg="#ECF0F1",
            bg="#2C3E50"
        )
        self.game_status_label.pack()

        # Main control frame
        control_frame = tk.Frame(self.root, padx=20, pady=10)
        control_frame.pack(fill=tk.X)

        # Large mic button (primary interaction - ADHD: big target, easy to find)
        self.mic_button = tk.Button(
            control_frame,
            text="🎤 HOLD TO SPEAK",
            font=("Arial", 18, "bold"),
            bg="#27AE60",
            fg="white",
            height=2,
            command=self.toggle_listening
        )
        self.mic_button.pack(fill=tk.X, pady=10)

        # Action buttons (secondary - keep simple)
        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            button_frame,
            text="📋 List Reminders",
            font=("Arial", 12),
            command=self.list_reminders_voice,
            bg="#3498DB",
            fg="white"
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tk.Button(
            button_frame,
            text="🗑️ Clear All",
            font=("Arial", 12),
            command=self.clear_all_reminders,
            bg="#E74C3C",
            fg="white"
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # Reminder list display (visual backup for voice)
        list_frame = tk.LabelFrame(self.root, text="Current Reminders", font=("Arial", 12, "bold"), padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.reminder_text = scrolledtext.ScrolledText(
            list_frame,
            font=("Arial", 11),
            height=10,
            wrap=tk.WORD
        )
        self.reminder_text.pack(fill=tk.BOTH, expand=True)

        # Steam setup frame (collapsible)
        setup_frame = tk.LabelFrame(self.root, text="⚙️ Steam Setup (One-time)", font=("Arial", 10), padx=10, pady=5)
        setup_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(setup_frame, text="API Key:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W)
        self.api_key_entry = tk.Entry(setup_frame, width=40, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5)
        self.api_key_entry.insert(0, self.config.get("steam_api_key", ""))

        tk.Label(setup_frame, text="Steam ID:", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W)
        self.steam_id_entry = tk.Entry(setup_frame, width=40)
        self.steam_id_entry.grid(row=1, column=1, padx=5)
        self.steam_id_entry.insert(0, self.config.get("steam_id", ""))

        tk.Button(
            setup_frame,
            text="Save",
            command=self.save_steam_config,
            bg="#16A085",
            fg="white"
        ).grid(row=0, column=2, rowspan=2, padx=5)

        # Exit button
        tk.Button(
            self.root,
            text="Exit",
            font=("Arial", 10),
            command=self.on_closing,
            bg="#95A5A6",
            fg="white"
        ).pack(pady=10)

    def toggle_listening(self):
        """Activate voice listener"""
        if not self.listening:
            self.listening = True
            self.mic_button.config(bg="#E67E22", text="🎤 LISTENING...")
            # Non-blocking: run in thread
            threading.Thread(target=self.listen_for_command, daemon=True).start()

    def listen_for_command(self):
        """Capture voice input and process command"""
        try:
            print("Starting microphone setup...")
            with sr.Microphone() as source:
                print("✓ Microphone initialized")
                # Brief audio cue (ADHD: attention grabber without overload)
                self.play_beep()

                # Adjust for ambient noise
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("✓ Ambient noise adjustment complete")

                # Listen
                print("Listening for command...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                # Convert to text
                print("Converting speech to text...")
                command_text = self.recognizer.recognize_google(audio)
                print(f"Heard: {command_text}")

                # Process command
                self.root.after(0, self.process_command, command_text)

        except sr.WaitTimeoutError:
            self.root.after(0, self.speak, "Didn't hear anything. Try again.")
        except sr.UnknownValueError:
            self.root.after(0, self.speak, "Sorry, didn't catch that. Try again.")
        except Exception as e:
            print(f"Microphone error: {str(e)}")
            import sys
            print("Python path:", sys.executable)
            import traceback
            traceback.print_exc()
            self.root.after(0, self.speak, f"Microphone error: {str(e)}")
        finally:
            # Reset button
            self.root.after(0, self.reset_mic_button)

    def reset_mic_button(self):
        """Return mic button to ready state"""
        self.listening = False
        self.mic_button.config(bg="#27AE60", text="🎤 HOLD TO SPEAK")

    def play_beep(self):
        """Audio cue for attention (ADHD: short beep = clear signal)"""
        # Simple beep using TTS engine (cross-platform)
        # Alternative: could use winsound on Windows, but this is portable
        pass  # pyttsx3 doesn't do beeps easily; skip for MVP

    def speak(self, text):
        """Text-to-speech feedback (blocking call - use in threads if needed)"""
        # Update GUI in main thread
        self.root.after(0, self.status_label.config, {"text": f"🔊 {text}"})
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
        self.root.after(0, self.status_label.config, {"text": "🎮 Ready to assist"})

    def process_command(self, text):
        """Parse spoken command and route to handler"""
        text_lower = text.lower()

        # Log what was heard (debugging)
        print(f"Heard: {text}")

        # Command: List reminders
        if "list" in text_lower and "reminder" in text_lower:
            self.list_reminders_voice()

        # Command: Clear all
        elif "clear all" in text_lower:
            self.clear_all_reminders()

        # Command: Clear specific reminder
        elif "clear" in text_lower and "reminder" in text_lower:
            # Extract what to clear (simple keyword match)
            self.clear_specific_reminder(text)

        # Command: Set reminder
        elif "remind" in text_lower:
            self.add_reminder(text)

        else:
            self.speak("I didn't understand that command. Try: remind me, list reminders, or clear all.")

    def add_reminder(self, text):
        """Parse and add a reminder"""
        # Debug: Print received text
        print(f"Processing reminder text: {text}")
        
        # Check if time-based (e.g., "in 15 minutes" or "in 5 minutes")
        time_match = re.search(r'(?:in|after) (\d+) minutes?', text, re.IGNORECASE)

        if time_match:
            minutes = int(time_match.group(1))
            trigger_time = datetime.now() + timedelta(minutes=minutes)

            # Extract reminder text (after "remind me" and before "in X minutes")
            reminder_text = re.sub(r'.*?(?:remind me|set reminder) (?:to )?', '', text, flags=re.IGNORECASE)
            reminder_text = re.sub(r'(?:in|after) \d+ minutes?.*', '', reminder_text, flags=re.IGNORECASE).strip()

            print(f"Parsed time: {minutes} minutes")
            print(f"Parsed reminder text: {reminder_text}")

            reminder = Reminder(reminder_text, "time", trigger_time)
            self.reminders.append(reminder)

            self.speak(f"Reminder set for {minutes} minutes: {reminder_text}")

        else:
            # Event or resource-based (store as event, manual trigger)
            reminder_text = re.sub(r'.*remind me (to )?', '', text, flags=re.IGNORECASE).strip()

            # Detect if resource-based (keywords: gold, wood, food, etc.)
            if any(word in reminder_text.lower() for word in ["gold", "wood", "food", "iron", "stone", "resource"]):
                reminder = Reminder(reminder_text, "resource")
                self.speak(f"Resource reminder set: {reminder_text}. Say 'trigger' to activate.")
            else:
                reminder = Reminder(reminder_text, "event")
                self.speak(f"Event reminder set: {reminder_text}")

            self.reminders.append(reminder)

        self.update_reminder_list()
        self.save_config()

    def list_reminders_voice(self):
        """Read back all reminders via voice"""
        if not self.reminders:
            self.speak("You have no reminders.")
            return

        # Audio cue
        count = len(self.reminders)
        self.speak(f"You have {count} reminder{'s' if count > 1 else ''}.")

        for i, reminder in enumerate(self.reminders, 1):
            if reminder.reminder_type == "time" and reminder.trigger_time:
                time_left = reminder.trigger_time - datetime.now()
                minutes_left = int(time_left.total_seconds() / 60)
                self.speak(f"{i}. In {minutes_left} minutes: {reminder.text}")
            else:
                self.speak(f"{i}. {reminder.reminder_type.capitalize()}: {reminder.text}")

    def clear_specific_reminder(self, text):
        """Clear reminder by keyword match"""
        # Extract keywords after "clear reminder"
        keywords = re.sub(r'.*clear reminder (about )?', '', text, flags=re.IGNORECASE).strip()

        # Find matching reminder
        for reminder in self.reminders[:]:
            if keywords.lower() in reminder.text.lower():
                self.reminders.remove(reminder)
                self.speak(f"Cleared reminder: {reminder.text}")
                self.update_reminder_list()
                self.save_config()
                return

        self.speak("No matching reminder found.")

    def clear_all_reminders(self):
        """Remove all reminders"""
        count = len(self.reminders)
        self.reminders.clear()
        self.update_reminder_list()
        self.save_config()
        self.speak(f"Cleared {count} reminder{'s' if count != 1 else ''}.")

    def update_reminder_list(self):
        """Refresh GUI list display"""
        self.reminder_text.delete(1.0, tk.END)

        if not self.reminders:
            self.reminder_text.insert(tk.END, "No reminders set.\n")
            return

        for i, reminder in enumerate(self.reminders, 1):
            if reminder.reminder_type == "time" and reminder.trigger_time:
                time_left = reminder.trigger_time - datetime.now()
                minutes_left = max(0, int(time_left.total_seconds() / 60))
                self.reminder_text.insert(tk.END, f"{i}. [TIME - {minutes_left}m] {reminder.text}\n")
            else:
                self.reminder_text.insert(tk.END, f"{i}. [{reminder.reminder_type.upper()}] {reminder.text}\n")

    def check_timers(self):
        """Periodically check for triggered time-based reminders"""
        now = datetime.now()

        for reminder in self.reminders[:]:
            if reminder.reminder_type == "time" and reminder.trigger_time:
                if now >= reminder.trigger_time:
                    # Trigger alert
                    self.trigger_reminder_alert(reminder)
                    self.reminders.remove(reminder)

        self.update_reminder_list()
        self.save_config()

        # Check again in 5 seconds
        self.root.after(5000, self.check_timers)

    def trigger_reminder_alert(self, reminder):
        """Alert user about triggered reminder (voice + popup)"""
        # Voice alert
        threading.Thread(target=self.speak, args=(f"Reminder: {reminder.text}",), daemon=True).start()

        # Popup (ADHD: visual + audio redundancy helps)
        messagebox.showinfo("⏰ Reminder", reminder.text)

    def save_steam_config(self):
        """Save Steam API credentials"""
        api_key = self.api_key_entry.get().strip()
        steam_id = self.steam_id_entry.get().strip()

        if not api_key or not steam_id:
            messagebox.showwarning("Incomplete", "Please enter both API key and Steam ID.")
            return

        # Immediately save to disk before starting Steam
        self.config["steam_api_key"] = api_key
        self.config["steam_id"] = steam_id
        
        # Write directly to file first
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Force OS to write file to disk

        print(f"Steam credentials saved to {CONFIG_FILE}")
        print(f"API Key: {api_key[:5]}...")
        print(f"Steam ID: {steam_id}")

        # Verify the save by reading back
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                if (saved_config["steam_api_key"] == api_key and 
                    saved_config["steam_id"] == steam_id):
                    print("✓ Config file verified")
                else:
                    print("✗ Config verification failed")
                    return
        except Exception as e:
            print(f"Config verification error: {str(e)}")
            return

        self.speak("Steam settings saved. Starting game detection.")
        self.start_steam_polling()

    def start_steam_polling(self):
        """Begin polling Steam API for game status"""
        if not self.steam_poll_active:
            self.steam_poll_active = True
            threading.Thread(target=self.poll_steam_api, daemon=True).start()

    def poll_steam_api(self):
        """Check Steam API every 30 seconds for running game"""
        while self.steam_poll_active:
            try:
                api_key = self.config.get("steam_api_key")
                steam_id = self.config.get("steam_id")

                if not api_key or not steam_id:
                    time.sleep(30)
                    continue

                # API call
                url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}"
                response = requests.get(url, timeout=10)
                data = response.json()

                # Parse response
                if "response" in data and "players" in data["response"] and len(data["response"]["players"]) > 0:
                    player = data["response"]["players"][0]

                    # Check if game is running
                    if "gameextrainfo" in player:
                        game_name = player["gameextrainfo"]

                        # Check if Civilization VI
                        if "Civilization VI" in game_name or "Civ VI" in game_name:
                            self.root.after(0, self.update_game_status, game_name, True)
                        else:
                            self.root.after(0, self.update_game_status, game_name, False)
                    else:
                        self.root.after(0, self.update_game_status, "No game running", False)
                else:
                    self.root.after(0, self.update_game_status, "API error - check credentials", False)

            except requests.exceptions.RequestException:
                self.root.after(0, self.update_game_status, "Steam API unreachable", False)
            except Exception as e:
                self.root.after(0, self.update_game_status, f"Error: {str(e)[:30]}", False)

            # Wait 30 seconds before next poll
            time.sleep(30)

    def update_game_status(self, game_name, is_civ6):
        """Update GUI with detected game"""
        self.current_game = game_name
        self.game_mode_active = is_civ6

        if is_civ6:
            self.game_status_label.config(text=f"🎮 Game: {game_name} (Detected!)", fg="#2ECC71")
        else:
            self.game_status_label.config(text=f"Game: {game_name}", fg="#ECF0F1")

    def on_closing(self):
        """Cleanup on app exit"""
        self.steam_poll_active = False
        self.save_config()
        self.root.destroy()


def main():
    """Entry point"""
    print("Gaming Assistant - Voice Command Center")
    print("For veterans with ADHD/PTSD/TBI who play complex strategy games")
    print("=" * 50)

    import sys
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")

    # Check dependencies (basic test)
    try:
        import speech_recognition
        print("✓ Speech Recognition loaded")
        import pyaudio
        print(f"✓ PyAudio loaded")
        import pyttsx3
        print("✓ pyttsx3 loaded")
        import requests
        print("✓ Requests loaded")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Run: pip install SpeechRecognition pyttsx3 pyaudio requests")
        return

    # Launch GUI
    root = tk.Tk()
    app = GamingAssistant(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    print("✓ App ready - GUI launched")
    print("\nTest commands:")
    print("- 'Remind me to build a forge when I have 500 gold'")
    print("- 'In 15 minutes remind me to check food stores'")
    print("- 'List my reminders'")
    print("- 'Clear all'")

    root.mainloop()


if __name__ == "__main__":
    main()