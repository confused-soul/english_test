import google.generativeai as genai
import streamlit as st
import sounddevice as sd
import pyttsx3
import numpy as np
import wave
import re
import random
import os
import time
from datetime import datetime
from questions import reading, repeating, jumbled, qna, stories, hr
import asyncio
# Access your API key as an environment variable
genai.configure(api_key=st.secrets["api_key"])

# Choose a model that's appropriate for your use case
model = genai.GenerativeModel('gemini-1.5-flash')

if "count" not in st.session_state:
    st.session_state.count = 0

if "instructions" not in st.session_state:
    st.session_state.instructions = """
### Section 1: Reading
In this section, you will read aloud a set of eight sentences displayed on your screen. This evaluates your pronunciation, clarity, and fluency in spoken English.
Answer Duration: 10 seconds
**Tips:**
1. Practice Aloud: Regularly read sentences aloud to enhance your fluency and pronunciation.
2. Focus on Clarity: Speak clearly and at a moderate pace to ensure your words are easily understood.
3. Emphasize Key Words: Use intonation to highlight important words in each sentence.

---

### Section 2: Repeating Sentences
You will listen to 16 audio sentences and repeat them exactly as you heard them. This tests your listening skills, aural comprehension, and pronunciation accuracy.
Answer Duration: 15 seconds
**Tips:**
1. Listen Actively: Concentrate on the audio and visualize the sentence as you listen.
2. Repeat Immediately: Echo the sentence right after hearing it to reinforce your memory.
3. Focus on Pronunciation: Pay attention to the pronunciation and rhythm of the sentences.

---

### Section 3: Jumbled Sentences
In this section, you will unscramble 10 jumbled audio sentences and read them aloud. This assesses your cognitive ability to recognize sentence structure and organization.
Answer Duration: 30 seconds
**Tips:**
1. Look for Clues: Identify keywords that indicate the beginning or end of a sentence.
2. Practice Unscrambling: Engage in exercises that involve rearranging sentences to build your skills.
3. Visualize the Structure: Picture the sentence in your mind to help rearrange the jumbled parts effectively.

---

### Section 4: Question and Answer
You will listen to 24 audio questions and respond with brief answers, typically one or two words. This evaluates your ability to answer clearly and succinctly.
Answer Duration: 15 seconds
**Tips:**
1. Keep Responses Concise: Answer clearly and directly to maintain brevity.
2. Familiarize with Common Questions: Practice responses to general questions to boost your confidence.
3. Stay Composed: Take a moment to think before responding to ensure clarity.

---

### Section 5: Storytelling
You will listen to a short story twice and then retell it in your own words within a specified time. This measures your memorization skills and ability to narrate effectively.
Answer Duration: 60 seconds
**Tips:**
1. Summarize Key Points: Focus on the main ideas of the story for easier recall.
2. Organize Your Thoughts: Structure your retelling with a clear beginning, middle, and end.
3. Practice Regularly: Retell various stories to enhance your ability to recall and narrate.

---

### Section 6: Open Questions
This section simulates a virtual HR interview, where you will answer open-ended questions in up to a minute. It assesses your communication skills and self-awareness regarding your experiences and motivations.
Answer Duration: 60 seconds
**Tips:**
1. Reflect on Your Experiences: Think about relevant experiences to share in your answers.
2. Practice Articulation: Speak your responses out loud to become comfortable expressing your thoughts.
3. Maintain a Positive Tone: Frame your answers positively, emphasizing your strengths and achievements.
"""

q1 = st.sidebar.number_input("Reading:", min_value=1, step=1, value=8)
q2 = st.sidebar.number_input("Repeating:", min_value=1, step=1, value=16)
q3 = st.sidebar.number_input("Jumbled:", min_value=1, step=1, value=10)
q4 = st.sidebar.number_input("QnA:", min_value=1, step=1, value=24)
q5 = st.sidebar.number_input("StoryTelling:", min_value=1, step=1, value=2)
q6 = st.sidebar.number_input("Open Questions:", min_value=1, step=1, value=2)

