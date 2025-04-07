import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import sys
import glob
import datetime
import cv2
import pytesseract
import pyautogui
import random
import numpy as np
from difflib import get_close_matches
from app.models import search_notes
import tkinter as tk
from tkinter import messagebox

engine = pyttsx3.init()

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()

def show_popup(options):
    """Displays a popup for multiple notes."""
    root = tk.Tk()
    root.withdraw()
    selected = messagebox.askquestion("Multiple Notes Found", "Do you want to see all notes?")
    if selected == "yes":
        for note in options:
            print(f"Title: {note[1]}\nContent: {note[2]}\n")
            speak(f"Title: {note[1]}. Content: {note[2]}.")
    root.destroy()

def search_my_name():
    """Searches for notes related to name or FIRs."""
    keywords = ["Siddharth", "mummy", "papa", "FIR"]
    found_notes = []
    
    for keyword in keywords:
        results = search_notes(keyword)
        if results:
            found_notes.extend(results)

    if found_notes:
        if len(found_notes) == 1:
            speak(f"One note found: {found_notes[0][1]} - {found_notes[0][2]}")
        else:
            show_popup(found_notes)
    else:
        speak("No notes found related to your search.")

# Set Tesseract OCR path (update this path based on your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Contact List (Case-Insensitive)
contacts = {
    "mummy": "+91 99974 11791",
    "papa": "+91 9837248208",
    "kanishk": "+91 82730 56607",
    "sir": "+918888888888",
    "doctor": "+91 9837248208"
}

# Convert contacts to lowercase for better matching
contacts_lower = {name.lower(): number for name, number in contacts.items()}

# Initialize recognizer & text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty("rate", 200)

DAILY_DIARY_PATH = "backend/DailyDiary/"
detected_links = []  # Store detected URLs from the screen

def speak(text):
    """Speak function with a non-blocking event loop."""
    engine.say(text)
    engine.runAndWait()

def recognize_speech():
    """Listen for voice commands with improved speed and error handling."""
    with sr.Microphone() as source:
        recognizer.pause_threshold = 0.5
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=6)
            command = recognizer.recognize_google(audio).strip().lower()
            print(f"DEBUG: You said -> {command}")  
            
            if command == "stop":
                speak("Okay, Goodbye!")
                sys.exit(0)
                
            return command
        except sr.UnknownValueError:
            print("Sorry, I didn't understand that.")
        except sr.RequestError:
            print("Error with speech recognition service.")
        except sr.WaitTimeoutError:
            print("Listening timed out. Please speak again.")
        return ""

def find_closest_match(name):
    """Find the closest contact name match using fuzzy matching."""
    matches = get_close_matches(name, contacts_lower.keys(), n=1, cutoff=0.5)
    print(f"DEBUG: Closest match found -> {matches}")  
    return matches[0] if matches else None

def read_latest_diary_entry():
    """Reads the most recent diary entry and speaks it."""
    diary_files = sorted(glob.glob(DAILY_DIARY_PATH + "*.txt"), key=os.path.getmtime, reverse=True)
    
    if not diary_files:
        speak("You have no diary entries yet.")
        return
    
    latest_file = diary_files[0]  
    with open(latest_file, "r", encoding="utf-8") as file:
        content = file.read()
    
    speak(f"Your last diary entry says: {content}")

def read_diary_by_date(date_str):
    """Reads a diary entry for the given date."""
    try:
        date_obj = datetime.datetime.strptime(date_str, "%B %d %Y")
        file_name = f"{date_obj.strftime('%B_%d_%Y')}.txt"
        file_path = os.path.join(DAILY_DIARY_PATH, file_name)
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            speak(f"Your diary entry for {date_str} says: {content}")
        else:
            speak(f"You have no diary entry for {date_str}.")
    
    except ValueError:
        speak("Sorry, I couldn't understand the date format. Please say it clearly.")

def capture_screen():
    """Captures the screen and extracts text including URLs."""
    global detected_links
    detected_links = []  # Reset detected links

    speak("Scanning your screen for links.")
    
    # Capture screenshot
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    # Extract text using OCR
    extracted_text = pytesseract.image_to_string(screenshot)

    # Extract URLs from text
    words = extracted_text.split()
    for word in words:
        if word.startswith("http") or word.startswith("www."):
            detected_links.append(word)

    if detected_links:
        speak(f"I found {len(detected_links)} links on your screen.")
    else:
        speak("No links detected on your screen.")

def open_detected_link():
    """Opens the first detected link or asks user for selection if multiple links exist."""
    if not detected_links:
        speak("No links are detected yet. Please try again after opening a webpage.")
        return

    if len(detected_links) == 1:
        speak(f"Opening {detected_links[0]}")
        webbrowser.open(detected_links[0])
    else:
        speak("Multiple links detected. Say the number of the link you want to open.")
        for i, link in enumerate(detected_links, 1):
            print(f"{i}. {link}")
            speak(f"Option {i}, {link}")

        selected_option = recognize_speech()
        if selected_option.isdigit():
            index = int(selected_option) - 1
            if 0 <= index < len(detected_links):
                speak(f"Opening {detected_links[index]}")
                webbrowser.open(detected_links[index])
            else:
                speak("Invalid selection. Please try again.")
        else:
            speak("Sorry, I couldn't understand the selection.")

# --------------- MARKED LOCATION: Updated execute_command Function ----------------

