import streamlit as st
import requests
import json
import time
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch

# Page configuration
st.set_page_config(
    page_title="AI PDF Document Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Get API tokens from Streamlit secrets
def get_api_tokens():
    try:
        groq_token = st.secrets.get("GROQ_TOKEN", "")
        hf_token = st.secrets.get("HF_TOKEN", "")
        return groq_token, hf_token
    except Exception as e:
        st.warning("⚠️ No secrets configured. Using template mode only.")
        return "", ""

GROQ_API_TOKEN, HF_API_TOKEN = get_api_tokens()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    
    .document-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .preview-box {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1.5rem;
        margin: 1rem 0;
        max-height: 400px;
        overflow-y: auto;
        white-space: pre-wrap;
        font-family: 'Courier New', monospace;
    }
    
    .api-status {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    
    .api-connected {
        background: #d4edda;
        color: #155724;
    }
    
    .api-disconnected {
        background: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Custom title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor='#333333'
        ))
        
        # Custom body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0
        ))
        
        # Custom header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=18,
            spaceBefore=18,
            alignment=TA_LEFT,
            textColor='#444444'
        ))
    
    def clean_text_for_pdf(self, text):
        """Clean text for PDF generation"""
        # Remove problematic characters and format
        text = text.replace('\u2019', "'")  # Right single quotation mark
        text = text.replace('\u201c', '"')  # Left double quotation mark
        text = text.replace('\u201d', '"')  # Right double quotation mark
        text = text.replace('\u2013', '-')  # En dash
        text = text.replace('\u2014', '-')  # Em dash
        return text
    
    def create_pdf(self, content, document_type="Document"):
        """Create PDF from content"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # Add title
            title = Paragraph(self.clean_text_for_pdf(document_type), self.styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Clean and split content
            content = self.clean_text_for_pdf(content)
            paragraphs = content.split('\n\n')
            
            for para in paragraphs:
                if para.strip():
                    # Check if it looks like a heading (short and might be all caps)
                    if len(para.strip()) < 80 and (para.strip().isupper() or para.strip().endswith(':')):
                        p = Paragraph(para.strip(), self.styles['CustomHeader'])
                    else:
                        p = Paragraph(para.strip(), self.styles['CustomBody'])
                    story.append(p)
                    story.append(Spacer(1, 12))
            
            # Add footer
            footer = Paragraph(
                f"Generated on {datetime.now().strftime('%B %d, %Y')} using AI PDF Generator",
                self.styles['Normal']
            )
            story.append(Spacer(1, 30))
            story.append(footer)
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            st.error(f"PDF Generation Error: {str(e)}")
            return None

class AIClient:
    def __init__(self):
        self.pdf_generator = PDFGenerator()
    
    def test_groq_connection(self):
        """Test Groq API connection"""
        if not GROQ_API_TOKEN:
            return False, "No API token"
        
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple request
            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=10)
            return response.status_code == 200, f"Status: {response.status_code}"
            
        except Exception as e:
            return False, str(e)
    
    def generate_with_groq(self, prompt, document_type):
        """Generate content using Groq API"""
        if not GROQ_API_TOKEN:
            return "Error: No Groq API token configured. Please add GROQ_TOKEN to Streamlit secrets."
        
        try:
            system_prompts = {
                "cover_letter": "You are a professional career advisor. Write a compelling, well-structured cover letter based on the provided information. Use proper business letter format with clear paragraphs, professional tone, and highlight relevant skills and experience. Make it engaging and tailored to the role.",
                
                "resume": "You are a professional resume writer. Create a comprehensive, well-structured resume based on the provided information. Include sections like Professional Summary, Work Experience (with bullet points of achievements), Education, Skills, and any other relevant sections. Use clear formatting and professional language.",
                
                "proposal": "You are a business proposal writer. Create a comprehensive business proposal based on the provided information. Include sections like Executive Summary, Problem Statement, Proposed Solution, Implementation Plan, Timeline, Budget Considerations, and Expected Outcomes. Make it professional and persuasive.",
                
                "letter": "You are a professional letter writer. Create a formal, well-structured letter based on the provided information. Use proper business letter format with appropriate greeting, body paragraphs, and closing. Maintain a professional and respectful tone throughout.",
                
                "document": "You are a professional document writer. Create a well-structured, professional document based on the provided information. Organize the content logically with clear headings and paragraphs."
            }
            
            system_prompt = system_prompts.get(document_type.lower(), system_prompts["document"])
            
            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please create a professional {document_type} based on the following requirements:\n\n{prompt}"}
                ],
                "max_tokens": 1500,
                "temperature": 0.7,
                "top_p": 1,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {GROQ_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content'].strip()
                else:
                    return "Error: Invalid response format from API"
            else:
                error_msg = f"API Error {response.status_code}"
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg += f": {error_detail['error'].get('message', 'Unknown error')}"
                except:
                    error_msg += f": {response.text}"
                return f"Error: {error_msg}"
                
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return "Error: Connection failed. Please check your internet connection."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_with_template(self, prompt, document_type):
        """Generate content using templates (fallback when no API)"""
        
        templates = {
            "cover_letter": """Dear Hiring Manager,