if "q1" not in st.session_state:
    st.session_state.q1 = 8
    st.session_state.q2 = 16
    st.session_state.q3 = 10
    st.session_state.q4 = 24
    st.session_state.q5 = 2
    st.session_state.q6 = 2

# Create a temporary directory to save the audio file
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# Streamlit app layout
st.title("Communication Test")

st.write(st.session_state.instructions)

sections = [
    "Section 1: Reading (8 Sentences)", 
    "Section 2: Repeating Sentences (16 Sentences)", 
    "Section 3: Jumbled Sentences (10 Sentences)",
    "Section 4: Question and Answer (24 Questions)",
    "Section 5: Storytelling (2 Questions)",
    "Section 6: Open Questions (2 Questions)"
]

def choose_random_items(original_list, n):
    if n > len(original_list):
        raise ValueError("n must not be greater than the length of the original list.")
    return random.sample(original_list, n)

# Choose random items for each section
if "quests" not in st.session_state:
    st.session_state.quests = [
        choose_random_items(reading, 8),
        choose_random_items(repeating, 16),
        choose_random_items(jumbled, 10),
        choose_random_items(qna, 24),
        choose_random_items(stories, 2),
        choose_random_items(hr, 2)
    ]

duration = [10, 15, 30, 10, 60, 60]

if "test_end" not in st.session_state:
    st.session_state.test_end = False

if "test_started" not in st.session_state:
    st.session_state.test_started = False
    st.session_state.readable = True
    st.session_state.current_section_no = 0  # Start from section 0
    st.session_state.current_question_no = 0
    st.session_state.current_section = sections[st.session_state.current_section_no]
    st.session_state.current_question = f"Question Number: {st.session_state.current_question_no + 1}/{len(st.session_state.quests[st.session_state.current_section_no])}: {st.session_state.quests[st.session_state.current_section_no][st.session_state.current_question_no]}"

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []


if st.sidebar.button("Update Questions"):
    st.session_state.q1 = q1
    st.session_state.q2 = q2
    st.session_state.q3 = q3
    st.session_state.q4 = q4
    st.session_state.q5 = q5
    st.session_state.q6 = q6
    st.session_state.quests = [
        choose_random_items(reading, st.session_state.q1),
        choose_random_items(repeating, st.session_state.q2),
        choose_random_items(jumbled, st.session_state.q3),
        choose_random_items(qna, st.session_state.q4),
        choose_random_items(stories, st.session_state.q5),
        choose_random_items(hr, st.session_state.q6)
    ]
    st.session_state.count = 0
    st.session_state.evaluations = []
    st.session_state.test_end = False
    st.session_state.test_started = False
    st.session_state.current_section_no = 0
    st.session_state.current_question_no = 0
    st.session_state.current_section = sections[st.session_state.current_section_no]
    st.session_state.current_question = f"Question Number: {st.session_state.current_question_no + 1}/{len(st.session_state.quests[st.session_state.current_section_no])}: {st.session_state.quests[st.session_state.current_section_no][st.session_state.current_question_no]}"
    st.rerun()  

# Sidebar for showing evaluations
st.sidebar.write("Remarks:")
st.sidebar.write("----------")
for eval in st.session_state.evaluations:
    st.sidebar.write(eval)

# Define the audio recording function
def record_audio(duration=5, fs=44100):
    st.write("Recording audio...")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='int16')
    sd.wait()  # Wait until the recording is finished
    st.write("Recording finished.")
    return audio_data

# Function to save the recorded audio to a WAV file with a timestamp
def save_audio(audio_data, fs=44100):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'recorded_audio_{timestamp}.wav'
    
    with wave.open(os.path.join(TEMP_DIR, filename), 'wb') as wf:
        wf.setnchannels(2)  # Stereo
        wf.setsampwidth(2)  # 16 bits
        wf.setframerate(fs)
        wf.writeframes(audio_data.tobytes())
    
    return filename  # Return the filename for playback

