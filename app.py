import streamlit as st
from google import genai
from google.cloud import bigquery
import numpy as np
import json

# Setup
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
PROJECT_ID = "project-72181980-533d-4978-aa7"

client = genai.Client(api_key=GEMINI_API_KEY)
client_bq = bigquery.Client(project=PROJECT_ID)

# Page config
st.set_page_config(
    page_title="Chicago Crime Intelligence Assistant",
    page_icon="🚔",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff4b4b, #ff8c00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    
    .hero-sub {
        font-size: 1.1rem;
        color: #888;
        margin-bottom: 2rem;
    }
    
    .answer-box {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-left: 4px solid #ff4b4b;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin: 1rem 0;
        font-size: 1.1rem;
        color: #ffffff;
        line-height: 1.7;
    }
    
    .stat-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        border: 1px solid #333;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        color: #ff4b4b;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #888;
        margin-top: 0.3rem;
    }

    .record-badge {
        display: inline-block;
        background: #ff4b4b22;
        color: #ff4b4b;
        border: 1px solid #ff4b4b44;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 0.8rem;
        margin: 2px;
    }
    
    .stTextInput > div > div > input {
        background-color: #1e1e2e;
        color: white;
        border: 1px solid #333;
        border-radius: 10px;
        font-size: 1rem;
        padding: 0.8rem;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #ff4b4b, #ff8c00);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
    }
    
    .sidebar-info {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #333;
        font-size: 0.85rem;
        color: #aaa;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🚔 About This App")
    st.markdown("""
    <div class="sidebar-info">
    This app uses a <b>RAG (Retrieval Augmented Generation)</b> pipeline to answer questions about Chicago crime data using AI.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Tech Stack")
    techs = ["Gemini Embedding API", "BigQuery Vector Search", "Gemini 2.5 Flash", "Streamlit", "Python"]
    for tech in techs:
        st.markdown(f"- {tech}")

    st.markdown("### 💡 Sample Questions")
    samples = [
        "Which areas had most gun crimes?",
        "What crimes happen most at night?",
        "Are weapons violations common in apartments?",
        "What is the most common crime type?"
    ]
    for s in samples:
        st.markdown(f"- *{s}*")

    st.markdown("---")
    st.markdown("<div style='color:#555;font-size:0.8rem'>Built by Priyanshu Pandita</div>", unsafe_allow_html=True)

# Hero section
st.markdown('<p class="hero-title">🚔 Chicago Crime Intelligence</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Ask anything about Chicago crime data — powered by RAG + Gemini AI</p>', unsafe_allow_html=True)

# Stats row
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-number">500</div>
        <div class="stat-label">Crime Records Indexed</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-number">3072</div>
        <div class="stat-label">Embedding Dimensions</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-number">Gemini</div>
        <div class="stat-label">AI Model</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# Functions
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_crimes(user_question, top_k=5):
    q_embedding = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=user_question
    ).embeddings[0].values

    query = """
    SELECT unique_key, primary_type, description, location_description, year, text, embedding
    FROM `project-72181980-533d-4978-aa7.de_practice.chicago_crime_embeddings`
    """
    df = client_bq.query(query).to_dataframe()
    df['similarity'] = df['embedding'].apply(
        lambda x: cosine_similarity(q_embedding, json.loads(x))
    )
    top_results = df.sort_values('similarity', ascending=False).head(top_k)
    return top_results[['primary_type', 'description', 'location_description', 'year', 'similarity']]

def answer_question(user_question):
    search_results = search_crimes(user_question, top_k=5)
    context = "Here are the most relevant crime records:\n\n"
    for idx, row in search_results.iterrows():
        context += f"- {row['primary_type']}: {row['description']} at {row['location_description']} ({row['year']})\n"

    prompt = f"""Based on these Chicago crime records:

{context}

Answer this question: {user_question}

Provide a clear, concise answer based only on the data provided."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text, search_results

# Search section
st.markdown("### 🔍 Ask a Question")
user_question = st.text_input("", placeholder="e.g. Which areas had most gun crimes in residential areas?")

if st.button("🔍 Search & Analyze") and user_question:
    with st.spinner("🔎 Searching crime records and generating AI answer..."):
        answer, results = answer_question(user_question)

    st.markdown("### 💬 AI Answer")
    st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

    st.markdown("### 📋 Relevant Records Found")
    st.dataframe(
        results.style.background_gradient(subset=['similarity'], cmap='Reds'),
        use_container_width=True
    )