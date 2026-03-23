import speech_recognition as sr
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, AutoModelForCausalLM
from huggingface_hub import login
import win32com.client
import torch
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA, LLMChain
import os

print("Importing done")

# Log in to Hugging Face using your API key
huggingface_api_key = "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"
login(huggingface_api_key)

print("Login done")

# Load the DistilBERT QA model and tokenizer
model_name = "distilbert-base-uncased-distilled-squad"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForQuestionAnswering.from_pretrained(model_name)

print("QA model loaded")

# Initialize the Windows SAPI voice engine
speaker = win32com.client.Dispatch("SAPI.SpVoice")

print("Voice engine initialized")

# Load PDF document
pdf_path = "C:\\Users\\Garima Kohli\\Desktop\\content.pdf"  # Update path
loader = PyPDFLoader(pdf_path)
document = loader.load()

if not document:
    print("Error: PDF content is empty. Check the file path or file format.")
    exit()

print("PDF loaded successfully")

# Concatenate all document text into a single string
context = " ".join(doc.page_content for doc in document)
print("PDF loaded and concatenated successfully")

# Split the document into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = text_splitter.split_documents(document)

print("Document chunked successfully")

# Create embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

print("Embeddings created")

print("loading...")

# Create a vector store
vectorstore = Chroma.from_documents(chunks, embeddings)
print("Vector store created")

def speak(text):
    """Convert text to speech using win32com.client."""
    speaker.Speak(text)

def get_voice_input():
    """Capture voice input and convert to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=10)
            query = recognizer.recognize_google(audio, language="en-IN")
            print(f"User said: {query}")
            return query
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand that.")
            speak("Sorry, I couldn't understand that.")
            return None
        except sr.RequestError:
            print("Request failed. Please check your internet connection.")
            speak("Request failed. Please check your internet connection.")
            return None

def find_relevant_chunk(query):
    """Retrieve the most relevant document chunk from the vectorstore."""
    results = vectorstore.similarity_search(query, k=1)
    if results:
        return results[0].page_content
    return ""

def answer_question(question, context):
    """Use the DistilBERT model for QA tasks."""
    # Retrieve the most relevant chunk
    relevant_chunk = find_relevant_chunk(question)
    if not relevant_chunk:
        return "Sorry, I couldn't find relevant information."
    
    """Use the DistilBERT model for QA tasks."""
    inputs = tokenizer(question, relevant_chunk, return_tensors='pt', truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    
    start_position = outputs.start_logits.argmax()
    end_position = outputs.end_logits.argmax()
    
    answer = tokenizer.decode(inputs.input_ids[0][start_position:end_position + 1], skip_special_tokens=True)
    return answer

def main():
    print("Welcome to the Voice Query Assistant!")
    speak("Welcome to the Voice Query Assistant!")

    while True:
        print("Press 'yes' to ask a question or type 'exit' to quit.")
        speak("Press 'yes' to ask a question or type 'exit' to quit.")
        command = input().strip()
        if command.lower() == "exit":
            break

        if command.lower() == "yes":
            query = get_voice_input()
            if query:
                answer = answer_question(query, context)
                print(f"AI Response: {answer}")
                speak(answer)
            else:
                print("No valid input received. Please try again.")
                speak("No valid input received. Please try again.")
        else:
            print("Invalid command. Please type 'yes' or 'exit'.")
            speak("Invalid command. Please type 'yes' or 'exit'.")

    print("Thank you for comming")
    speak("Thank you for comming")

if __name__ == '__main__':
    main()