# Function to perform text-to-speech
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 120)  # Set speech rate
    engine.setProperty('volume', 0.9)  # Set volume level
    engine.say(text)  # Add text to the speech queue
    engine.runAndWait()  # Wait for the speech to finish
    engine.stop()  # Stop the speech engine
    st.session_state.readable = True
    st.rerun()

def update():
    global end_flag
    st.session_state.current_question_no += 1
    if st.session_state.current_question_no >= len(st.session_state.quests[st.session_state.current_section_no]):
        st.session_state.current_section_no += 1
        st.session_state.current_question_no = 0
        if st.session_state.current_section_no >= len(sections):
            st.write("All sections completed!")
            total = st.session_state.q1 + 2*st.session_state.q2 + 3*st.session_state.q3 + 4*st.session_state.q4 + 5*st.session_state.q5 + 6*st.session_state.q6
            final = st.session_state.count*100/total
            st.sidebar.write(f"Score: {final:.2f}")
            st.session_state.test_end = True
            return
    st.session_state.current_section = sections[st.session_state.current_section_no]
    st.session_state.readable = st.session_state.current_section_no == 0
    if st.session_state.current_section_no == 0:
        st.session_state.current_question = f"Question Number: {st.session_state.current_question_no + 1}/{len(st.session_state.quests[st.session_state.current_section_no])}: {st.session_state.quests[st.session_state.current_section_no][st.session_state.current_question_no]}"
    else:
        st.session_state.current_question = f"Question Number: {st.session_state.current_question_no + 1}/{len(st.session_state.quests[st.session_state.current_section_no])}"
    st.rerun()

async def evaluate(sec, ques, filename):
    form = ["Question is a sentence which should be read properly and completely in the audio file.",
            "Question is a sentence narated to candidate which should be repeated properly and completely in the audio file.",
            "Question is a jumbled sentence which should be arranged properly and completely in the audio file.",
            "Question is a simple query which should be answered properly and completely in the audio file. in one or two words.",
            "Question is a story which should be narrated properly and completely in the audio file.",
            "Question is an open question which should be answered properly and completely in the audio file."]
    inst = f"Question: {ques}. Evaluate the audio very strictly, answer should be accurately match according to question. Check for proper grammer, pronunciation. Provide result of being pass or fail along with valuable remark. Pass only if it is almost 95% correct. Reply in format : [Score: ____/100 & Remark: ........]"
    prompt = f"{form[st.session_state.current_section_no]} {inst}"
    audio_file = genai.upload_file(path=os.path.join(TEMP_DIR, filename))
    response = model.generate_content([audio_file, prompt])
    result = re.findall(r'\[(.*?)\]', response.text)[-1]
    match = re.search(r'Score:\s*(\d+)/100\s*&\s*Remark:\s*(.*)', result)
    if match:
        score = match.group(1)  # Capture the score
        remark = match.group(2)
    else:
        score = 0
        remark = "No remark provided."
    upd_remark = f"S{st.session_state.current_section_no}Q{st.session_state.current_question_no} : {remark}"
    st.session_state.evaluations.append(upd_remark)
    level = st.session_state.current_section_no + 1
    marks = int(score)*level/100
    st.session_state.count += marks
    audio_file.delete()
    return

if st.button("Start Test", disabled=st.session_state.test_started):
    st.write("Test started!")
    st.session_state.instructions = ""
    st.session_state.test_started = True
    st.rerun()

if st.session_state.test_started:
    st.write(st.session_state.current_section)
    st.write(st.session_state.current_question)

    if st.session_state.current_section_no != 0:
        if st.button("Listen to Question", disabled=st.session_state.readable): 
            speak(st.session_state.quests[st.session_state.current_section_no][st.session_state.current_question_no])

    if st.button("Record Answer"):
        audio_data = record_audio(duration[st.session_state.current_section_no])
        saved_filename = save_audio(audio_data)
        st.success(f"Audio recorded successfully! Saved as {saved_filename}")
        asyncio.run(evaluate(st.session_state.current_section, st.session_state.current_question, saved_filename))
        time.sleep(3)  # Wait before updating the question
        update()
