import os
import textwrap
import google.generativeai as genai
import streamlit as st
import fitz  # PyMuPDF
from sqlalchemy import Integer, create_engine, Column, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# Set up the API key for Google Generative AI
api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY", "AIzaSyDUougpBtSxniIZYHyrYLwQFPLomXX5h90")
genai.configure(api_key=api_key)

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-1.5-pro')

# Function to format text as Markdown
def to_markdown(text):
    text = text.replace('•', '  *')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Failed to extract text from PDF: {e}")
        return ""

# Function to generate the prompt based on resume contents
def generate_prompt_from_resume(resume_text):
    return f"""
Role: Career advisor specializing in job recommendations for students.

Instruction: Analyze the resume contents and generate a suitable job description and personalized advice based on this student's information:

Resume Details:
{resume_text}

Step 1: Generate a suitable job description including:
- Job Title
- Salary Range (Optional)
- Company details (Name, Industry, Size, Culture)
- Responsibilities (3 key responsibilities)
- Qualifications (Optional - Educational Background,Technical Skills,Strong Communication Skills,Project Completed)
- Additional Information (Optional - Company culture, industry trends)
- How to Apply (3 steps)

Step 2: Provide personalized advice for the student based on their profile and the generated job description.

Job Recommendation Output:

Job Title:
Salary Range: (Optional)
Company: (Name, Industry, Size, Culture)
Responsibilities:
    1.
    2.
    3.
Qualifications:
    1.
    2.
    3.
Additional Information: (Optional - Company culture, industry trends)
How to Apply:
    1.
    2.
    3.
Personalized Advice:
"""

# Database setup
DATABASE_URL = "mysql+pymysql://root:rohit@localhost/Student_recommendationsdb?charset=utf8mb4"
Base = declarative_base()

# Define the database model with appropriate column sizes
class Recommendation(Base):
    __tablename__ = 'recommendations'
    name = Column(String(255))
    email = Column(String(255), primary_key=True)
    education = Column(String(255))
    degree = Column(String(255))
    year_of_passing = Column(String(4))
    course = Column(String(255))
    job_title = Column(Text)
    salary_range = Column(Text)
    company = Column(Text)
    responsibilities = Column(Text)
    qualifications = Column(Text)
    additional_info = Column(Text)
    personalized_advice = Column(Text)
    completed_modules = Column(String(255))
    assignment_completion = Column(Integer) 
    passed_quizzes = Column(String(255))
    projects_completed = Column(String(255))
    certifications = Column(String(255))
    internship = Column(String(255))
    resume = Column(Text)
    active_job_platforms = Column(String(255))

# Create the database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# Function to extract job details from generated text
def extract_job_details(generated_text):
    job_details = {
        "Job Title": None,
        "Salary Range": None,
        "Company": None,
        "Responsibilities": None,
        "Qualifications": None,
        "Additional Info": None,
        "Personalized Advice": None
    }

    # Extract job title
    job_title_start = generated_text.find("Job Title:")
    if job_title_start != -1:
        job_title_end = generated_text.find("\n", job_title_start)
        job_details["Job Title"] = generated_text[job_title_start + len("Job Title:"):job_title_end].strip()

    # Extract salary range
    salary_range_start = generated_text.find("Salary Range:")
    if salary_range_start != -1:
        salary_range_end = generated_text.find("\n", salary_range_start)
        job_details["Salary Range"] = generated_text[salary_range_start + len("Salary Range:"):salary_range_end].strip()

    # Extract company details
    company_start = generated_text.find("Company:")
    if company_start != -1:
        company_end = generated_text.find("Responsibilities:", company_start)
        job_details["Company"] = generated_text[company_start + len("Company:"):company_end].strip()

    # Extract responsibilities
    responsibilities_start = generated_text.find("Responsibilities:")
    if responsibilities_start != -1:
        qualifications_start = generated_text.find("Qualifications:", responsibilities_start)
        job_details["Responsibilities"] = generated_text[responsibilities_start + len("Responsibilities:"):qualifications_start].strip()

    # Extract qualifications
    qualifications_start = generated_text.find("Qualifications:")
    if qualifications_start != -1:
        additional_info_start = generated_text.find("Additional Information:", qualifications_start)
        job_details["Qualifications"] = generated_text[qualifications_start + len("Qualifications:"):additional_info_start].strip()

    # Extract additional information
    additional_info_start = generated_text.find("Additional Information:")
    if additional_info_start != -1:
        personalized_advice_start = generated_text.find("Personalized Advice:", additional_info_start)
        job_details["Additional Info"] = generated_text[additional_info_start + len("Additional Information:"):personalized_advice_start].strip()

    # Extract personalized advice
    personalized_advice_start = generated_text.find("Personalized Advice:")
    if personalized_advice_start != -1:
        job_details["Personalized Advice"] = generated_text[personalized_advice_start + len("Personalized Advice:"):].strip()

    return job_details