I am writing to express my strong interest in the position you have available. Based on the information provided:

{prompt}

I am confident that my background and skills make me an excellent candidate for this role. My experience includes:

• Strong analytical and problem-solving abilities
• Excellent written and verbal communication skills
• Proven track record of working effectively in team environments
• Adaptability and eagerness to learn new technologies and methodologies

I am excited about the opportunity to contribute to your organization and would welcome the chance to discuss how my qualifications align with your needs. I am available for an interview at your convenience and look forward to hearing from you.

Thank you for your time and consideration.

Sincerely,
[Your Name]""",

            "resume": """[YOUR NAME]
[Your Email Address] | [Your Phone Number] | [Your City, State]
[LinkedIn Profile] | [Portfolio/Website]

PROFESSIONAL SUMMARY
Experienced professional with a strong background in the requirements outlined: {prompt}

CORE COMPETENCIES
• Technical Skills: [Based on your background]
• Leadership & Team Management
• Project Management
• Problem Solving & Analysis
• Communication & Collaboration

PROFESSIONAL EXPERIENCE

[MOST RECENT POSITION] | [Company Name] | [Dates]
• Led projects and initiatives resulting in improved efficiency
• Collaborated with cross-functional teams to achieve organizational goals  
• Implemented solutions that enhanced operational effectiveness
• Demonstrated expertise in relevant technologies and methodologies

[PREVIOUS POSITION] | [Company Name] | [Dates]
• Contributed to key projects and strategic initiatives
• Developed and maintained professional relationships with stakeholders
• Applied technical skills to solve complex business challenges

EDUCATION
[Degree] in [Field] | [University Name] | [Year]

CERTIFICATIONS & ADDITIONAL QUALIFICATIONS
[Relevant certifications based on your field]""",

            "proposal": """BUSINESS PROPOSAL

EXECUTIVE SUMMARY
This proposal outlines a comprehensive solution to address the requirements specified: {prompt}

PROBLEM STATEMENT
Based on the current situation and needs identified, there are opportunities for improvement that can be addressed through strategic planning and implementation.

PROPOSED SOLUTION
Our recommended approach includes:
• Thorough analysis of current processes and systems
• Development of customized solutions tailored to specific requirements
• Implementation of best practices and industry standards
• Ongoing support and optimization

IMPLEMENTATION PLAN
Phase 1: Assessment and Planning (Weeks 1-2)
• Detailed requirements gathering
• Stakeholder interviews and analysis
• Solution design and documentation

Phase 2: Development and Testing (Weeks 3-6)
• Solution development and configuration
• Quality assurance and testing procedures
• User training materials preparation

Phase 3: Deployment and Support (Weeks 7-8)
• System deployment and go-live support
• User training and knowledge transfer
• Post-implementation support and optimization

