import os
import time
import streamlit as st
from datetime import date
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import google.api_core.exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- API Keys (read from environment variables for safety) ---
GOOGLE_API_KEY = "AIzaSyDv3zVBjzVttDt1lx36M5KO9oopKhG6SDg"
OPENAI_API_KEY = "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"

if not GOOGLE_API_KEY and not OPENAI_API_KEY:
    st.error("❌ No API keys found. Set GOOGLE_API_KEY or OPENAI_API_KEY as environment variables.")
    st.stop()

# --- Streamlit Configuration ---
st.set_page_config(page_title="AI-Powered Travel Planner", layout="wide")
st.markdown("<h1 style='text-align: center; color: #2a4a7d;'>AI-Powered Travel Planner</h1>", unsafe_allow_html=True)

# --- User Inputs ---
with st.expander("✈️ Enter Trip Details", expanded=True):
    col1, col2, col3 = st.columns(3)
    source = col1.text_input("From:", placeholder="Enter departure city")
    destination = col2.text_input("To:", placeholder="Enter destination city")
    trip_duration = col3.slider("Trip Duration (days):", 1, 30, 3)

    col4, col5, col6 = st.columns(3)  # Added column for budget
    date_of_travel = col4.date_input("Travel Date:", min_value=date.today())
    travel_mode = col5.selectbox("Preferred Mode:", ["Any", "Flight", "Train", "Bus", "Cab"])
    budget = col6.number_input("Budget ($):", min_value=0, value=1000, step=100)

    add_prefs = st.checkbox("Add Advanced Preferences")
    interests = "general"
    dietary_prefs = "none"
    if add_prefs:
        col7, col8 = st.columns(2)
        interests = col7.multiselect("Interests:", ["Historical", "Adventure", "Cultural", "Nature", "Food"])
        dietary_prefs = col8.selectbox("Dietary Preferences:", ["None", "Vegetarian", "Vegan", "Gluten-Free"])
    
    # Added notes field
    notes = st.text_area("Additional Notes:", placeholder="Any special requests or preferences?")

# --- Throttle Requests ---
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0

# --- Prompt Template ---
chat_template = ChatPromptTemplate.from_messages([
    ("system", "You are an expert travel planner. Provide a detailed itinerary with transport, accommodation (suggest home stays), and food suggestions in a tabulated format for easy understanding this is important. Make it eco-friendly and specify how it's eco-friendly. Consider the budget and notes provided."),
    ("human", "Plan a {duration}-day trip from {source} to {destination} on {date} with a ${budget} budget. Mode: {mode}. Interests: {interests}. Diet: {diet}. Notes: {notes}")
])

# --- Retry Decorator for Gemini ---
def is_resource_exhausted(e):
    return isinstance(e, google.api_core.exceptions.ResourceExhausted)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception_type(google.api_core.exceptions.ResourceExhausted)
)
def gemini_generate(chain, inputs):
    return chain.invoke(inputs)

# --- Button Click Logic ---
if st.button("Generate Travel Plan", use_container_width=True):
    now = time.time()
    if now - st.session_state.last_request_time < 30:
        st.warning("⏳ Please wait a bit before requesting again.")
    elif not source or not destination:
        st.warning("⚠️ Please fill in all required fields.")
    else:
        st.session_state.last_request_time = now

        with st.spinner("🧠 Generating your perfect itinerary..."):
            try:
                inputs = {
                    "source": source,
                    "destination": destination,
                    "date": date_of_travel.strftime('%d %b %Y'),
                    "duration": trip_duration,
                    "mode": travel_mode,
                    "budget": budget,
                    "interests": ", ".join(interests) if isinstance(interests, list) else interests,
                    "diet": dietary_prefs,
                    "notes": notes
                }

                response = None

                # --- Try Gemini ---
                if GOOGLE_API_KEY:
                    try:
                        gemini_llm = ChatGoogleGenerativeAI(api_key=GOOGLE_API_KEY, model="gemini-2.0-flash")
                        chain = chat_template | gemini_llm | StrOutputParser()
                        response = gemini_generate(chain, inputs)
                    except google.api_core.exceptions.ResourceExhausted as e:
                        st.warning("⚠️ Gemini quota exceeded or rate-limited. Falling back to OpenAI...")
                        response = None
                    except Exception as e:
                        st.warning(f"⚠️ Gemini error: {str(e)}. Trying OpenAI...")
                        response = None

                # --- Fallback: OpenAI ---
                if not response and OPENAI_API_KEY:
                    try:
                        openai_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")
                        chain = chat_template | openai_llm | StrOutputParser()
                        response = chain.invoke(inputs)
                    except Exception as e:
                        st.error(f"❌ OpenAI error: {str(e)}")
                        response = None

                # --- Show Result or Error ---
                if response:
                    st.subheader(f"🗺️ Your {trip_duration}-Day {destination} Itinerary")
                    st.markdown(response, unsafe_allow_html=True)

                    itinerary_markdown = f"""
# 🌍 Travel Itinerary for {destination}
### ✈️ Trip Details:
- **From:** {source}
- **To:** {destination}
- **Date:** {date_of_travel.strftime('%d %b %Y')}
- **Duration:** {trip_duration} days
- **Budget:** ${budget}
- **Preferred Mode:** {travel_mode}
- **Interests:** {', '.join(interests) if add_prefs else 'General'}
- **Dietary Preferences:** {dietary_prefs if add_prefs else 'None'}
- **Additional Notes:** {notes if notes else 'None'}

## 📌 Itinerary Plan:
{response}
"""
                    st.download_button("📥 Download Itinerary", data=itinerary_markdown.encode('utf-8'),
                                       file_name=f"{destination}_itinerary.md", mime="text/markdown")
                else:
                    st.error("❌ No response received from either provider. Please try again later or check your API quotas.")

            except Exception as e:
                st.error(f"⚠️ An unexpected error occurred: {str(e)}")

# --- Footer ---
st.markdown("<hr><center><small>Powered by Gemini & OpenAI | Built with ❤️ using Streamlit</small></center>", unsafe_allow_html=True)
