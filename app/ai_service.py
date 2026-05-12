"""
AI service for interacting with Vertex AI (Gemini).
Handles RAG-based question answering with IDEAM enterprise architecture context.
"""
import logging
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, Part
from app.config import GCP_PROJECT_ID, VERTEX_LOCATION, VERTEX_MODEL
from app.prompts.system_prompt import SYSTEM_PROMPT, CONTEXT_TEMPLATE
from app.knowledge_service import build_context_for_query

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy initialization of the Gemini model."""
    global _model
    if _model is None:
        aiplatform.init(project=GCP_PROJECT_ID, location=VERTEX_LOCATION)
        _model = GenerativeModel(
            VERTEX_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
    return _model


def generate_response(user_message: str) -> str:
    """
    Generate a response using Gemini with RAG context from Firestore.

    1. Searches Firestore for relevant context
    2. Builds a contextual prompt
    3. Sends to Gemini for response generation
    """
    try:
        # Step 1: Retrieve context from knowledge base
        context = build_context_for_query(user_message)
        logger.info(f"Retrieved context length: {len(context)} chars")

        # Step 2: Build the full prompt with context
        full_prompt = CONTEXT_TEMPLATE.format(
            context=context,
            question=user_message,
        )

        # Step 3: Generate response with Gemini
        model = _get_model()
        response = model.generate_content(
            full_prompt,
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 40,
            },
        )

        if response and response.text:
            return response.text
        else:
            return (
                "⚠️ No pude generar una respuesta. "
                "Por favor, intenta reformular tu pregunta."
            )

    except Exception as e:
        logger.error(f"Error generating AI response: {e}", exc_info=True)
        return (
            "❌ Ocurrió un error al procesar tu consulta. "
            "Por favor, intenta de nuevo en unos momentos."
        )
