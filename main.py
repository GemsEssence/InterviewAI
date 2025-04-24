import os
import time
import tempfile
from gtts import gTTS
import playsound
import speech_recognition as sr
from openai import OpenAI
from dotenv import load_dotenv
import os


# Load API key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=openai_api_key)


# Global interview state
interview_context = {
    "messages": [],
    "transcript": [],
    "start_time": None,
    "duration_secs": 0,
    "tech": "",
    "exp": 0,
    "active": False
}


# Speak the interviewer’s question using gTTS
def speak(text):
    print("\nInterviewer:", text)
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as fp:
        tts.save(fp.name)
        playsound.playsound(fp.name)


# Listen to candidate’s voice answer and convert to text
def listen():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        print("\n🎤 Listening... Please speak your answer:")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        response = recognizer.recognize_google(audio)
        print("Candidate:", response)
        return response
    except sr.UnknownValueError:
        print("❌ Sorry, could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"❌ Speech recognition failed: {e}")
        return ""


# Starts the interview and asks first question
def start_interview(tech, exp, duration):
    interview_context.update({
        "messages": [
            {"role": "system", "content": f"You are a technical interviewer for a {tech} developer with {exp} years of experience."},
            {"role": "user", "content": "Hi, I'm ready for the interview."}
        ],
        "transcript": [],
        "start_time": time.time(),
        "duration_secs": duration * 60,
        "tech": tech,
        "exp": exp,
        "active": True
    })

    first_q = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=interview_context["messages"] + [
            {"role": "user", "content": f"Ask a technical question related to {tech} suitable for a candidate with {exp} years of experience."}
        ]
    ).choices[0].message.content

    interview_context["messages"].append({"role": "assistant", "content": first_q})
    interview_context["transcript"].append(f"Interviewer: {first_q}")
    speak(first_q)


# Handles follow-up and checks interview timing
def continue_interview(user_input):
    interview_context["messages"].append({"role": "user", "content": user_input})
    interview_context["transcript"].append(f"Candidate: {user_input}")

    if time.time() - interview_context["start_time"] >= interview_context["duration_secs"]:
        print("\nInterview ended. Here's your feedback:\n")
        print(get_feedback())
        interview_context["active"] = False
        return False

    follow_up = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=interview_context["messages"] + [
            {"role": "user", "content": f"Ask a follow-up technical question related to {interview_context['tech']} based on the last answer."}
        ]
    ).choices[0].message.content

    interview_context["messages"].append({"role": "assistant", "content": follow_up})
    interview_context["transcript"].append(f"Interviewer: {follow_up}")
    speak(follow_up)
    return True


# Gets final feedback
def get_feedback():
    feedback_prompt = "Give detailed and constructive feedback based on this interview:\n" + "\n".join(interview_context["transcript"])
    feedback = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior technical interviewer giving feedback to a candidate."},
            {"role": "user", "content": feedback_prompt}
        ]
    ).choices[0].message.content
    return feedback


# Main loop
def run_interview():
    print("🎙️ Welcome to the LLM-Powered Voice Interview\n")
    tech = input("Enter the technology (e.g., Python, React): ")
    exp = float(input("Enter your years of experience: "))
    duration = int(input("Enter interview duration in minutes: "))

    start_interview(tech, exp, duration)

    while interview_context["active"]:
        answer = listen()
        if answer.strip():
            if not continue_interview(answer):
                break
        else:
            print("❗Please repeat your answer.")


if __name__ == "__main__":
    run_interview()




