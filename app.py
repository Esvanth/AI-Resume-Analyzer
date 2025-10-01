import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.resume_parser import ResumeParser
from src.nlp_processor import NLPProcessor
from src.scorer import ResumeScorer
import tempfile
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .skill-tag {
        background: #e1f5fe;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_processors():
    """Load and cache the processing components"""
    try:
        parser = ResumeParser()
        nlp_processor = NLPProcessor()
        scorer = ResumeScorer()
        return parser, nlp_processor, scorer
    except Exception as e:
        st.error(f"Error loading processors: {str(e)}")
        return None, None, None

def create_gauge_chart(score_percentage, title="Overall Score"):
    """Create a gauge chart for score visualization"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score_percentage,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20}},
        delta = {'reference': 70, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ffebee'},
                {'range': [40, 70], 'color': '#fff3e0'},
                {'range': [70, 100], 'color': '#e8f5e8'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        font={'color': "darkblue", 'family': "Arial"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

def create_component_bar_chart(component_scores):
    """Create bar chart for component scores"""
    components = list(component_scores.keys())
    scores = [score * 100 for score in component_scores.values()]
    
    # Clean up component names
    clean_components = []
    for comp in components:
        clean_name = comp.replace('_', ' ').title()
        if clean_name == 'Skills Match':
            clean_name = 'Skills Match'
        elif clean_name == 'Experience Years':
            clean_name = 'Experience'
        elif clean_name == 'Resume Quality':
            clean_name = 'Resume Quality'
        clean_components.append(clean_name)
    
    fig = go.Figure(data=[
        go.Bar(
            x=clean_components,
            y=scores,
            marker_color=['#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            text=[f'{score:.1f}%' for score in scores],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Score Breakdown by Component",
        xaxis_title="Components",
        yaxis_title="Score (%)",
        yaxis=dict(range=[0, 100]),
        height=400,
        showlegend=False
    )
    
    return fig

def display_skills(skills_dict):
    """Display skills in a formatted way"""
    if not skills_dict:
        st.write("No skills detected")
        return
    
    for category, skills in skills_dict.items():
        if skills:
            st.write(f"**{category.title().replace('_', ' ')}:**")
            skills_html = ""
            for skill in skills:
                skills_html += f'<span class="skill-tag">{skill}</span>'
            st.markdown(skills_html, unsafe_allow_html=True)
            st.write("")  # Add spacing

def process_job_requirements():
    """Process job requirements from sidebar inputs"""
    st.sidebar.header("📋 Job Requirements")
    st.sidebar.markdown("---")
    
    # Required Skills
    required_skills_input = st.sidebar.text_area(
        "Required Skills (comma-separated)",
        placeholder="Python, SQL, Machine Learning, React, etc.",
        help="Enter the essential skills for this position"
    )
    
    # Nice-to-have Skills
    nice_to_have_input = st.sidebar.text_area(
        "Nice-to-Have Skills (comma-separated)",
        placeholder="Docker, AWS, Kubernetes, etc.",
        help="Enter additional skills that would be beneficial"
    )
    
    # Experience Requirements
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_experience = st.number_input(
            "Min Experience (years)",
            min_value=0,
            max_value=20,
            value=2,
            help="Minimum years of experience required"
        )
    
    with col2:
        preferred_experience = st.number_input(
            "Preferred Experience (years)",
            min_value=0,
            max_value=30,
            value=5,
            help="Preferred years of experience"
        )
    
    # Education Requirements
    education_options = ["None", "Associates", "Bachelors", "Masters", "PhD"]
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        required_education = st.selectbox(
            "Required Education",
            education_options,
            index=2,  # Default to Bachelors
            help="Minimum education level required"
        )
    
    with col2:
        preferred_education = st.selectbox(
            "Preferred Education",
            education_options,
            index=3,  # Default to Masters
            help="Preferred education level"
        )
    
    # Job Details (Optional)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📝 Job Details (Optional)")
    
    job_title = st.sidebar.text_input("Job Title", placeholder="e.g., Senior Software Engineer")
    company_name = st.sidebar.text_input("Company Name", placeholder="e.g., Tech Corp Inc.")
    
    # Process inputs
    required_skills = [skill.strip() for skill in required_skills_input.split(',') if skill.strip()]
    nice_to_have_skills = [skill.strip() for skill in nice_to_have_input.split(',') if skill.strip()]
    
    job_requirements = {
        'required_skills': required_skills,
        'nice_to_have_skills': nice_to_have_skills,
        'min_experience': min_experience,
        'preferred_experience': preferred_experience if preferred_experience > min_experience else None,
        'education_level': required_education if required_education != "None" else None,
        'preferred_education_level': preferred_education if preferred_education != "None" and preferred_education != required_education else None,
        'job_title': job_title,
        'company_name': company_name
    }
    
    return job_requirements

def main():
    # Header
    st.markdown('<div class="main-header"><h1>🤖 AI Resume Screener</h1><p>Upload resumes and get AI-powered candidate scoring</p></div>', unsafe_allow_html=True)
    
    # Load processors
    parser, nlp_processor, scorer = load_processors()
    
    if not all([parser, nlp_processor, scorer]):
        st.error("Failed to load required components. Please check your installation.")
        st.stop()
    
    # Process job requirements from sidebar
    job_requirements = process_job_requirements()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📁 Upload Resume")
        
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'docx'],
            help="Supported formats: PDF, DOCX (Max size: 200MB)"
        )
        
        # Display job requirements summary
        if any(job_requirements.values()):
            st.subheader("📋 Current Job Requirements")
            
            if job_requirements['job_title']:
                st.write(f"**Position:** {job_requirements['job_title']}")
            if job_requirements['company_name']:
                st.write(f"**Company:** {job_requirements['company_name']}")
            
            if job_requirements['required_skills']:
                st.write(f"**Required Skills:** {', '.join(job_requirements['required_skills'])}")
            
            if job_requirements['nice_to_have_skills']:
                st.write(f"**Nice-to-have:** {', '.join(job_requirements['nice_to_have_skills'])}")
            
            st.write(f"**Experience:** {job_requirements['min_experience']}+ years")
            
            if job_requirements['education_level']:
                st.write(f"**Education:** {job_requirements['education_level']} degree")
    
    with col2:
        if uploaded_file is None:
            st.header("👋 Getting Started")
            st.info("""
            1. **Set Job Requirements** in the sidebar
            2. **Upload a resume** using the file uploader
            3. **Get instant AI analysis** and scoring
            4. **Review detailed breakdown** and recommendations
            """)
            
            # Sample requirements
            st.subheader("💡 Sample Job Requirements")
            st.code("""
Required Skills: Python, SQL, Machine Learning, Pandas
Nice-to-have: Docker, AWS, React
Experience: 3+ years
Education: Bachelors degree
            """)
    
    # Process uploaded file
    if uploaded_file is not None:
        try:
            with st.spinner("🔄 Processing resume... This may take a few moments."):
                # Parse resume
                resume_text = parser.parse_resume(uploaded_file)
                
                if not resume_text or len(resume_text.strip()) < 50:
                    st.error("Could not extract sufficient text from the resume. Please ensure the file is readable and contains text.")
                    st.stop()
                
                # Process with NLP
                processed_data = nlp_processor.process_resume(resume_text)
                
                # Calculate score
                scoring_result = scorer.calculate_overall_score(processed_data, job_requirements)
            
            # Display Results
            st.header("📊 Analysis Results")
            
            # Overall Score Section
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Gauge chart
                gauge_fig = create_gauge_chart(scoring_result['score_percentage'])
                st.plotly_chart(gauge_fig, use_container_width=True)
            
            with col2:
                st.metric(
                    label="Overall Score",
                    value=f"{scoring_result['score_percentage']}%",
                    delta=f"{scoring_result['score_percentage'] - 70:.1f}% from benchmark"
                )
                
                # Recommendation
                recommendation = scoring_result.get('recommendation', 'No recommendation')
                if 'Strong' in recommendation:
                    st.success(recommendation)
                elif 'Good' in recommendation:
                    st.info(recommendation)
                elif 'Moderate' in recommendation:
                    st.warning(recommendation)
                else:
                    st.error(recommendation)
            
            with col3:
                # Quick stats
                st.metric("Experience", f"{processed_data['experience']['total_years']} years")
                st.metric("Education", processed_data['education']['level'] or 'Not specified')
                total_skills = sum(len(skills) for skills in processed_data['skills'].values())
                st.metric("Skills Found", total_skills)
            
            # Component Scores
            st.subheader("📈 Detailed Score Breakdown")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Bar chart
                bar_fig = create_component_bar_chart(scoring_result['component_scores'])
                st.plotly_chart(bar_fig, use_container_width=True)
            
            with col2:
                # Component scores as metrics
                st.write("**Individual Component Scores:**")
                for component, score in scoring_result['component_scores'].items():
                    clean_name = component.replace('_', ' ').title()
                    st.metric(
                        label=clean_name,
                        value=f"{score:.2f}",
                        delta=f"{score - 0.7:.2f}" if score != 0 else None
                    )
            
            # Detailed Information Sections
            st.header("📋 Extracted Information")
            
            tab1, tab2, tab3, tab4 = st.tabs(["👤 Contact", "💼 Experience", "🎓 Education", "🛠️ Skills"])
            
            with tab1:
                st.subheader("Contact Information")
                contact = processed_data['contact_info']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if contact['email']:
                        st.success(f"📧 **Email:** {contact['email']}")
                    else:
                        st.warning("📧 **Email:** Not found")
                
                with col2:
                    if contact['phone']:
                        st.success(f"📞 **Phone:** {contact['phone']}")
                    else:
                        st.warning("📞 **Phone:** Not found")
                
                with col3:
                    if contact['linkedin']:
                        st.success(f"💼 **LinkedIn:** {contact['linkedin']}")
                    else:
                        st.warning("💼 **LinkedIn:** Not found")
            
            with tab2:
                st.subheader("Professional Experience")
                experience = processed_data['experience']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Experience", f"{experience['total_years']} years")
                    
                    if experience.get('organizations'):
                        st.write("**Organizations:**")
                        for org in experience['organizations'][:5]:  # Show top 5
                            st.write(f"• {org}")
                
                with col2:
                    if experience.get('job_titles'):
                        st.write("**Job Titles Found:**")
                        for title in experience['job_titles'][:5]:  # Show top 5
                            st.write(f"• {title}")
            
            with tab3:
                st.subheader("Educational Background")
                education = processed_data['education']
                
                col1, col2 = st.columns(2)
                with col1:
                    if education['has_degree']:
                        st.success(f"🎓 **Degree Level:** {education['level'] or 'Detected but unspecified'}")
                    else:
                        st.warning("🎓 **Degree:** Not clearly identified")
                
                with col2:
                    if education.get('institutions'):
                        st.write("**Institutions:**")
                        for institution in education['institutions'][:3]:
                            st.write(f"• {institution}")
            
            with tab4:
                st.subheader("Technical & Professional Skills")
                display_skills(processed_data['skills'])
            
            # Feedback Section
            if 'feedback' in scoring_result:
                st.header("💡 AI Feedback & Recommendations")
                
                feedback = scoring_result['feedback']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'skills' in feedback:
                        st.info(f"**Skills:** {feedback['skills']}")
                    
                    if 'experience' in feedback:
                        st.info(f"**Experience:** {feedback['experience']}")
                
                with col2:
                    if 'education' in feedback:
                        st.info(f"**Education:** {feedback['education']}")
                    
                    if 'quality' in feedback:
                        st.info(f"**Resume Quality:** {feedback['quality']}")
            
            # Raw resume text (expandable)
            with st.expander("📄 View Raw Resume Text"):
                st.text_area("Resume Content", resume_text, height=300)
            
            # Download results
            st.header("📥 Export Results")
            
            # Create summary data for download
            summary_data = {
                'Candidate_Info': {
                    'File_Name': uploaded_file.name,
                    'Processing_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Overall_Score': scoring_result['score_percentage'],
                    'Recommendation': scoring_result.get('recommendation', ''),
                },
                'Contact_Info': processed_data['contact_info'],
                'Skills': processed_data['skills'],
                'Experience': processed_data['experience'],
                'Education': processed_data['education'],
                'Component_Scores': scoring_result['component_scores'],
                'Job_Requirements': job_requirements
            }
            
            # Convert to DataFrame for download
            results_df = pd.DataFrame([{
                'File_Name': uploaded_file.name,
                'Overall_Score': scoring_result['score_percentage'],
                'Skills_Score': scoring_result['component_scores']['skills_match'] * 100,
                'Experience_Score': scoring_result['component_scores']['experience_years'] * 100,
                'Education_Score': scoring_result['component_scores']['education'] * 100,
                'Quality_Score': scoring_result['component_scores']['resume_quality'] * 100,
                'Total_Experience': processed_data['experience']['total_years'],
                'Education_Level': processed_data['education']['level'],
                'Email': processed_data['contact_info']['email'],
                'Phone': processed_data['contact_info']['phone'],
                'Recommendation': scoring_result.get('recommendation', ''),
                'Processing_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            
            col1, col2 = st.columns(2)
            with col1:
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="📊 Download Results as CSV",
                    data=csv,
                    file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                import json
                json_data = json.dumps(summary_data, indent=2, default=str)
                st.download_button(
                    label="📋 Download Detailed JSON",
                    data=json_data,
                    file_name=f"detailed_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
        except Exception as e:
            st.error(f"❌ Error processing resume: {str(e)}")
            st.write("**Troubleshooting tips:**")
            st.write("1. Ensure the file is a valid PDF or DOCX")
            st.write("2. Check that the file contains readable text")
            st.write("3. Try a different file format")
            st.write("4. Make sure the file is not corrupted")

# Sidebar information
def sidebar_info():
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ About This Tool")
    st.sidebar.info("""
    This AI Resume Screener uses:
    - **NLP** for information extraction
    - **Machine Learning** for intelligent scoring
    - **Multiple criteria** for comprehensive evaluation
    
    **Scoring Components:**
    - Skills Match (40%)
    - Experience (25%)
    - Education (20%)
    - Resume Quality (15%)
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Best Practices")
    st.sidebar.success("""
    **For better results:**
    1. Use clear, readable resume formats
    2. Specify detailed job requirements
    3. Include both required and nice-to-have skills
    4. Set realistic experience expectations
    """)

if __name__ == "__main__":
    sidebar_info()
    main()
