from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)

from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech

from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os

import webbrowser
from AppOpener import open as appopen

env_vars = dotenv_values(".env")

Username = env_vars.get("Username") or "User"
Assistantname = env_vars.get("Assistantname") or "Jarvis"

DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well. How may I help you?'''

subprocesses = []

Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]


def ShowDefaultChatIfNoChats():
    File = open(r'Data\ChatLog.json', "r", encoding='utf-8')

    if len(File.read()) < 5:
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write("")

        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessage)


def ReadChatLogJson():
    with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
        return json.load(file)


def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""

    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"

    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))


def ShowChatsOnGUI():
    File = open(TempDirectoryPath('Database.data'), "r", encoding='utf-8')
    Data = File.read()

    if len(str(Data)) > 0:
        with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
            file.write(Data)


def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()


InitialExecution()


def MainExecution():

    SetAssistantStatus("Listening...")
    Query = SpeechRecognition()
    ShowTextToScreen(f"{Username} : {Query}")

    q = Query.lower().strip()

    # ================= 🔥 DIRECT COMMAND FIX =================
    if "play" in q:
        run(Automation([f"play {q.replace('play', '').strip()}"]))
        return

    elif "open" in q:
        run(Automation([f"open {q.replace('open', '').strip()}"]))
        return

    elif "close" in q:
        run(Automation([f"close {q.replace('close', '').strip()}"]))
        return
    # ========================================================

    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)

    print("\nDecision :", Decision, "\n")

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    Merged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    # 🔥 AUTOMATION (fallback if model returns command)
    for cmd in Decision:
        if cmd.startswith(tuple(Functions)):
            run(Automation([cmd]))
            return

    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))

        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return

    else:
        for Queries in Decision:

            if "general" in Queries:
                QueryFinal = Queries.replace("general ", "")
                Answer = ChatBot(QueryModifier(QueryFinal))

            elif "realtime" in Queries:
                QueryFinal = Queries.replace("realtime ", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))

            elif "exit" in Queries:
                Answer = "Okay, Bye!"
                os._exit(1)

            else:
                continue

            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return


def FirstThread():
    while True:
        if GetMicrophoneStatus() == "True":
            MainExecution()
        else:
            if "Available..." not in GetAssistantStatus():
                SetAssistantStatus("Available...")
            sleep(0.1)


def SecondThread():
    GraphicalUserInterface()


if __name__ == "__main__":
    thread = threading.Thread(target=FirstThread, daemon=True)
    thread.start()
    SecondThread()