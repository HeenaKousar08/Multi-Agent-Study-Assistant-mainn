from phi.agent import Agent
from phi.model.groq import Groq
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo
import yaml
import os

class StudyAgents:
    def __init__(self, topic, subject_category, knowledge_level, learning_goal, 
                 time_available, learning_style, model_name, provider):
        """
        Initialize the study agents with student context and persona data.
        """
        self.topic, self.subject_category = topic, subject_category
        self.knowledge_level, self.learning_goal = knowledge_level, learning_goal
        self.time_available, self.learning_style = time_available, learning_style
        self.model_name, self.provider = model_name, provider
        
        # Load configuration from YAML
        with open("prompts.yaml", "r") as f:
            data = yaml.safe_load(f)
            self.personas = data.get("personas", {})
            self.style_info = data.get("learning_styles", {}).get(learning_style, {})

    def _get_model(self, temp=0.7):
        """
        Configures the AI model based on the selected provider.
        """
        if self.provider == "groq":
            return Groq(
                id=self.model_name, 
                api_key=os.getenv("GROQ_API_KEY"), 
                temperature=temp
            )
        return OpenAIChat(id=self.model_name, temperature=temp)

    def student_analyzer_agent(self):
        """Assesses the student's background and prerequisites."""
        return Agent(
            model=self._get_model(0.5),
            system_prompt=f"{self.personas.get('student_analyzer')['system_prompt']}\nStyle: {self.style_info.get('description')}"
        )

    def roadmap_creator_agent(self):
        """Generates the step-by-step learning path."""
        return Agent(
            model=self._get_model(0.7),
            system_prompt=self.personas.get('roadmap_creator')['system_prompt']
        )

    def tutor_agent(self):
        """General tutor for conversational learning and concept explanation."""
        return Agent(
            model=self._get_model(0.6),
            system_prompt=f"{self.personas.get('tutor_agent')['system_prompt']}\nLevel: {self.knowledge_level}"
        )

    def quiz_generator_agent(self):
        """
        FIXED: Generates level-based assessments.
        """
        return Agent(
            model=self._get_model(temp=0.5),
            system_prompt=self.personas.get('quiz_generator', {}).get('system_prompt', "")
        )

    def resource_finder_agent(self):
        """Searches the web for relevant learning materials."""
        return Agent(
            model=self._get_model(0.6),
            tools=[DuckDuckGo()],
            system_prompt=self.personas.get('resource_finder')['system_prompt']
        )

    def rag_tutor_agent(self, knowledge_base=None):
        """
        FIXED: Specialized tutor for answering questions based on uploaded documents.
        """
        system_prompt = self.personas.get('tutor_agent', {}).get('system_prompt', "")
        
        agent_config = {
            "model": self._get_model(temp=0.4),
            "system_prompt": f"{system_prompt}\nFocus strictly on providing answers grounded in the uploaded document context."
        }
        
        # Enable RAG features if a knowledge base is passed
        if knowledge_base:
            agent_config["knowledge_base"] = knowledge_base
            agent_config["search_knowledge"] = True
            
        return Agent(**agent_config)