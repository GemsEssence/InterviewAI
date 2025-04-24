import os
import time
import tempfile
from gtts import gTTS
from playsound import playsound
import speech_recognition as sr
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


session = {
    "messages": [],
    "transcript": [],
    "start_time": None,
    "duration_secs": 0,
    "tech": "",
    "exp": 0,
    "active": False
}


def speak(text):
    print("\n🧠 Interviewer:", text)
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as fp:
        tts.save(fp.name)
        playsound(fp.name)


def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as mic:
        print("\n🎤 Listening for your answer...")
        recognizer.adjust_for_ambient_noise(mic)
        audio = recognizer.listen(mic)
    try:
        response = recognizer.recognize_google(audio)
        print("🧑 Candidate:", response)
        return response
    except sr.UnknownValueError:
        print("❌ Didn't catch that.")
    except sr.RequestError as e:
        print(f"❌ Error: {e}")
    return ""


def ask_gpt(prompt):
    messages = session["messages"] + [{"role": "user", "content": prompt}]
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=messages
    )
    return response.choices[0].message.content


def start_interview(tech, exp, duration_min):
    session.update({
        "messages": [
            {"role": "system", "content": f"You are a technical interviewer for a {tech} developer with {exp} years of experience."},
            {"role": "user", "content": "Hi, I'm ready for the interview."}
        ],
        "transcript": [],
        "start_time": time.time(),
        "duration_secs": duration_min * 60,
        "tech": tech,
        "exp": exp,
        "active": True
    })
    question = ask_gpt(f"Ask a technical question related to {tech} for a candidate with {exp} years of experience.")
    session["messages"].append({"role": "assistant", "content": question})
    session["transcript"].append(f"Interviewer: {question}")
    speak(question)


def continue_interview(answer):
    session["messages"].append({"role": "user", "content": answer})
    session["transcript"].append(f"Candidate: {answer}")

    if time.time() - session["start_time"] >= session["duration_secs"]:
        print("\n📋 Interview Finished. Here's your feedback:\n")
        print(get_feedback())
        session["active"] = False
        return False

    question = ask_gpt(f"Ask a follow-up technical question about {session['tech']} based on the last answer.")
    session["messages"].append({"role": "assistant", "content": question})
    session["transcript"].append(f"Interviewer: {question}")
    speak(question)
    return True


def get_feedback():
    feedback_prompt = "Give detailed feedback based on this interview:\n" + "\n".join(session["transcript"])
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior technical interviewer giving feedback to a candidate."},
            {"role": "user", "content": feedback_prompt}
        ]
    )
    return response.choices[0].message.content


def run_interview():
    print("🎙️ Welcome to your AI-powered interview\n")
    tech = input("Technology (e.g., Python, React): ")
    exp = float(input("Years of experience: "))
    duration = int(input("Duration in minutes: "))

    start_interview(tech, exp, duration)

    while session["active"]:
        answer = listen()
        if answer.strip():
            if not continue_interview(answer):
                break
        else:
            print("🔁 Let's try that again...")


if __name__ == "__main__":
    run_interview()