# Generate the results with the Google Generative AI model
def generate_job_recommendation(student_info, resume_text):
    try:
        prompt = generate_prompt_from_resume(resume_text)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Failed to generate recommendation: {e}")
        return ""

# Function to clean asterisks from text fields
def clean_asterisks(text):
    return text.replace('*', '') if text else text

# Streamlit app
st.title("Job Recommendation System")

# Sidebar for uploading a PDF and submitting the form
st.sidebar.header("Upload Your Resume")
with st.sidebar:
    uploaded_file = st.file_uploader("Please Upload Your Resume Here", type=["pdf"])
    if uploaded_file is not None:
        st.write("Uploaded file:")
        st.write(uploaded_file.name)
        resume_text = extract_text_from_pdf(uploaded_file)

    # Check for uploaded resume
    if uploaded_file is None:
        st.warning("Please upload your resume.")
        missing_resume = True

# User input form
with st.form("student_info_form"):
    col1, col2 = st.columns(2)
    with col1:
        st.write("Enter Student Details")
    with col2:
        st.write("Enter Course Details")
    with col1:
        student_name = st.text_input("Name", placeholder="Please Enter Your Name")
        student_email = st.text_input("Email", placeholder="Please Enter Your Email")
        education = st.selectbox(
            "Education",
            [
                "Select Education",
                "Other",
                "High School",
                "GED (General Educational Development)",
                "Associate of Arts (AA)",
                "Associate of Science (AS)",
                "Associate of Applied Science (AAS)",
                "Bachelor of Arts (BA)",
                "Bachelor of Arts (BA) (Economics)",
                "Bachelor of Arts (BA) (English)",
                "Bachelor of Arts (BA) (History)",
                "Bachelor of Arts (BA) (Political Science)",
                "Bachelor of Arts (BA) (Psychology)",
                "Bachelor of Arts (BA) (Sociology)",
                "Bachelor of Arts (BA) (Philosophy)",
                "Bachelor of Arts (BA) (Anthropology)",
                "Bachelor of Arts (BA) (Linguistics)",
                "Bachelor of Arts (BA) (Journalism)",
                "Bachelor of Arts (BA) (Geography)",
                "Bachelor of Science (BS)",
                "Bachelor of Science (BS) (Biology)",
                "Bachelor of Science (BS) (Chemistry)",
                "Bachelor of Science (BS) (Physics)",
                "Bachelor of Science (BS) (Mathematics)",
                "Bachelor of Science (BS) (Statistics)",
                "Bachelor of Science (BS) (Computer Science)",
                "Bachelor of Science (BS) (Environmental Science)",
                "Bachelor of Science (BS) (Geology)",
                "Bachelor of Science (BS) (Psychology)",
                "Bachelor of Science (BS) (Nursing)",
                "Bachelor of Business Administration (BBA)",
                "Bachelor of Business Administration (BBA) (Finance)",
                "Bachelor of Business Administration (BBA) (Marketing)",
                "Bachelor of Business Administration (BBA) (Human Resources)",
                "Bachelor of Business Administration (BBA) (International Business)",
                "Bachelor of Business Administration (BBA) (Operations Management)",
                "Bachelor of Business Administration (BBA) (Entrepreneurship)",
                "Bachelor of Business Administration (BBA) (Supply Chain Management)",
                "Bachelor of Computer Applications (BCA)",
                "Bachelor of Computer Applications (BCA) (General)",
                "Bachelor of Computer Applications (BCA) (Database Management)",
                "Bachelor of Computer Applications (BCA) (Software Development)",
                "Bachelor of Computer Applications (BCA) (Networking)",
                "Bachelor of Fine Arts (BFA)",
                "Bachelor of Fine Arts (BFA) (Painting)",
                "Bachelor of Fine Arts (BFA) (Sculpture)",
                "Bachelor of Fine Arts (BFA) (Graphic Design)",
                "Bachelor of Fine Arts (BFA) (Photography)",
                "Bachelor of Fine Arts (BFA) (Animation)",
                "Bachelor of Engineering (BE or BEng)",
                "Bachelor of Engineering (BE) (Civil Engineering)",
                "Bachelor of Engineering (BE) (Mechanical Engineering)",
                "Bachelor of Engineering (BE) (Computer Science and Engineering)",
                "Bachelor of Engineering (BE) (Electrical Engineering)",
                "Bachelor of Engineering (BE) (Electronics and Communication Engineering)",
                "Bachelor of Engineering (BE) (Chemical Engineering)",
                "Bachelor of Engineering (BE) (Aeronautical Engineering)",
                "Bachelor of Engineering (BE) (Automobile Engineering)",
                "Bachelor of Engineering (BE) (Biomedical Engineering)",
                "Bachelor of Engineering (BE) (Biotechnology Engineering)",
                "Bachelor of Engineering (BE) (Environmental Engineering)",
                "Bachelor of Engineering (BE) (Industrial Engineering)",
                "Bachelor of Engineering (BE) (Information Technology)",
                "Bachelor of Engineering (BE) (Instrumentation Engineering)",
                "Bachelor of Engineering (BE) (Marine Engineering)",
                "Bachelor of Engineering (BE) (Materials Science and Engineering)",
                "Bachelor of Engineering (BE) (Metallurgical Engineering)",
                "Bachelor of Engineering (BE) (Mining Engineering)",
                "Bachelor of Engineering (BE) (Petroleum Engineering)",
                "Bachelor of Engineering (BE) (Power Engineering)",
                "Bachelor of Engineering (BE) (Production Engineering)",
                "Bachelor of Engineering (BE) (Software Engineering)",
                "Bachelor of Engineering (BE) (Textile Engineering)",
                "Bachelor of Technology (BTech)",
                "Bachelor of Technology (BTech) (Civil Engineering)",
                "Bachelor of Technology (BTech) (Mechanical Engineering)",
                "Bachelor of Technology (BTech) (Computer Science and Engineering)",
                "Bachelor of Technology (BTech) (Information Technology)",
                "Bachelor of Technology (BTech) (Electrical Engineering)",
                "Bachelor of Technology (BTech) (Electronics and Communication Engineering)",
                "Bachelor of Technology (BTech) (Chemical Engineering)",
                "Bachelor of Technology (BTech) (Aeronautical Engineering)",
                "Bachelor of Technology (BTech) (Automobile Engineering)",
                "Bachelor of Technology (BTech) (Biomedical Engineering)",
                "Bachelor of Technology (BTech) (Biotechnology Engineering)",
                "Bachelor of Technology (BTech) (Environmental Engineering)",
                "Bachelor of Technology (BTech) (Industrial Engineering)",
                "Bachelor of Technology (BTech) (Instrumentation Engineering)",
                "Bachelor of Technology (BTech) (Marine Engineering)",
                "Bachelor of Technology (BTech) (Materials Science and Engineering)",
                "Bachelor of Technology (BTech) (Metallurgical Engineering)",
                "Bachelor of Technology (BTech) (Mining Engineering)",
                "Bachelor of Technology (BTech) (Petroleum Engineering)",
                "Bachelor of Technology (BTech) (Power Engineering)",
                "Bachelor of Technology (BTech) (Production Engineering)",
                "Bachelor of Technology (BTech) (Software Engineering)",
                "Bachelor of Technology (BTech) (Textile Engineering)",
                "Bachelor of Computer Science (BCS)",
                "Bachelor of Education (BEd)",
                "Bachelor of Laws (LLB)",
                "Bachelor of Medicine, Bachelor of Surgery (MBBS)",
                "Master of Arts (MA)",
                "Master of Arts (MA) (Economics)",
                "Master of Arts (MA) (English)",
                "Master of Arts (MA) (History)",
                "Master of Arts (MA) (Political Science)",
                "Master of Arts (MA) (Psychology)",
                "Master of Arts (MA) (Sociology)",
                "Master of Arts (MA) (Philosophy)",
                "Master of Arts (MA) (Anthropology)",
                "Master of Arts (MA) (Linguistics)",
                "Master of Arts (MA) (Journalism)",
                "Master of Arts (MA) (Geography)",
                "Master of Science (MS or MSc)",
                "Master of Science (MS) (Biology)",
                "Master of Science (MS) (Chemistry)",
                "Master of Science (MS) (Physics)",
                "Master of Science (MS) (Mathematics)",
                "Master of Science (MS) (Statistics)",
                "Master of Science (MS) (Computer Science)",
                "Master of Science (MS) (Environmental Science)",
                "Master of Science (MS) (Geology)",
                "Master of Science (MS) (Psychology)",
                "Master of Science (MS) (Nursing)",
                "Master of Business Administration (MBA)",
                "Master of Business Administration (MBA) (Finance)",
                "Master of Business Administration (MBA) (Marketing)",
                "Master of Business Administration (MBA) (Human Resources)",
                "Master of Business Administration (MBA) (International Business)",
                "Master of Business Administration (MBA) (Operations Management)",
                "Master of Business Administration (MBA) (Entrepreneurship)",
                "Master of Business Administration (MBA) (Supply Chain Management)",
                "Master of Computer Applications (MCA)",
                "Master of Computer Applications (MCA) (General)",
                "Master of Computer Applications (MCA) (Database Management)",
                "Master of Computer Applications (MCA) (Software Development)",
                "Master of Computer Applications (MCA) (Networking)",
                "Master of Fine Arts (MFA)",
                "Master of Fine Arts (MFA) (Painting)",
                "Master of Fine Arts (MFA) (Sculpture)",
                "Master of Fine Arts (MFA) (Graphic Design)",
                "Master of Fine Arts (MFA) (Photography)",
                "Master of Fine Arts (MFA) (Animation)",
                "Master of Engineering (ME)",
                "Master of Engineering (ME) (Civil Engineering)",
                "Master of Engineering (ME) (Mechanical Engineering)",
                "Master of Engineering (ME) (Computer Science and Engineering)",
                "Master of Engineering (ME) (Electrical Engineering)",
                "Master of Engineering (ME) (Electronics and Communication Engineering)",
                "Master of Engineering (ME) (Chemical Engineering)",
                "Master of Engineering (ME) (Aeronautical Engineering)",
                "Master of Engineering (ME) (Automobile Engineering)",
                "Master of Engineering (ME) (Biomedical Engineering)",
                "Master of Engineering (ME) (Biotechnology Engineering)",
                "Master of Engineering (ME) (Environmental Engineering)",
                "Master of Engineering (ME) (Industrial Engineering)",
                "Master of Engineering (ME) (Information Technology)",
                "Master of Engineering (ME) (Instrumentation Engineering)",
                "Master of Engineering (ME) (Marine Engineering)",
                "Master of Engineering (ME) (Materials Science and Engineering)",
                "Master of Engineering (ME) (Metallurgical Engineering)",
                "Master of Engineering (ME) (Mining Engineering)",
                "Master of Engineering (ME) (Petroleum Engineering)",
                "Master of Engineering (ME) (Power Engineering)",
                "Master of Engineering (ME) (Production Engineering)",
                "Master of Engineering (ME) (Software Engineering)",
                "Master of Engineering (ME) (Textile Engineering)",
                "Master of Technology (MTech)",
                "Master of Technology (MTech) (Civil Engineering)",
                "Master of Technology (MTech) (Mechanical Engineering)",
                "Master of Technology (MTech) (Computer Science and Engineering)",
                "Master of Technology (MTech) (Information Technology)",
                "Master of Technology (MTech) (Electrical Engineering)",
                "Master of Technology (MTech) (Electronics and Communication Engineering)",
                "Master of Technology (MTech) (Chemical Engineering)",
                "Master of Technology (MTech) (Aeronautical Engineering)",
                "Master of Technology (MTech) (Automobile Engineering)",
                "Master of Technology (MTech) (Biomedical Engineering)",
                "Master of Technology (MTech) (Biotechnology Engineering)",
                "Master of Technology (MTech) (Environmental Engineering)",
                "Master of Technology (MTech) (Industrial Engineering)",
                "Master of Technology (MTech) (Instrumentation Engineering)",
                "Master of Technology (MTech) (Marine Engineering)",
                "Master of Technology (MTech) (Materials Science and Engineering)",
                "Master of Technology (MTech) (Metallurgical Engineering)",
                "Master of Technology (MTech) (Mining Engineering)",
                "Master of Technology (MTech) (Petroleum Engineering)",
                "Master of Technology (MTech) (Power Engineering)",
                "Master of Technology (MTech) (Production Engineering)",
                "Master of Technology (MTech) (Software Engineering)",
                "Master of Technology (MTech) (Textile Engineering)",
                "Master of Computer Science (MCS)",
                "Master of Education (MEd)",
                "Master of Laws (LLM)",
                "Master of Public Health (MPH)",
                "Master of Social Work (MSW)",
                "Master of Medicine (MMed)",
                "Doctor of Philosophy (PhD)",
                "Doctor of Philosophy (PhD) (Engineering)",
                "Doctor of Philosophy (PhD) (Science)",
                "Doctor of Philosophy (PhD) (Humanities)",
                "Doctor of Philosophy (PhD) (Social Sciences)",
                "Doctor of Philosophy (PhD) (Management)",
                "Doctor of Philosophy (PhD) (Education)",
                "Doctor of Philosophy (PhD) (Medicine)",
                "Doctor of Philosophy (PhD) (Law)",
                "Doctor of Philosophy (PhD) (Public Health)",
                "Doctor of Medicine (MD)",
                "Doctor of Education (EdD)",
                "Doctor of Business Administration (DBA)",
                "Doctor of Law (JD)",
                "Doctor of Engineering (DEng)",
                "Doctor of Science (DSc)",
                "Medical Doctor (MD)",
                "Doctor of Dental Surgery (DDS)",
                "Doctor of Veterinary Medicine (DVM)",
                "Doctor of Pharmacy (PharmD)"
            ],
            index=0
        )

        degree = st.selectbox("Degree", ["Select Degree","Under Graduate(UG)","Post Graduate(PG)","Graduate","Doctorate","Others"], index=0)
        year_of_passing = st.slider("Year of Passing", min_value=2010, max_value=2030, value=2024)
        linkedin = st.text_input("LinkedIn URL", placeholder="Enter Your URL")

    with col2:
        course = st.selectbox("Course", ["Select Course", "Data Science"], index=0)
        all_modules = ["Python", "EDA", "SQL", "Power BI", "Data Science"]
        completed_modules = st.multiselect("Completed Modules", all_modules)
        assignment_completion = st.slider("Assignment Completion (%)", min_value=0, max_value=100, value=0, step=1, help="Percentage of assignments completed")
        all_quizzes = ["Python Quiz", "EDA Quiz", "SQL Quiz", "Power BI Quiz", "Data Science Quiz"]
        passed_quizzes = st.multiselect("Passed Quizzes", all_quizzes)
        projects_completed = st.selectbox("Number of Projects Completed", options=[str(i) for i in range(7)], index=0)
        internship = st.radio("Internship", ["Yes", "No"], index=1)

    col3 = st.columns(2)
    all_certifications = ["SUNY", "NASSCOM", "INNODATATICS", "IBM", "UTM", "Python Programming", "R programming",
                          "Basic course on SQL", "Data Visualization using Power BI", "Data Science using Python & R Programming",
                          "Data Science using AI", "Certificate Program on Data Science"]
    certifications = st.multiselect("Certifications", all_certifications)
    resume_status = st.selectbox("Resume Status", ["Select", "Created", "Not Created", "Updated"], index=0)
    all_jobs = ["LinkedIn", "Indeed", "Glassdoor", "Monster", "CareerBuilder", "SimplyHired", "ZipRecruiter", "AngelList", 
                "FlexJobs", "Dice", "Naukri.com", "Hired", "Job.com", "Snagajob", "Upwork", "Guru", "Toptal", "We Work Remotely", 
                "Remote.co"]
    active_job_platforms = st.multiselect("Active Job Platforms", all_jobs)

    form_submitted = st.form_submit_button("Generate Recommendation")