EXPECTED OUTCOMES
• Improved efficiency and productivity
• Enhanced user experience and satisfaction
• Measurable return on investment
• Scalable solution for future growth

BUDGET CONSIDERATIONS
Investment required will be commensurate with the scope and complexity of the solution, with flexible options to meet budget requirements.

CONCLUSION
We are committed to delivering a solution that meets your specific needs and exceeds expectations. We look forward to the opportunity to discuss this proposal in detail.""",

            "letter": """[Date]

[Recipient Name]
[Recipient Title]
[Company/Organization Name]
[Address]

Dear [Recipient Name/Title],

I hope this letter finds you well. I am writing to address the matter outlined below:

{prompt}

I believe this correspondence will help clarify the situation and provide the necessary information for your consideration. Please find the relevant details and context provided above.

I would appreciate your attention to this matter and look forward to your response. Should you require any additional information or clarification, please do not hesitate to contact me.

Thank you for your time and consideration of this request.

Sincerely,

[Your Name]
[Your Title]
[Your Contact Information]""",

            "document": """PROFESSIONAL DOCUMENT

OVERVIEW
This document has been prepared to address the requirements and specifications outlined in your request: {prompt}

MAIN CONTENT
Based on the information provided, this document covers the key areas of focus and provides comprehensive coverage of the relevant topics.

The content has been structured to ensure clarity and accessibility, with logical organization and professional presentation throughout.

KEY POINTS
• Comprehensive coverage of specified requirements
• Professional formatting and presentation
• Clear and concise language appropriate for the intended audience
• Actionable recommendations and next steps where applicable

CONCLUSION
This document provides a solid foundation for moving forward with the outlined objectives and requirements. Please review the content and let me know if any adjustments or additional information are needed.

