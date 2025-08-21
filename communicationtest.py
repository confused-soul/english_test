import google.generativeai as genai
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import tempfile
import os
import pyttsx3
import re
import random
import time
from datetime import datetime
from questions import reading, repeating, jumbled, qna, stories, hr
import asyncio
import threading

# Access your API key as an environment variable
api_key = st.secrets["api_key"]
genai.configure(api_key=api_key)

# Choose a model that's appropriate for your use case
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize session states
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

# Sidebar configuration
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

# App layout
st.title("🎙️ Communication Test")

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

# Initialize questions
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

# Initialize test states
if "test_end" not in st.session_state:
    st.session_state.test_end = False

if "test_started" not in st.session_state:
    st.session_state.test_started = False
    st.session_state.readable = True
    st.session_state.current_section_no = 0
    st.session_state.current_question_no = 0
    st.session_state.current_section = sections[st.session_state.current_section_no]
    st.session_state.current_question = f"Question Number: {st.session_state.current_question_no + 1}/{len(st.session_state.quests[st.session_state.current_section_no])}: {st.session_state.quests[st.session_state.current_section_no][st.session_state.current_question_no]}"

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []

if "is_speaking" not in st.session_state:
    st.session_state.is_speaking = False

if "audio_played" not in st.session_state:
    st.session_state.audio_played = False

# Update questions button
if st.sidebar.button("🔄 Update Questions"):
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
    # Reset test state
    for key in ['count', 'evaluations', 'test_end', 'test_started', 'current_section_no', 
                'current_question_no', 'is_speaking', 'audio_played']:
        if key in st.session_state:
            if key == 'evaluations':
                st.session_state[key] = []
            elif key in ['count', 'current_section_no', 'current_question_no']:
                st.session_state[key] = 0
            else:
                st.session_state[key] = False
    
    st.session_state.readable = True
    st.session_state.current_section = sections[0]
    st.session_state.current_question = f"Question Number: 1/{len(st.session_state.quests[0])}: {st.session_state.quests[0][0]}"
    st.rerun()

# Sidebar for showing evaluations
st.sidebar.write("📊 **Evaluation Results:**")
st.sidebar.write("---")
if st.session_state.evaluations:
    for i, eval in enumerate(st.session_state.evaluations, 1):
        st.sidebar.write(f"{i}. {eval}")
else:
    st.sidebar.write("*No evaluations yet*")

# TTS function using threading to avoid blocking
def speak_text(text):
    def tts_thread():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 120)
            engine.setProperty('volume', 0.9)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            st.error(f"TTS Error: {str(e)}")
        finally:
            st.session_state.is_speaking = False
            st.session_state.audio_played = True
    
    if not st.session_state.is_speaking:
        st.session_state.is_speaking = True
        st.session_state.audio_played = False
        thread = threading.Thread(target=tts_thread)
        thread.daemon = True
        thread.start()

def update_question():
    st.session_state.current_question_no += 1
    if st.session_state.current_question_no >= len(st.session_state.quests[st.session_state.current_section_no]):
        st.session_state.current_section_no += 1
        st.session_state.current_question_no = 0
        if st.session_state.current_section_no >= len(sections):
            # Test completed
            total = (st.session_state.q1 + 2*st.session_state.q2 + 3*st.session_state.q3 + 
                    4*st.session_state.q4 + 5*st.session_state.q5 + 6*st.session_state.q6)
            final_score = st.session_state.count * 100 / total
            st.session_state.test_end = True
            st.success(f"🎉 Test Completed! Final Score: {final_score:.2f}%")
            return
    
    st.session_state.current_section = sections[st.session_state.current_section_no]
    st.session_state.readable = st.session_state.current_section_no == 0
    st.session_state.audio_played = False
    
    if st.session_state.current_section_no == 0:
        st.session_state.current_question = f"Question Number: {st.session_state.current_question_no + 1}/{len(st.session_state.quests[st.session_state.current_section_no])}: {st.session_state.quests[st.session_state.current_section_no][st.session_state.current_question_no]}"
    else:
        st.session_state.current_question = f"Question Number: {st.session_state.current_question_no + 1}/{len(st.session_state.quests[st.session_state.current_section_no])}"
    
    st.rerun()

