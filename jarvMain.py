from datetime import datetime
import speech_recognition as sr
import pyttsx3
import webbrowser
import wikipedia
import wolframalpha
import music as ms

# Speech engine initialization
engine = pyttsx3.init()
voices = engine.getProperty('voices')
voice_id = 'com.apple.speech.synthesis.voice.Daniel'
activation_word = 'jarvis' #should be a single word(?) ask why

#uses the id of the voices
engine.setProperty('voice', voice_id)

# # Use to see british voices
# for voice in voices:
#     print(voice, voice.id)

#Configure Browser
#Set The Path
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))


#WolframAlpha
web_id = "LLAXR6-Y3G4EKJX2J"
wolframClient = wolframalpha.Client(web_id)

def listOrDict(var):
    if isinstance(var, list):
        return var[0]['plaintext']
    return var['plaintext']


def speak(text, rate = 120): #rate is how fast voice talks
    engine.setProperty('rate', rate)
    engine.say(text)
    engine.runAndWait()

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
        speak("Computation Failed; Querying universal databank.")
        return search_wiki(question)
    


def parseCommand():
    listener = sr.Recognizer()
    print("Listening")

    with sr.Microphone() as src:
        listener.pause_threshold = 1.5 # seconds before stops listening
        base_speech = listener.listen(src) #recorded input
    
    try:
        print("Processing Speech")
        query = listener.recognize_google(base_speech, language="en_us") #processed input
        print(f"you said: {query}")
    except Exception as e:
        speak("Didn't quite catch that")
        print(e)
        return 'None'
    
    return query

#main func:
if __name__ == '__main__':
    speak("All Systems Up")

    while True:
        # Parse as list
        query = parseCommand().lower().split()

        if(query[0] == activation_word):
            query.pop(0)
            
            #List commands
            if query[0] == 'say':
                if 'hello' in query:
                    speak("Salutations, Dipshit")
                else:
                    query.pop(0)
                    speech = ' '.join(query)
                    speak(speech)
            if query[0] == 'off':
                speak("With Pleasure")
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
                    speak("Unable to Computer")

            #Note taking
            if ' '.join(query[:3]) == "create new log":
                speak("Ready to log")
                newNote = parseCommand().lower()
                curr_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

                with open('note_%s.txt' % curr_time, 'w') as newFile:
                    newFile.write(newNote)
                speak("Note has been written")
            
            #Music Player:
            if ' '.join(query[:3]) == "enter music mode":
                speak("Downloading DJ Skills... Entering DJ Environment...")
                