# Check if the form is submitted
if form_submitted:
    # Track whether we have any empty required fields
    missing_required_fields = False

    # Check for empty 'Name' field
    if not student_name.strip():
        st.warning("Please enter your name in the 'Name' field.")
        missing_required_fields = True

    # Check for empty 'Email' field
    if not student_email.strip():
        st.warning("Please enter your email in the 'Email' field.")
        missing_required_fields = True

    # Check for 'Select Education' field
    if education == "Select Education":
        st.warning("Please select an education level from the 'Education' field.")
        missing_required_fields = True

    # Check for 'Select Degree' field
    if degree == "Select Degree":
        st.warning("Please select a degree from the 'Degree' field.")
        missing_required_fields = True

    # Check for 'Select Course' field
    if course == "Select Course":
        st.warning("Please select a course from the 'Course' field.")
        missing_required_fields = True

    # Check for 'Completed Modules' field - must select at least one
    if not completed_modules:
        st.warning("Please select at least one module in 'Completed Modules'.")
        missing_required_fields = True
    else:
        # Warn about uncompleted modules
        uncompleted_modules = [module for module in all_modules if module not in completed_modules]
        for module in uncompleted_modules:
            st.warning(f"Please complete your '{module}' module.")

    # Check for 'Passed Quizzes' field - must select at least one
    if not passed_quizzes:
        st.warning("Please pass at least one quiz in 'Passed Quizzes'.")
        missing_required_fields = True
    else:
        # Warn about unpassed quizzes
        unpassed_quizzes = [quiz for quiz in all_quizzes if quiz not in passed_quizzes]
        for quiz in unpassed_quizzes:
            st.warning(f"Please pass the '{quiz}' .")

    # Check assignment completion percentage and warn if below 80%
    if assignment_completion < 80:
        st.warning("Please note that your assignment completion is below 80%.")

    # Proceed only if all required fields are filled
    if not missing_required_fields:
        student_info = {
            "name": student_name,
            "email": student_email,
            "education": education,
            "degree": degree,
            "year_of_passing": str(year_of_passing),
            "course": course,
            "linkedin": linkedin,
            "completed_modules": ", ".join(completed_modules),
            "Assignment Completion": assignment_completion,
            "passed_quizzes": ", ".join(passed_quizzes),
            "projects_completed": projects_completed,
            "certifications": ",".join(certifications),
            "internship": internship,
            "resume": resume_status,
            "active_job_platforms": ",".join(active_job_platforms)
        }

        if uploaded_file is not None:
            generated_text = generate_job_recommendation(student_info, resume_text)
            job_details = extract_job_details(generated_text)

            # Clean asterisks from job details
            job_details = {k: clean_asterisks(v) for k, v in job_details.items()}

            st.write("### Generated Job Recommendation:")
            st.markdown(to_markdown(generated_text))

            # Save the job details to the MySQL database
            db_session = SessionLocal()
            recommendation = Recommendation(
                name=student_info["name"],
                email=student_info["email"],
                education=student_info["education"],
                degree=student_info["degree"],
                year_of_passing=student_info["year_of_passing"],
                course=student_info["course"],
                job_title=job_details.get("Job Title"),
                salary_range=job_details.get("Salary Range"),
                company=job_details.get("Company"),
                responsibilities=job_details.get("Responsibilities"),
                qualifications=job_details.get("Qualifications"),
                additional_info=job_details.get("Additional Info"),
                personalized_advice=job_details.get("Personalized Advice"),
                completed_modules=student_info["completed_modules"],
                assignment_completion=assignment_completion,
                passed_quizzes=student_info["passed_quizzes"],
                projects_completed=student_info["projects_completed"],
                certifications=student_info["certifications"],
                internship=student_info["internship"],
                resume=student_info["resume"],
                active_job_platforms=student_info["active_job_platforms"]
            )

            db_session.add(recommendation)
            db_session.commit()
            db_session.close()

            st.success(f"Generated recommendation for {student_info['name']} saved to the database.")
    else:
        st.warning("Please fill all the required fields before generating a recommendation.")