async def evaluate_audio(sec, ques, audio_bytes):
    form = [
        "Question is a sentence which should be read properly and completely in the audio file.",
        "Question is a sentence narrated to candidate which should be repeated properly and completely in the audio file.",
        "Question is a jumbled sentence which should be arranged properly and completely in the audio file.",
        "Question is a simple query which should be answered properly and completely in the audio file in one or two words.",
        "Question is a story which should be narrated properly and completely in the audio file.",
        "Question is an open question which should be answered properly and completely in the audio file."
    ]
    
    inst = f"Question: {ques}. Evaluate the audio very strictly, answer should accurately match according to question. Check for proper grammar, pronunciation. Provide result of being pass or fail along with valuable remark. Pass only if it is almost 95% correct. Reply in format: [Score: ____/100 & Remark: ........]"
    prompt = f"{form[st.session_state.current_section_no]} {inst}"
    
    try:
        # Save audio bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        # Upload to Gemini
        audio_file = genai.upload_file(path=tmp_file_path)
        response = model.generate_content([audio_file, prompt])
        
        # Parse response
        result = re.findall(r'\[(.*?)\]', response.text)
        if result:
            result_text = result[-1]
            match = re.search(r'Score:\s*(\d+)/100\s*&\s*Remark:\s*(.*)', result_text)
            if match:
                score = int(match.group(1))
                remark = match.group(2)
            else:
                score = 0
                remark = "Could not parse evaluation result."
        else:
            score = 0
            remark = "No evaluation result found."
        
        # Update session state
        upd_remark = f"S{st.session_state.current_section_no + 1}Q{st.session_state.current_question_no + 1}: {remark}"
        st.session_state.evaluations.append(upd_remark)
        
        level = st.session_state.current_section_no + 1
        marks = score * level / 100
        st.session_state.count += marks
        
        # Cleanup
        audio_file.delete()
        os.unlink(tmp_file_path)
        
        return score, remark
        
    except Exception as e:
        st.error(f"Evaluation error: {str(e)}")
        return 0, f"Evaluation failed: {str(e)}"

# Main test interface
if not st.session_state.test_started:
    if st.button("🚀 Start Test", type="primary", use_container_width=True):
        st.session_state.instructions = ""
        st.session_state.test_started = True
        st.rerun()

if st.session_state.test_started and not st.session_state.test_end:
    st.write(f"### {st.session_state.current_section}")
    st.write(f"**{st.session_state.current_question}**")
    
    # Show duration for current section
    current_duration = duration[st.session_state.current_section_no]
    st.info(f"⏱️ Answer Duration: {current_duration} seconds")
    
    # Listen to question button (for sections other than reading)
    if st.session_state.current_section_no != 0:
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔊 Listen to Question", 
                        disabled=st.session_state.is_speaking,
                        use_container_width=True):
                speak_text(st.session_state.quests[st.session_state.current_section_no][st.session_state.current_question_no])
        
        with col2:
            if st.session_state.is_speaking:
                st.warning("🎵 Playing audio...")
            elif st.session_state.audio_played:
                st.success("✅ Audio played")
    
    st.write("---")
    
    # Audio recording using audio_recorder_streamlit
    st.write("🎙️ **Record your answer:**")
    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=2.0,
        sample_rate=16000
    )
    
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Submit Answer", type="primary", use_container_width=True):
                with st.spinner("🔍 Evaluating your answer..."):
                    try:
                        # Run evaluation
                        score, remark = asyncio.run(evaluate_audio(
                            st.session_state.current_section_no,
                            st.session_state.quests[st.session_state.current_section_no][st.session_state.current_question_no],
                            audio_bytes
                        ))
                        st.success(f"Score: {score}/100 - {remark}")
                        time.sleep(2)
                        update_question()
                    except Exception as e:
                        st.error(f"Error during evaluation: {str(e)}")
        
        with col2:
            if st.button("🔄 Re-record", use_container_width=True):
                st.rerun()

elif st.session_state.test_end:
    st.balloons()
    st.success("🎉 Congratulations! You have completed the Communication Test.")
    
    # Calculate and display final score
    total = (st.session_state.q1 + 2*st.session_state.q2 + 3*st.session_state.q3 + 
             4*st.session_state.q4 + 5*st.session_state.q5 + 6*st.session_state.q6)
    final_score = st.session_state.count * 100 / total
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric("Final Score", f"{final_score:.2f}%", delta=None)
    
    # Performance breakdown
    st.write("### 📈 Performance Breakdown")
    section_names = ["Reading", "Repeating", "Jumbled", "Q&A", "Storytelling", "Open Questions"]
    weights = [1, 2, 3, 4, 5, 6]
    question_counts = [st.session_state.q1, st.session_state.q2, st.session_state.q3, 
                      st.session_state.q4, st.session_state.q5, st.session_state.q6]
    
    for i, (section, weight, count) in enumerate(zip(section_names, weights, question_counts)):
        max_score = weight * count
        st.write(f"**{section}**: Weight {weight}x, Questions {count}, Max Score {max_score}")
    
    if st.button("🔄 Restart Test", use_container_width=True):
        # Reset all session states
        keys_to_reset = ['count', 'evaluations', 'test_end', 'test_started', 
                        'current_section_no', 'current_question_no', 'is_speaking', 'audio_played']
        for key in keys_to_reset:
            if key in st.session_state:
                if key == 'evaluations':
                    st.session_state[key] = []
                elif key in ['count', 'current_section_no', 'current_question_no']:
                    st.session_state[key] = 0
                else:
                    st.session_state[key] = False
        
        st.session_state.readable = True
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
        st.rerun()
