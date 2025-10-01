import spacy
import re
from datetime import datetime
from collections import Counter
import string

class NLPProcessor:
    """Class to handle NLP processing and information extraction from resumes"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy English model not found. Please run: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Predefined skill sets (expand these based on your needs)
        self.tech_skills = {
            'programming': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go',
                'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css',
                'typescript', 'perl', 'shell', 'bash', 'powershell'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'django', 'flask', 'spring', 'nodejs',
                'express', 'laravel', 'rails', 'tensorflow', 'pytorch', 'keras',
                'scikit-learn', 'pandas', 'numpy', 'bootstrap', 'jquery'
            ],
            'tools': [
                'git', 'docker', 'kubernetes', 'jenkins', 'ansible', 'terraform',
                'vagrant', 'maven', 'gradle', 'npm', 'yarn', 'webpack', 'jira',
                'confluence', 'slack', 'trello'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'elasticsearch',
                'sqlite', 'cassandra', 'dynamodb', 'neo4j', 'influxdb'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'heroku', 'digital ocean', 'linode',
                's3', 'ec2', 'lambda', 'cloudformation', 'terraform'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'project management', 'agile', 'scrum', 'kanban', 'analytical',
                'creative', 'innovative', 'collaborative'
            ]
        }
        
    def extract_contact_info(self, text):
        """Extract email, phone, LinkedIn from resume text"""
        contact = {}
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact['email'] = emails[0] if emails else None
        
        # Phone extraction (various formats) - IMPROVED
        phone_patterns = [
            # International with country code
            r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            # US format with parentheses: (123) 456-7890
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            # US format with dots: 123.456.7890
            r'\d{3}\.\d{3}\.\d{4}',
            # US format with dashes: 123-456-7890
            r'\d{3}-\d{3}-\d{4}',
            # Simple 10 digit: 1234567890
            r'\b\d{10}\b',
            # Indian format: +91 12345 67890 or +91-1234567890
            r'\+91[-.\s]?\d{5}[-.\s]?\d{5}',
            r'\+91[-.\s]?\d{10}',
            # General international
            r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                phones.extend(matches)
                break  # Use the first pattern that finds a match
        
        # Clean and format phone numbers
        if phones:
            phone = phones[0]
            if isinstance(phone, tuple):
                phone = ''.join(filter(None, phone))  # Join tuple and filter empty strings
            
            # Remove extra whitespace
            phone = ' '.join(phone.split())
            contact['phone'] = phone.strip()
        else:
            contact['phone'] = None
        
        # LinkedIn extraction - IMPROVED VERSION
        linkedin_urls = []
        
        # Pattern 1: Full URL with http/https
        full_url_pattern = r'https?://(?:www\.)?linkedin\.com/(?:in|pub)/[\w\-]+'
        linkedin_urls.extend(re.findall(full_url_pattern, text, re.IGNORECASE))
        
        # Pattern 2: URL without protocol
        if not linkedin_urls:
            partial_url_pattern = r'(?:www\.)?linkedin\.com/(?:in|pub)/[\w\-]+'
            partial_matches = re.findall(partial_url_pattern, text, re.IGNORECASE)
            if partial_matches:
                # Add https:// prefix if not present
                linkedin_urls = [f"https://{url}" if not url.startswith('http') else url 
                               for url in partial_matches]
        
        # Pattern 3: Just the username part (linkedin.com/in/username)
        if not linkedin_urls:
            username_pattern = r'linkedin\.com/in/([\w\-]+)'
            username_matches = re.findall(username_pattern, text, re.IGNORECASE)
            if username_matches:
                linkedin_urls = [f"https://linkedin.com/in/{username}" 
                               for username in username_matches]
        
        contact['linkedin'] = linkedin_urls[0] if linkedin_urls else None
        
        return contact
    
    def extract_skills(self, text):
        """Extract technical and soft skills using keyword matching"""
        text_lower = text.lower()
        found_skills = {}
        
        for category, skills in self.tech_skills.items():
            found_skills[category] = []
            for skill in skills:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills[category].append(skill)
        
        # Remove empty categories
        found_skills = {k: v for k, v in found_skills.items() if v}
        
        return found_skills
    
    def extract_experience(self, text):
        """Extract work experience details using NLP and regex"""
        experience_data = {
            'total_years': 0,
            'organizations': [],
            'job_titles': [],
            'experience_sections': []
        }
        
        if not self.nlp:
            return self._extract_experience_fallback(text)
        
        doc = self.nlp(text)
        
        # Extract organizations using NER
        organizations = []
        for ent in doc.ents:
            if ent.label_ == "ORG" and len(ent.text.strip()) > 2:
                org = ent.text.strip()
                # Filter out common false positives
                if not any(word in org.lower() for word in ['university', 'college', 'school', 'degree']):
                    organizations.append(org)
        
        experience_data['organizations'] = list(set(organizations))
        
        # Extract years of experience using various patterns
        years_patterns = [
            r'(\d+)[\s\-]*(?:years?|yrs?)[\s\-]*(?:of\s+)?(?:experience|exp)',
            r'(?:experience|exp)[\s\-]*(?:of\s+)?(\d+)[\s\-]*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)',
        ]
        
        years_found = []
        text_lower = text.lower()
        
        for pattern in years_patterns:
            matches = re.findall(pattern, text_lower)
            years_found.extend([int(match) for match in matches if match.isdigit()])
        
        if years_found:
            experience_data['total_years'] = max(years_found)
        
        # If no explicit years mentioned, try to infer from date ranges
        if experience_data['total_years'] == 0:
            experience_data['total_years'] = self._infer_experience_from_dates(text)
        
        return experience_data
    
    def _extract_experience_fallback(self, text):
        """Fallback method when spaCy is not available"""
        experience_data = {
            'total_years': 0,
            'organizations': [],
            'job_titles': [],
            'experience_sections': []
        }
        
        # Simple regex-based experience extraction
        years_pattern = r'(\d+)[\s-]*(?:years?|yrs?)'
        years_matches = re.findall(years_pattern, text.lower())
        
        if years_matches:
            experience_data['total_years'] = max([int(y) for y in years_matches])
        
        return experience_data
    
    def _infer_experience_from_dates(self, text):
        """Try to infer total experience from date ranges in resume"""
        # Look for date patterns like "2020-2023", "Jan 2020 - Dec 2022", etc.
        date_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4})',  # 2020-2023
            r'(\d{4})\s*[-–]\s*(?:present|current)',  # 2020-present
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})\s*[-–]\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})',
        ]
        
        current_year = datetime.now().year
        years_worked = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    start_year = int(match[0])
                    end_year = int(match[1]) if match[1].isdigit() else current_year
                    years_worked.append(end_year - start_year)
        
        return max(years_worked) if years_worked else 0
    
    def extract_education(self, text):
        """Extract education information"""
        education_data = {
            'has_degree': False,
            'level': None,
            'institutions': [],
            'fields': []
        }
        
        text_lower = text.lower()
        
        # Education keywords
        education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'diploma',
            'university', 'college', 'institute', 'school'
        ]
        
        education_data['has_degree'] = any(keyword in text_lower for keyword in education_keywords)
        
        # Degree level detection
        if 'phd' in text_lower or 'ph.d' in text_lower or 'doctorate' in text_lower:
            education_data['level'] = 'PhD'
        elif 'master' in text_lower or 'mba' in text_lower or 'm.s' in text_lower or 'm.a' in text_lower:
            education_data['level'] = 'Masters'
        elif 'bachelor' in text_lower or 'b.s' in text_lower or 'b.a' in text_lower or 'b.tech' in text_lower:
            education_data['level'] = 'Bachelors'
        elif 'associate' in text_lower:
            education_data['level'] = 'Associates'
        
        # Extract institutions using NER if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    org_text = ent.text.lower()
                    if any(edu_word in org_text for edu_word in ['university', 'college', 'institute', 'school']):
                        education_data['institutions'].append(ent.text)
        
        return education_data
    
    def process_resume(self, text):
        """Main processing function that extracts all information"""
        if not text or len(text.strip()) < 50:
            return {
                'contact_info': {'email': None, 'phone': None, 'linkedin': None},
                'skills': {},
                'experience': {'total_years': 0, 'organizations': [], 'job_titles': []},
                'education': {'has_degree': False, 'level': None}
            }
        
        try:
            processed_data = {
                'contact_info': self.extract_contact_info(text),
                'skills': self.extract_skills(text),
                'experience': self.extract_experience(text),
                'education': self.extract_education(text),
                'text_length': len(text),
                'word_count': len(text.split())
            }
            
            return processed_data
            
        except Exception as e:
            print(f"Error processing resume: {str(e)}")
            return {
                'contact_info': {'email': None, 'phone': None, 'linkedin': None},
                'skills': {},
                'experience': {'total_years': 0, 'organizations': [], 'job_titles': []},
                'education': {'has_degree': False, 'level': None}
            }
