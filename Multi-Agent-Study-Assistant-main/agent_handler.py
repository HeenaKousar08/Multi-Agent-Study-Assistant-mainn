import yaml
import streamlit as st
import os
from study_agents import StudyAgents
from typing import Optional, Dict, Any

class StudyAssistantHandler:
    def __init__(self, topic, subject_category, knowledge_level, learning_goal, 
                 time_available, learning_style, model_name="gpt-4o", provider="openai"):
        """
        Initialize the study assistant handler with robust environment checks.
        """
        self.topic = topic
        self.subject_category = subject_category
        self.knowledge_level = knowledge_level
        self.learning_goal = learning_goal
        self.time_available = time_available
        self.learning_style = learning_style
        self.model_name = model_name
        self.provider = provider
        
        # Ensure API Key is available in environment for agents
        if not os.getenv("GROQ_API_KEY") and provider == "groq":
            st.error("❌ GROQ_API_KEY not found. Please check your .env file.")
            
        self.agents = StudyAgents(
            topic, subject_category, knowledge_level, learning_goal,
            time_available, learning_style, model_name, provider
        )
        self.config = self._load_config()
        self.rag_helper = None
    
    def _load_config(self):
        """Load configuration from YAML."""
        with open("prompts.yaml", "r") as file:
            return yaml.safe_load(file)
    
    def _format_prompt(self, prompt_template, **kwargs):
        """Helper to inject variables into YAML templates."""
        return prompt_template.format(**kwargs)
    
    def analyze_student(self):
        """Creates the initial student profile."""
        results = {}
        with st.status("🧠 Analyzing your learning profile...", expanded=False) as status:
            analyzer = self.agents.student_analyzer_agent()
            prompt = self._format_prompt(
                self.config["prompts"]["student_analysis"]["base"],
                topic=self.topic,
                subject_category=self.subject_category,
                knowledge_level=self.knowledge_level,
                learning_goal=self.learning_goal,
                time_available=self.time_available,
                learning_style=self.learning_style
            )
            
            resp = analyzer.run(prompt, stream=False)
            results["analysis"] = resp.content
            status.update(label="Analysis complete!", state="complete")
        return results
    
    def create_roadmap(self, student_analysis: str):
        """Creates the detailed roadmap using analysis data."""
        results = {}
        with st.status("🗺️ Designing your personalized roadmap...", expanded=False) as status:
            creator = self.agents.roadmap_creator_agent()
            prompt = self._format_prompt(
                self.config["prompts"]["roadmap_creation"]["base"],
                student_analysis=student_analysis,
                topic=self.topic,
                learning_goal=self.learning_goal,
                time_available=self.time_available,
                knowledge_level=self.knowledge_level
            )
            
            resp = creator.run(prompt, stream=False)
            results["roadmap"] = resp.content
            status.update(label="Roadmap finalized!", state="complete")
        return results
    
    def generate_quiz(self, difficulty_level: str, focus_areas: str = "general", num_questions: int = 5):
        """
        CRITICAL: Generates tests specifically filtered by the student's current level.
        """
        results = {}
        generator = self.agents.quiz_generator_agent()
        prompt = self._format_prompt(
            self.config["prompts"]["quiz_generation"]["base"],
            topic=self.topic,
            difficulty_level=difficulty_level,
            focus_areas=focus_areas,
            num_questions=num_questions
        )
        
        resp = generator.run(prompt, stream=False)
        results["quiz"] = resp.content
        return results
    
    def get_tutoring(self, student_question: str, context: str = ""):
        """Fixed Tutor Chat logic to be concise and supportive."""
        tutor = self.agents.tutor_agent()
        prompt = self._format_prompt(
            self.config["prompts"]["tutoring"]["base"],
            student_question=student_question,
            context=context,
            knowledge_level=self.knowledge_level
        )
        
        resp = tutor.run(prompt, stream=False)
        return resp.content

    def query_documents(self, question: str):
        """Fixed RAG querying to ensure context is correctly passed."""
        if not self.rag_helper:
            return "No documents uploaded. Please use the RAG Docs tab to upload a PDF first."
        
        # Retrieve context from vector store
        relevant_context = self.rag_helper.query(question, k=4)
        context_str = "\n\n".join(relevant_context)
        
        # Synthesize answer using RAG tutor
        rag_tutor = self.agents.rag_tutor_agent()
        prompt = self._format_prompt(
            self.config["prompts"]["rag_query"]["base"],
            question=question,
            context=context_str
        )
        
        resp = rag_tutor.run(prompt, stream=False)
        return resp.content

    def add_document_to_rag(self, file_path: str, file_type: str = "pdf") -> bool:
        """Connects to RAGHelper to index files."""
        # This assumes you have a RAGHelper class defined in rag_helper.py
        from rag_helper import RAGHelper
        if not self.rag_helper:
            self.rag_helper = RAGHelper()
            
        if file_type == "pdf":
            return self.rag_helper.load_pdf(file_path)
        return self.rag_helper.load_text(file_path)