Thank you for the opportunity to prepare this document."""
        }
        
        base_template = templates.get(document_type.lower(), templates["document"])
        
        # Format the template with the user's prompt
        formatted_content = base_template.format(prompt=prompt)
        
        # Add a note about template mode
        note = f"\n\n---\nNote: This document was generated using template mode. For enhanced AI-generated content, configure an API token in Streamlit secrets."
        
        return formatted_content + note
    
    def generate_content(self, prompt, document_type, use_api=True):
        """Generate content using the best available method"""
        if use_api and GROQ_API_TOKEN:
            result = self.generate_with_groq(prompt, document_type)
            # If API fails, fall back to template
            if result.startswith("Error:"):
                st.warning("API generation failed, falling back to template mode...")
                return self.generate_with_template(prompt, document_type)
            return result
        else:
            return self.generate_with_template(prompt, document_type)

def check_api_status():
    """Check API connection status"""
    status = {}
    
    # Check Groq API
    if GROQ_API_TOKEN:
        try:
            ai_client = AIClient()
            is_working, message = ai_client.test_groq_connection()
            status['groq'] = is_working
            status['groq_message'] = message
        except Exception as e:
            status['groq'] = False
            status['groq_message'] = str(e)
    else:
        status['groq'] = False
        status['groq_message'] = "No token configured"
    
    return status

def main():
    # Initialize AI client
    ai_client = AIClient()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI PDF Document Generator</h1>
        <p>Generate professional documents using AI - Cover Letters, Resumes, Proposals, and More!</p>
        <p style="font-size: 0.9em; opacity: 0.9;">✨ Works with free APIs and template mode!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API status
    api_status = check_api_status()
    
    # Sidebar
    st.sidebar.header("⚙️ Configuration")
    
    # API Status Display
    st.sidebar.subheader("🔌 API Status")
    if api_status.get('groq', False):
        st.sidebar.markdown('<div class="api-status api-connected">✅ Groq API: Connected</div>', unsafe_allow_html=True)
        use_api = st.sidebar.checkbox("Use AI API", value=True, help="Use Groq API for enhanced content generation")
    else:
        st.sidebar.markdown(f'<div class="api-status api-disconnected">❌ AI API: {api_status.get("groq_message", "Not available")}</div>', unsafe_allow_html=True)
        st.sidebar.info("💡 Add GROQ_TOKEN in Streamlit secrets for AI generation")
        use_api = False
    
    # Document type selection
    document_types = {
        "Cover Letter": "cover_letter",
        "Resume": "resume", 
        "Business Proposal": "proposal",
        "Formal Letter": "letter",
        "Custom Document": "document"
    }
    
    selected_doc_type = st.sidebar.selectbox(
        "📋 Document Type",
        list(document_types.keys()),
        help="Select the type of document you want to generate"
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Document Generation")
        
        # Document type info
        doc_descriptions = {
            "Cover Letter": "Generate a professional cover letter tailored to a specific job or company. Include your background, skills, and motivation.",
            "Resume": "Create a comprehensive resume with your professional experience, education, skills, and achievements.",
            "Business Proposal": "Draft a detailed business proposal including executive summary, problem statement, solution, and implementation plan.",
            "Formal Letter": "Write a formal business or personal letter with proper formatting and professional tone.",
            "Custom Document": "Generate any type of professional document based on your specific requirements."
        }
        
        st.markdown(f"""
        <div class="document-card">
            <h4>{selected_doc_type}</h4>
            <p>{doc_descriptions[selected_doc_type]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Prompt input
        prompt_examples = {
            "Cover Letter": "I'm applying for a Senior Software Engineer position at Microsoft. I have 7 years of experience with Python, JavaScript, and cloud technologies (AWS, Azure). I previously worked at two startups where I led development teams and built scalable web applications. I'm passionate about AI/ML and have contributed to open-source projects. I want to emphasize my leadership experience and technical versatility.",
            
            "Resume": "Create a resume for Sarah Johnson, a Marketing Manager with 6 years of experience. Skills include digital marketing, SEO, content strategy, Google Analytics, social media management, and project management. She worked at TechStart Inc (2021-2024) as Marketing Manager, increased website traffic by 150%, managed $500K budget, led team of 4. Previously at Creative Agency (2018-2021) as Marketing Specialist. Education: MBA Marketing from UCLA (2018), BS Business from USC (2016). Certifications: Google Ads, HubSpot Content Marketing.",
            
            "Business Proposal": "Proposal for implementing a comprehensive cybersecurity solution for a mid-size financial services company (200 employees). Current challenges: outdated security infrastructure, increasing cyber threats, regulatory compliance requirements, recent phishing attempts. Proposed solution: next-generation firewall, endpoint detection and response (EDR), employee security training program, 24/7 monitoring service. Expected outcomes: 95% threat detection rate, full compliance with financial regulations, reduced security incidents. Budget: $150K initial investment, $50K annual maintenance. Implementation timeline: 4 months.",
            
            "Formal Letter": "Write a formal complaint letter to the Property Management Company regarding ongoing noise issues in apartment 4B. The tenant in the unit above has been consistently playing loud music and having parties until 2 AM on weeknights for the past month. Previous verbal complaints to the building manager have not resolved the issue. Request immediate action to address the noise violations as outlined in the lease agreement. Mention specific dates of incidents: March 15, 18, 22, and 25. Request written response within 7 business days.",
            
            "Custom Document": "Create a comprehensive project proposal for developing a mobile app for a local restaurant chain. Include market analysis, technical requirements, development timeline, team structure, and budget breakdown..."
        }
        
        prompt = st.text_area(
            "📝 Enter your detailed requirements:",
            height=200,
            placeholder=prompt_examples[selected_doc_type],
            help="Provide comprehensive information about what you want in your document. The more detailed your prompt, the better the generated content will be."
        )
        
        # Action buttons
        col_prev, col_gen = st.columns(2)
        
        with col_prev:
            preview_btn = st.button("🔍 Preview Content", use_container_width=True, disabled=not prompt.strip())
        
        with col_gen:
            generate_btn = st.button("📄 Generate PDF", use_container_width=True, disabled=not prompt.strip(), type="primary")
        
        # Preview functionality
        if preview_btn and prompt.strip():
            with st.spinner('🤖 Generating content preview...'):
                content = ai_client.generate_content(prompt, document_types[selected_doc_type], use_api)
                
                if content.startswith("Error:"):
                    st.markdown(f"""
                    <div class="error-message">
                        <strong>⚠️ Generation Error:</strong><br>{content}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("### 📋 Content Preview")
                    st.markdown(f"""
                    <div class="preview-box">
{content}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show word count
                    word_count = len(content.split())
                    st.info(f"📊 Generated {word_count} words")
        
        # Generate PDF functionality
        if generate_btn and prompt.strip():
            with st.spinner('🔄 Generating PDF document...'):
                # Generate content
                content = ai_client.generate_content(prompt, document_types[selected_doc_type], use_api)
                
                if content.startswith("Error:"):
                    st.markdown(f"""
                    <div class="error-message">
                        <strong>⚠️ Content Generation Error:</strong><br>{content}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Generate PDF
                    pdf_content = ai_client.pdf_generator.create_pdf(content, selected_doc_type)
                    
                    if pdf_content:
                        # Success message
                        st.markdown("""
                        <div class="success-message">
                            <strong>🎉 Success!</strong> Your PDF document has been generated successfully!
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Download button
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{selected_doc_type.replace(' ', '_')}_{timestamp}.pdf"
                        
                        st.download_button(
                            label="📥 Download PDF Document",
                            data=pdf_content,
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        # Show success stats
                        word_count = len(content.split())
                        st.success(f"✅ Generated {word_count} words in PDF format")
                    else:
                        st.error("❌ Failed to generate PDF. Please try again.")
    
    with col2:
        st.header("💡 Setup & Tips")
        
        # Setup instructions
        with st.expander("🚀 Deploy to Streamlit Cloud", expanded=True):
            st.markdown("""
            **Quick Deployment Steps:**
            
            1. **Upload to GitHub:**
               - Create new repository
               - Upload `streamlit_app.py` and `requirements.txt`
            
            2. **Deploy on Streamlit:**
               - Go to [share.streamlit.io](https://share.streamlit.io)
               - Connect GitHub account
               - Select your repository
               - Click "Deploy"
            
            3. **Add API Token (Optional):**
               - Go to app settings → Secrets
               - Add: `GROQ_TOKEN = "your_api_key_here"`
            """)
        
        with st.expander("🆓 Get Free API Access"):
            st.markdown("""
            **Recommended: Groq (Fast & Free)**
            
            1. Visit [console.groq.com](https://console.groq.com)
            2. Sign up with email
            3. Go to API Keys section
            4. Create new API key
            5. Copy the key
            
            **Free Limits:**
            - 1,000 requests per day
            - Very fast responses
            - Multiple AI models available
            """)
        
        # Usage tips
        st.markdown("""
        ### 🎯 Writing Better Prompts
        
        **✅ Do:**
        - Be specific about requirements
        - Include relevant details and context  
        - Mention preferred tone/style
        - Provide background information
        
        **❌ Avoid:**
        - Vague or generic requests
        - Too short descriptions
        - Missing key details
        
        **💡 Pro Tips:**
        - Use the example prompts as templates
        - Include specific names, dates, numbers
        - Mention any special requirements
        - Specify the target audience
        """)
        
        # System status
        st.markdown("### 📊 System Status")
        
        if use_api and api_status.get('groq', False):
            st.success("✅ AI Mode: Enhanced Generation")
        elif GROQ_API_TOKEN and not api_status.get('groq', False):
            st.warning("⚠️ AI Mode: Connection Issues")
        else:
            st.info("ℹ️ Template Mode: Basic Generation")
        
        st.info(f"📄 Document Type: **{selected_doc_type}**")
        
        # Usage statistics
        if 'generation_count' not in st.session_state:
            st.session_state.generation_count = 0
        
        if generate_btn and prompt.strip():
            st.session_state.generation_count += 1
        
        st.metric("📈 Documents Generated", st.session_state.generation_count)

if __name__ == "__main__":
    main()