def execute_command(command):
    """Execute voice commands efficiently with optimized handling."""

    command = command.strip().lower()  # Normalize command for better matching
    
    
    
   # === CALL FEATURE ===
    if command.startswith("call "):
        contact_name = command.replace("call ", "").strip()
        matched_contact = find_closest_match(contact_name)

        if matched_contact:
            contact_number = contacts_lower[matched_contact]
            speak(f"Calling {matched_contact} now.")

            # Platform-independent calling mechanism
            if sys.platform.startswith("win"):
                os.system(f"start tel:{contact_number}")  # Windows
            elif sys.platform.startswith("darwin"):
                os.system(f"open tel://{contact_number}")  # macOS
            elif sys.platform.startswith("linux"):
                os.system(f"xdg-open tel://{contact_number}")  # Linux (GNOME/KDE)

        else:
            speak(f"I couldn't find {contact_name} in your contacts. Please try again.")

    # === BASIC COMMANDS ===
    if command == "hey system":
        speak("Yes, I'm listening.")

    elif command == "stop":
        speak("Okay, Goodbye!")
        sys.exit(0)

    # === SYSTEM CONTROL COMMANDS ===
    elif command == "open chrome":
        speak("Opening Chrome.")
        os.system("start chrome")

    elif command == "open notepad":
        speak("Opening Notepad.")
        os.system("notepad")

    elif command == "open calculator":
        speak("Opening Calculator.")
        os.system("calc")

    elif command == "shutdown":
        speak("Shutting down your PC.")
        os.system("shutdown /s /t 3")

    elif command == "restart":
        speak("Restarting your PC.")
        os.system("shutdown /r /t 3")

    # === SCREEN SCANNER COMMANDS ===
    elif command == "scan screen":
        capture_screen()

    elif command == "open link":
        open_detected_link()

    elif command == "show detected links":
        if detected_links:
            speak(f"I found {len(detected_links)} links. Here they are:")
            for i, link in enumerate(detected_links, 1):
                print(f"{i}. {link}")
                speak(f"Link {i}: {link}")
        else:
            speak("No links detected on your screen.")

    elif command.startswith("select link number "):
        try:
            index = int(command.replace("select link number ", "")) - 1
            if 0 <= index < len(detected_links):
                speak(f"Opening {detected_links[index]}")
                webbrowser.open(detected_links[index])
            else:
                speak("Invalid link number. Please try again.")
        except ValueError:
            speak("I couldn't understand the number. Please try again.")

    # === WEB SEARCH & BROWSING COMMANDS ===
    elif command.startswith("search "):
        query = command.replace("search ", "").strip()
        speak(f"Searching for {query} on Google.")
        webbrowser.open(f"https://www.google.com/search?q={query}")

    elif command == "open youtube":
        speak("Opening YouTube.")
        webbrowser.open("https://www.youtube.com")

    elif command.startswith("play "):
        song = command.replace("play ", "").strip()
        speak(f"Playing {song} on YouTube.")
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")

    elif command == "open gmail":
        speak("Opening Gmail.")
        webbrowser.open("https://mail.google.com")

    # === DAILY DIARY COMMANDS ===
    elif command == "create diary entry":
        speak("Starting a new diary entry for today.")
        file_name = datetime.datetime.now().strftime("%B_%d_%Y") + ".txt"
        file_path = os.path.join(DAILY_DIARY_PATH, file_name)
        
        speak("What would you like to write?")
        diary_entry = recognize_speech()
        
        if diary_entry:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(diary_entry)
            speak("Diary entry saved successfully.")
        else:
            speak("No text detected. Entry was not saved.")

    elif command == "read my last diary entry":
        read_latest_diary_entry()

    elif command == "list all diary entries":
        diary_files = sorted(glob.glob(DAILY_DIARY_PATH + "*.txt"), key=os.path.getmtime)
        if diary_files:
            speak("Here are your diary entries:")
            for file in diary_files:
                print(file.split("/")[-1])
                speak(file.split("/")[-1])
        else:
            speak("You have no diary entries yet.")

    # === VOICE ASSISTANT INTERACTION COMMANDS ===
    elif command == "what is today's date?":
        today = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today's date is {today}.")

    elif command == "what time is it?":
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {current_time}.")

    elif command == "tell me a joke":
        jokes = [
            "Why don't programmers like nature? Because it has too many bugs.",
        "Why did the computer catch a cold? It left its Windows open.",
        "Why do Java developers wear glasses? Because they don't see sharp.",
        "Why was the function so sad? Because it didn't return anything.",
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "How do you comfort a JavaScript bug? You console it.",
        "Why was the developer broke? Because he used up all his cache.",
        "Why did the programmer quit his job? He didn't get arrays.",
        "What is a programmer's favorite place to hang out? The Foo Bar.",
        "Why did the database administrator break up with the girl? She had too many relations.",
        "Why did the Python programmer break up? Because he had too many 'if' statements and not enough 'else'.",
        "Why do Python programmers prefer snakes? Because they don't have semicolons!",
        ]
        speak(np.random.choice(jokes))

    elif command == "who are you?":
        speak("I am your AI assistant, here to help you with your tasks and make your life easier!")

    else:
        speak("I'm sorry, I didn't understand that command.")

# -----------------------------------------------------------------------------------

# Start listening for commands
speak("Hey, I'm ready! Say a command.")
while True:
    command = recognize_speech()
    if command:
        execute_command(command)
