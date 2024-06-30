import os
import sys
import openai
import json
import re
from time import time, sleep
from urllib.parse import urlparse, parse_qs
import textwrap
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import streamlit as st

openai.api_key = 'sk-proj-CpNemz0YDojvoNiBVMkAT3BlbkFJTwGgK0sv1UmubB4wRqw8'

def get_transcript(url):
    try:
        url_data = urlparse(url)
        video_id = parse_qs(url_data.query)["v"][0]
    except Exception as e:
        print("ERROR ! INVALID LINK !?!", e)
        return (-1,-1)
    if not video_id:
        print('Video ID not found.')
        return (-1,-1)
    try:
        formatter = TextFormatter()
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        text = formatter.format_transcript(transcript)
        text = re.sub(r'\s+', ' ', text).replace('--', '')
        return video_id, text
    except Exception as e:
        print('Error downloading transcript',e)
        return (-1,-1)
      
def gpt3_completion(prompt, tokens):
    max_retry = 4
    retry = 0
    while True:
        try:
            response = openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=tokens,
                top_p=1.0,
                frequency_penalty=0.25,
                presence_penalty=0.0)
            text = response.choices[0].message.content.strip()
            text = re.sub(r'\s+', ' ', str(text))
            if not text:
                retry += 1
                continue
            return text

        except Exception as e:
            retry += 1
            if retry >= max_retry:
                return "Base model error: %s" % e
            print('Connection Error w/ OpenAI:', e)
            sleep(0.8)
            pass

def ask_gpt(text, job='SUMMARY'):
    chunks = textwrap.wrap(text, width=10000)
    results = list()
  
    for i, chunk in enumerate(chunks):
        output = ""
        if job=='SUMMARY':
            prompt = f"Write a concise summary of the following: {chunk} CONCISE SUMMARY:"
            prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
            output = gpt3_completion(prompt, tokens=100)
          
        elif job == 'REWRITE':
            prompt = f"Following paragraphs are chunk of summaries. Combine and rewrite them in an elaborated fashion: {chunk} CONTENT:"
            prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
            output = gpt3_completion(prompt, tokens=100)
          
        results.append(output)
        print(f'{i+1} of {len(chunks)}\n{output}\n\n\n')
    return results
    
count = 0
def main():
    summary = ""
    global count
    st.title("YouTube Video Summarizer")
    st.write("Welcome. Please enter a YouTube Video Link and Enter to obtain its Summary")

    count += 1
    user_input = st.text_input("You:", key=f"user_input_{count}")
    if user_input.lower() in ['goodbye', 'bye']:
        st.write("Thank you for using my application. Have a great day!")
        st.stop()
    if user_input:
        video_id, text = get_transcript(user_input)
        if video_id == -1 and text == -1:
            print("ERROR ARGS!!")
            sys.exit()
        if text:
            results = ask_gpt(text,'SUMMARY')
            summary = '\n\n'.join(results)
            if len(results) > 1:
                summary = ask_gpt(summary, 'REWRITE')
                summary = '\n\n'.join(summary)
        st.text_area("YouTube Summarizer", value=summary, height=101, max_chars=None, key=f"chatbot_response_{count}")

if __name__ == '__main__':
    main()
