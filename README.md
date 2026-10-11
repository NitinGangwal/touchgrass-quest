# Touch Grass Quest

An AI-powered outdoor scavenger hunt built for the Hacktoberfest 2026 "Touch Grass" challenge.
You get 5 quests, go outside, photograph what you find, and an open-weight Gemma model checks
your photos and shares a fun fact. The screen is only needed at the start and the end.

## How it works
1. Pick a place (park, campus, garden...) and a difficulty. The AI generates 5 quests.
2. Go outside and take a photo for each quest with your phone.
3. Upload the photos. Gemma checks whether each one matches and adds a fun fact.
4. Get points and a short AI-written nature journal.

## Open-source AI
- Gemma 4 (open-weight) through the Gemini API
- Gemma 3 running fully on-device through Ollama (photos never leave your laptop)
Switch between them in the sidebar.

## Run it
1. Install Ollama (https://ollama.com) and run: ollama pull gemma3:4b
2. pip install -r requirements.txt
3. python -m streamlit run touchgrass.py
4. For Gemma 4, enter a free Gemini API key from https://aistudio.google.com/apikey

## Tech stack
Python, Streamlit, Gemma 4, Gemma 3, Ollama, Pillow

## License
MIT
