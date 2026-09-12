# Learning Recommendation System

A Streamlit web app that generates personalized job recommendations for students by analyzing their resume and academic profile using Google's Gemini AI.

## Features
- 📄 Extracts text from uploaded PDF resumes (PyMuPDF)
- 🤖 Generates tailored job descriptions and career advice via Google Gemini (`gemini-1.5-pro`)
- 📝 Collects student profile data: education, degree, completed modules, quizzes, certifications, internships, and more
- ✅ Form validation for required fields and progress tracking (assignments, modules, quizzes)
- 🗄️ Persists recommendations and student data to a MySQL database (SQLAlchemy ORM)

## Tech Stack
- **Frontend/UI:** Streamlit
- **AI Model:** Google Generative AI (Gemini)
- **PDF Parsing:** PyMuPDF (fitz)
- **Database:** MySQL + SQLAlchemy

## Setup
1. Install dependencies: `pip install streamlit google-generativeai PyMuPDF sqlalchemy pymysql`
2. Set your API key: `export GOOGLE_GENERATIVE_AI_API_KEY=your_key_here`
3. Configure your MySQL connection string
4. Run: `streamlit run job1.py`

## How It Works
Students fill out a profile form and upload their resume (PDF). The app extracts resume text, sends it to Gemini with a structured prompt, parses the AI's response into job title, responsibilities, qualifications, and personalized advice, then stores everything in a database.
