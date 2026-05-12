"""
AI service for interacting with Vertex AI (Gemini).
Handles RAG-based question answering with IDEAM enterprise architecture context.
"""
import logging
from google import genai
from google.genai.types import GenerateContentConfig
from app.config import GCP_PROJECT_ID, VERTEX_LOCATION, VERTEX_MODEL
from app.prompts.system_prompt import SYSTEM_PROMPT, CONTEXT_TEMPLATE
from app.knowledge_service import build_context_for_query

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy initialization of the GenAI client."""
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=VERTEX_LOCATION,
        )
    return _client


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
        client = _get_client()
        response = client.models.generate_content(
            model=VERTEX_MODEL,
            contents=full_prompt,
            config=GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=2048,
                temperature=0.3,
                top_p=0.8,
                top_k=40,
            ),
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
