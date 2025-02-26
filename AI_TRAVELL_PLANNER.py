
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

# Streamlit UI 
st.title("AI-Powered Travel Planner")
st.write("Enter your travel details to get estimated travel costs for various travel modes including cab, train, bus, and flights.")

# User input fields
source = st.text_input("Source:")
destination = st.text_input("Destination:")


if st.button("Get Travel Cost Estimate"):
    if source and destination:
        with st.spinner("Fetching travel options..."):
            # LangChain components
            chat_template = ChatPromptTemplate(messages=[
                ("system", """
                You are an AI-powered travel assistant that provides users with the best travel options based on their preferences.
                Given a source and destination, you must generate a structured travel plan with multiple options, including cab, train, bus, and flights.
                Each option should include the estimated cost, travel time, and any relevant details like stops or transfers.
                Prioritize accuracy, cost-effectiveness, and convenience while presenting the results in a clear, easy-to-read format.
                """),
                ("human", "Find travel options from {source} to {destination} with estimated costs.")
            ])
            
            chat_model = ChatGoogleGenerativeAI(api_key="AIzaSyCHGvCV_UsrQLx8EZrb58IQ9qqQEyRNcYI", model="gemini-2.0-flash-exp")
            parser = StrOutputParser()
            
            
            chain = chat_template | chat_model | parser
            
            
            raw_input = {"source": source, "destination": destination}
            response = chain.invoke(raw_input)
            
            #structured response
            st.success("Estimated Travel Options and Costs:")
            travel_modes = response.split("\n")  
            for mode in travel_modes:
                st.write(mode)
    else:
        st.error("Please enter both source and destination.")
