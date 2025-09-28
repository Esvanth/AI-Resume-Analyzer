import math
from collections import Counter

class ResumeScorer:
    """Class to score resumes based on job requirements"""
    
    def __init__(self):
        # Scoring weights (should sum to 1.0)
        self.weights = {
            'skills_match': 0.4,      # 40% weight on skills matching
            'experience_years': 0.25,  # 25% weight on experience
            'education': 0.20,        # 20% weight on education
            'resume_quality': 0.15    # 15% weight on resume quality
        }
        
        # Minimum thresholds for scoring
        self.min_text_length = 100
        self.min_word_count = 20
    
    def score_skills_match(self, resume_skills, required_skills, nice_to_have_skills=None):
        """Score based on skill matching with required and nice-to-have skills"""
        if not required_skills and not nice_to_have_skills:
            return 0.5  # Neutral score if no requirements
        
        # Flatten resume skills into a single list
        resume_skill_list = []
        for category, skills in resume_skills.items():
            resume_skill_list.extend([skill.lower().strip() for skill in skills])
        
        resume_skill_set = set(resume_skill_list)
        
        # Process required skills
        required_skill_list = [skill.lower().strip() for skill in (required_skills or [])]
        required_skill_set = set(required_skill_list)
        
        # Process nice-to-have skills
        nice_to_have_skill_list = [skill.lower().strip() for skill in (nice_to_have_skills or [])]
        nice_to_have_skill_set = set(nice_to_have_skill_list)
        
        # Calculate matches
        required_matches = len(resume_skill_set & required_skill_set)
        nice_to_have_matches = len(resume_skill_set & nice_to_have_skill_set)
        
        # Score calculation
        required_score = 0
        if required_skill_set:
            required_score = required_matches / len(required_skill_set)
        
        nice_to_have_score = 0
        if nice_to_have_skill_set:
            nice_to_have_score = nice_to_have_matches / len(nice_to_have_skill_set)
        
        # Weighted combination (required skills more important)
        if required_skill_set and nice_to_have_skill_set:
            final_score = (required_score * 0.8) + (nice_to_have_score * 0.2)
        elif required_skill_set:
            final_score = required_score
        elif nice_to_have_skill_set:
            final_score = nice_to_have_score
        else:
            final_score = 0.5
        
        return min(final_score, 1.0)
    
    def score_experience(self, years_experience, required_years=0, preferred_years=None):
        """Score based on years of experience with required and preferred thresholds"""
        if years_experience < 0:
            return 0.0
        
        # If no experience requirements, give neutral score
        if required_years == 0 and not preferred_years:
            return 0.5
        
        # Score based on meeting requirements
        if years_experience >= required_years:
            base_score = 0.7  # Base score for meeting requirements
            
            # Bonus for exceeding requirements
            if preferred_years and years_experience >= preferred_years:
                base_score = 1.0
            elif years_experience > required_years:
                # Diminishing returns for extra experience
                excess = years_experience - required_years
                bonus = min(0.3, excess * 0.05)  # Max 0.3 bonus
                base_score = min(1.0, base_score + bonus)
            
            return base_score
        else:
            # Penalty for not meeting requirements
            if required_years > 0:
                return years_experience / required_years * 0.6  # Max 60% if below requirements
            else:
                return 0.5
    
    def score_education(self, education_info, required_level=None, preferred_level=None):
        """Score based on education level"""
        if not education_info.get('has_degree', False):
            if required_level:
                return 0.2  # Low score if degree required but not found
            else:
                return 0.6  # Neutral-low if no degree required
        
        # Education level hierarchy
        education_hierarchy = {
            'Associates': 1,
            'Bachelors': 2,
            'Masters': 3,
            'MBA': 3,
            'PhD': 4
        }
        
        current_level = education_info.get('level')
        if not current_level:
            return 0.5  # Neutral if degree detected but level unclear
        
        current_score = education_hierarchy.get(current_level, 1)
        
        # If no requirements specified, score based on level
        if not required_level and not preferred_level:
            return min(current_score / 4.0, 1.0)  # Normalize to 0-1
        
        required_score = education_hierarchy.get(required_level, 0) if required_level else 0
        preferred_score = education_hierarchy.get(preferred_level, 0) if preferred_level else 0
        
        # Score based on meeting requirements
        if current_score >= required_score:
            base_score = 0.7
            if preferred_score and current_score >= preferred_score:
                base_score = 1.0
            elif current_score > required_score:
                bonus = min(0.3, (current_score - required_score) * 0.15)
                base_score = min(1.0, base_score + bonus)
            return base_score
        else:
            # Penalty for not meeting education requirements
            return current_score / max(required_score, 1) * 0.6
    
    def score_resume_quality(self, processed_data):
        """Score overall resume quality and completeness"""
        quality_score = 0.0
        
        # Check text length and word count
        text_length = processed_data.get('text_length', 0)
        word_count = processed_data.get('word_count', 0)
        
        if text_length < self.min_text_length or word_count < self.min_word_count:
            return 0.1  # Very low score for insufficient content
        
        # Contact information completeness
        contact = processed_data.get('contact_info', {})
        if contact.get('email'):
            quality_score += 0.25
        if contact.get('phone'):
            quality_score += 0.15
        if contact.get('linkedin'):
            quality_score += 0.10
        
        # Skills section presence and diversity
        skills = processed_data.get('skills', {})
        total_skills = sum(len(skill_list) for skill_list in skills.values())
        
        if total_skills > 0:
            quality_score += 0.15
            # Bonus for skill diversity
            if len(skills) > 2:  # Multiple skill categories
                quality_score += 0.10
        
        # Experience information
        experience = processed_data.get('experience', {})
        if experience.get('total_years', 0) > 0:
            quality_score += 0.15
        
        if experience.get('organizations'):
            quality_score += 0.10
        
        return min(quality_score, 1.0)
    
    def calculate_overall_score(self, processed_data, job_requirements=None):
        """Calculate final weighted score with detailed breakdown"""
        if not processed_data:
            return self._empty_score_result()
        
        job_requirements = job_requirements or {}
        
        # Calculate individual component scores
        skills_score = self.score_skills_match(
            processed_data.get('skills', {}),
            job_requirements.get('required_skills', []),
            job_requirements.get('nice_to_have_skills', [])
        )
        
        experience_score = self.score_experience(
            processed_data.get('experience', {}).get('total_years', 0),
            job_requirements.get('min_experience', 0),
            job_requirements.get('preferred_experience')
        )
        
        education_score = self.score_education(
            processed_data.get('education', {}),
            job_requirements.get('education_level'),
            job_requirements.get('preferred_education_level')
        )
        
        quality_score = self.score_resume_quality(processed_data)
        
        # Store component scores
        component_scores = {
            'skills_match': skills_score,
            'experience_years': experience_score,
            'education': education_score,
            'resume_quality': quality_score
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            component_scores[component] * weight
            for component, weight in self.weights.items()
        )
        
        # Generate detailed feedback
        feedback = self._generate_feedback(component_scores, processed_data, job_requirements)
        
        return {
            'overall_score': overall_score,
            'component_scores': component_scores,
            'score_percentage': round(overall_score * 100, 1),
            'feedback': feedback,
            'recommendation': self._get_recommendation(overall_score)
        }
    
    def _generate_feedback(self, component_scores, processed_data, job_requirements):
        """Generate detailed feedback for each component"""
        feedback = {}
        
        # Skills feedback
        skills_score = component_scores['skills_match']
        if skills_score < 0.5:
            feedback['skills'] = "Consider adding more relevant technical skills mentioned in the job description."
        elif skills_score < 0.8:
            feedback['skills'] = "Good skill match, but could be improved by learning additional required skills."
        else:
            feedback['skills'] = "Excellent skill match with job requirements."
        
        # Experience feedback
        exp_score = component_scores['experience_years']
        years = processed_data.get('experience', {}).get('total_years', 0)
        required = job_requirements.get('min_experience', 0)
        
        if exp_score < 0.5:
            feedback['experience'] = f"Experience ({years} years) is below the required {required} years."
        elif exp_score < 0.8:
            feedback['experience'] = f"Experience ({years} years) meets basic requirements."
        else:
            feedback['experience'] = f"Excellent experience level ({years} years) for this role."
        
        # Education feedback
        edu_score = component_scores['education']
        edu_level = processed_data.get('education', {}).get('level', 'None')
        
        if edu_score < 0.5:
            feedback['education'] = f"Education level ({edu_level}) may not meet job requirements."
        else:
            feedback['education'] = f"Education level ({edu_level}) is appropriate for this role."
        
        # Quality feedback
        quality_score = component_scores['resume_quality']
        if quality_score < 0.5:
            feedback['quality'] = "Resume could be improved with more complete contact information and better formatting."
        elif quality_score < 0.8:
            feedback['quality'] = "Resume quality is good but could be enhanced."
        else:
            feedback['quality'] = "Excellent resume quality and completeness."
        
        return feedback
    
    def _get_recommendation(self, overall_score):
        """Get hiring recommendation based on overall score"""
        if overall_score >= 0.8:
            return "Strong Candidate - Recommend for Interview"
        elif overall_score >= 0.6:
            return "Good Candidate - Consider for Interview"
        elif overall_score >= 0.4:
            return "Moderate Candidate - Review Carefully"
        else:
            return "Weak Candidate - Consider Rejection"
    
    def _empty_score_result(self):
        """Return empty score result for error cases"""
        return {
            'overall_score': 0.0,
            'component_scores': {
                'skills_match': 0.0,
                'experience_years': 0.0,
                'education': 0.0,
                'resume_quality': 0.0
            },
            'score_percentage': 0.0,
            'feedback': {'error': 'Could not process resume'},
            'recommendation': 'Unable to Evaluate'
        }