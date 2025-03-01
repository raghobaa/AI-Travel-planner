
import streamlit as st
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from datetime import date
import os
API_KEY = os.getenv("API_KEY") 




# Streamlit UI 
st.set_page_config(page_title="AI-Powered Travel Planner", page_icon="\U0001F30D", layout="centered")

image_url = "https://raw.githubusercontent.com/Abhiram4u/AI-Travel-planner/main/travel%200.png"
st.image(image_url, use_container_width=True) # homepage image



st.markdown("<h1 style='text-align: center;'>AI-Powered Travel Planner</h1>", unsafe_allow_html=True)
st.write("Plan your trip effortlessly with AI-generated travel options and estimated costs!")

# User input fields
col1, col2 = st.columns(2)
with col1:
    source = st.text_input("Enter Source City:")
with col2:
    destination = st.text_input("Enter Destination City:")

date_of_travel = st.date_input("Select Travel Date:", min_value=date.today())
price_range = st.slider("Select Price Range (₹):", min_value=500, max_value=50000, value=(1000, 20000), step=500)
travel_mode = st.selectbox("Preferred Travel Mode:", ["Any", "Flight", "Train", "Bus", "Cab"])

if st.button("Find Best Travel Options"):
    if source and destination:
        with st.spinner("Fetching best travel options..."):
            # LangChain components
            chat_template = ChatPromptTemplate(messages=[
                ("system", """
                You are an AI-powered travel assistant that provides users with the best travel options based on their preferences.
                Given a source, destination, travel date, price range, and preferred mode, generate a structured travel plan.
                Include multiple options like cab, train, bus, and flights with estimated costs, travel time, and details like stops or transfers.
                Also, provide a sample itinerary with recommended travel schedules and estimated duration.
                Prioritize accuracy, cost-effectiveness, and user preferences while presenting the results in a clear, easy-to-read format.
                """),
                ("human", "Find travel options from {source} to {destination} on {date_of_travel} with estimated costs in the range of ₹{price_min} to ₹{price_max}, considering {travel_mode} as a preferred mode. Also, suggest a travel itinerary.")
            ])
            
            chat_model = ChatGoogleGenerativeAI(api_key=API_KEY, model="gemini-2.0-flash-exp")
            parser = StrOutputParser()
            
            chain = chat_template | chat_model | parser
            
            raw_input = {
                "source": source, 
                "destination": destination,
                "date_of_travel": date_of_travel.strftime('%Y-%m-%d'),
                "price_min": price_range[0],
                "price_max": price_range[1],
                "travel_mode": travel_mode
            }
            response = chain.invoke(raw_input)
            
            # Display structured response
            st.success("✨ Best Travel Options and Estimated Costs:")
            #travel_modes = response.split("\n")
            #for mode in travel_modes:
                #st.write("- ", mode)
            
            # Sample Itinerary Section
            st.subheader("📅 Suggested Travel Details:")
            st.write("Here is a recommended itinerary based on your travel preferences:")
            st.write(response)  
            
         
    else:
        st.error("Please enter both source and destination cities.")
