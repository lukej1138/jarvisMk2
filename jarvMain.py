from datetime import datetime
import speech_recognition as sr
import pyttsx3
import webbrowser
import wikipedia
import wolframalpha
import music as ms
import sounddevice as sd
import numpy as np
import time
from kokoro import KPipeline
from queue import Queue
import threading
import time
import calendarGoogle
import os 
pipeline = KPipeline(lang_code='a')


# Speech engine initialization
#engine = pyttsx3.init()
#voices = engine.getPropiperty('voices')
#voice_id = 'com.apple.speech.synthesis.voice.Daniel'
#engine.setProperty('voice', voice_id)

activation_word = 'jarvis' 


#Configure Browser
#Set The Path
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))


#WolframAlpha
web_id = "LLAXR6-Y3G4EKJX2J"
wolframClient = wolframalpha.Client(web_id)

stop_speaking = False
speech_thread = None

def listOrDict(var):
    if isinstance(var, list):
        return var[0]['plaintext']
    return var['plaintext']


def speak(text): 
    # engine.setProperty('rate', rate)
    # engine.say(text)
    # engine.runAndWait()
    global stop_speaking, speech_thread
    
    stop_speaking = True
    if speech_thread and speech_thread.is_alive():
        speech_thread.join() 
    stop_speaking = False


    def _threaded_speaking():
        generator = pipeline(text, voice='bm_lewis')
        try:
            for i, (gs, ps, audio) in enumerate(generator):
                if stop_speaking:
                    sd.stop()
                    break
                sd.play(audio, samplerate=24050)
                sd.wait()
        except Exception as e:
            if "PortAudio" not in str(e):  # Only show non-audio errors
                print(f"Error: {e}")
        finally:
            sd.stop()


    speech_thread = threading.Thread(target=_threaded_speaking)
    speech_thread.daemon = True
    speech_thread.start()




def search_wiki(query = ''):
    searchResults = wikipedia.search(query)
    if not searchResults:
        print("No wikipedia results")
        return "No Results Detected"
    try:
        wikiPage = wikipedia.page(searchResults[0])
    except wikipedia.DisambiguationError as e:
        wikiPage = wikipedia.page(e.options[0])
    print(wikiPage.title)
    wikiSummary = str(wikiPage.summary)
    return wikiSummary

def search_wolframalpha(query=''):
    response = wolframClient.query(query)
    #@success: wolfram could resolve query
    #@numpods: number of results returned
    #pod: List of results. can contain subpods.
    if response['@success'] == 'false':
        return 'Could not compute'
    
    #query resolved
    result = ''
    
    #question
    pod0 = response['pod'][0]

    pod1 = response['pod'][1]
    # May contain the answer, highest confidence
    #If has title of result or definition or is primary, then its official result
    if(('result') in pod1['@title'].lower() or (pod1.get('@primary', 'false') == 'true') or ('definition' in pod1['@title'].lower())):
        #Get the result:
        result = listOrDict(pod1['subpod'])
        # remove the bracketed
        return result.split('(')[0]
    else:
        question = listOrDict(pod0['subpod'])
        #try out wikipedia
        speak("Computation Failed; trying wikipedia.")
        return search_wiki(question)
    
def get_listening_result():
    listener = sr.Recognizer()
    listener.energy_threshold = 4000 
    listener.dynamic_energy_threshold = True
    print("Listening")

    with sr.Microphone() as src:
        timeout = 1 # seconds before stops listening
        listener.adjust_for_ambient_noise(src)
        try:
            base_speech = listener.listen(src) #recorded input
            query = listener.recognize_google(base_speech, language="en_us").lower() #processed input
            print(f"Heard: {query}")
            return query
        except Exception as e:
            print(e)
            return 'None'
    return query

def parseCommand():
    global stop_speaking
    command = get_listening_result()
    if not command:
        return None
    
    if ("stop" in command or "shut up" in command) and stop_speaking == False:
        stop_speaking = True
        sd.stop()
        time.sleep(0.5)
        return "interrupt"
    
    if activation_word in command:
        return command



#main func:
if __name__ == '__main__':
    speak("Hello!")
    time.sleep(2)

    is_speaking = False
    while True:
        # Parse as list
        query = parseCommand()
        if not query:
            continue

        query = query.lower().split()
        if query == "interrupt":
            is_speaking = False
            continue

        if(activation_word == query[0] and len(query) > 1):
            query.pop(0)
            is_speaking = True
            
            #List commands
            if query[0] == 'say':
                if 'hello' in query:
                    speak("Salutations")
                else:
                    query.pop(0)
                    speech = ' '.join(query)
                    speak(speech)
            if query[0] == 'off':
                speak("With Pleasure")
                time.sleep(2)
                break

            #Navigation:
            if query[0] == 'go' and query[1] == 'to':
                speak('Opening...')
                query = ' '.join(query[2:])
                if '.' not in query:
                    query = query + ".com"
                webbrowser.get('chrome').open_new(query)

            #Wikipedia
            if query[0] == 'look' and query[1] == 'up':
                query.pop(0)
                query = ' '.join(query)
                speak("Loading Data... Processing...")
                speak(search_wiki(query))

            #WolframAlpha
            if query[0] == 'compute' or query[0] == 'calculate':
                query = ' '.join(query[1:])
                speak("computing")
                try:
                    result = search_wolframalpha(query)
                    speak(result)
                except:
                    speak("Unable to Compute")

            #Note taking
            if ' '.join(query[:3]) == "create new log":
                speak("Ready to log")
                newNote = parseCommand().lower()
                curr_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

                with open('note_%s.txt' % curr_time, 'w') as newFile:
                    newFile.write(newNote)
                speak("Note has been written")
            
            #Music Player:
            if "play" in query[:3]:
                if "by" in query:
                    speak(f"Playing {" ".join(query[query.index("play")+1:query.index("by")])} by {" ".join(query[query.index("by")+1:])}")
                    if not ms.search_and_play_spotify(" ".join(query[query.index("play")+1:query.index("by")]), " ".join(query[query.index("by")+1:])):
                        speak("Sorry, I couldn't find that song. Could you try repeating your command?")
                else:
                    speak(f"Playing {" ".join(query[query.index("play")+1:])}")
                    if not ms.search_and_play_spotify(" ".join(query[query.index("play")+1:])):
                        speak("Sorry, I couldn't find that song. Could you try repeating your command?")
            
            if "resume" in query:
                result = ms.resume()
                if not result:
                    speak("Music is already playing, sir")
                else:
                    speak("Playback started")
            
            if ("pause" in query or "off" in query) and "music" in query:
                result = ms.pause()
                if not result:
                    speak("Music is already off, sir")
                


            #Scheduler
            if "schedule" in query or "calendar" in query:
                if query[0] == "remove":
                    calendarGoogle.remove(query[1:query.index("from")])
                elif query[0] == "add":
                    start, end, date, name = calendarGoogle.parseEvent(" ".join(query[1:]))
                    if start == "No Break":
                        speak("Please use the work 'break' when adding to the calendar")
                    elif not start or not end or not date or not name:
                        speak("Could not add to calendar; please try again")
                    else: 
                        speak(f"Adding {name} to your schedule, sir")
                        calendarGoogle.add(start, end, date, name)
            is_speaking = False
    os._exit(0)
                


                


