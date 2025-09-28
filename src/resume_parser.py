import PyPDF2
import pdfplumber
from docx import Document
import re
import io

class ResumeParser:
    """Class to handle resume parsing from PDF and DOCX files"""
    
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF using pdfplumber for better formatting"""
        text = ""
        try:
            # If it's a file-like object (Streamlit upload), use it directly
            if hasattr(pdf_file, 'read'):
                with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            else:
                # If it's a file path
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
        except Exception as e:
            print(f"Error extracting PDF text: {str(e)}")
            # Fallback to PyPDF2
            try:
                if hasattr(pdf_file, 'read'):
                    pdf_file.seek(0)  # Reset file pointer
                    reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
                else:
                    reader = PyPDF2.PdfReader(pdf_file)
                
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            except Exception as e2:
                print(f"Fallback PDF extraction also failed: {str(e2)}")
                return ""
        
        return text
    
    def extract_text_from_docx(self, docx_file):
        """Extract text from Word document"""
        text = ""
        try:
            if hasattr(docx_file, 'read'):
                # Streamlit uploaded file
                doc = Document(io.BytesIO(docx_file.read()))
            else:
                # File path
                doc = Document(docx_file)
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
                
        except Exception as e:
            print(f"Error extracting DOCX text: {str(e)}")
            return ""
        
        return text
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s@.-]', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def parse_resume(self, uploaded_file):
        """Main parsing function for Streamlit uploaded files"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'pdf':
                text = self.extract_text_from_pdf(uploaded_file)
            elif file_extension in ['docx', 'doc']:
                text = self.extract_text_from_docx(uploaded_file)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            return self.clean_text(text)
            
        except Exception as e:
            print(f"Error parsing resume: {str(e)}")
            return ""