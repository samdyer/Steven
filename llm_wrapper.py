import logging
from google import genai
from google.genai import errors

# Configure basic logging for fallback events
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMWrapper:
    """
    A wrapper for Google's GenAI models.
    Routes requests to Gemma 4 as the primary model,
    with an automatic fallback to Gemini 2.5 Flash on failure.
    """
    def __init__(self, api_key: str = None):
        # Initialize the official google-genai client
        # If api_key is None, it will automatically look for the GEMINI_API_KEY environment variable
        self.client = genai.Client(api_key=api_key)
        
        # Official model IDs based on Google AI documentation
        self.primary_model = "gemma-4-31b-it"
        self.fallback_model = "gemini-2.5-flash"

    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generates content using the primary model, falling back to the secondary model if an API error occurs.
        """
        try:
            # Attempt to use the primary Gemma 4 model
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt,
                **kwargs
            )
            return response.text

        except errors.APIError as e:
            # Log the failure of the primary model
            logger.warning(
                f"Primary model ({self.primary_model}) failed with APIError code {e.code}: {e.message}. "
                f"Falling back to {self.fallback_model}."
            )
            
            # Fallback to the stable Gemini 2.5 Flash model
            try:
                fallback_response = self.client.models.generate_content(
                    model=self.fallback_model,
                    contents=prompt,
                    **kwargs
                )
                return fallback_response.text
            except errors.APIError as fallback_error:
                logger.error(
                    f"Fallback model ({self.fallback_model}) also failed with APIError code {fallback_error.code}: {fallback_error.message}."
                )
                raise fallback_error
        except Exception as e:
            # Catch any other unexpected exceptions (e.g., network issues)
            logger.error(f"An unexpected error occurred: {str(e)}")
            raise e

# Example usage:
if __name__ == "__main__":
    # Ensure you have the GEMINI_API_KEY environment variable set
    wrapper = LLMWrapper()
    
    prompt = "Explain the importance of fallback mechanisms in AI applications."
    try:
        result = wrapper.generate_content(prompt)
        print("\n--- Generated Content ---")
        print(result)
    except Exception as e:
        print(f"Failed to generate content: {e}")
