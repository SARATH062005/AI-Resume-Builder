import requests
import json
import logging

logger = logging.getLogger()

def get_targeted_ai_suggestion(api_key, job_role, resume_data, target_field, job_context=None):
    """Gets a targeted AI suggestion for a single field, using the rest of the resume as context."""
    logger.info(f"Requesting targeted AI suggestion for field: '{target_field}'.")
    if not api_key:
        return "Error: API key is not set."

    # *** MODIFICATION: Add logic for the 'skills' target_field ***
    if target_field == "summary":
        task_instruction = "Generate a concise and impactful professional summary (2-4 sentences)."
    elif target_field == "skills":
        task_instruction = "Generate a comma-separated list of key technical and soft skills relevant to the target job."
    elif target_field == "experience_description" and job_context:
        task_instruction = (f"Rewrite the work experience description for the role of '{job_context.get('title')}' "
                            f"at '{job_context.get('company')}'. Focus on quantifiable achievements and use professional, action-oriented bullet points.")
    else:
        return f"Error: Invalid target field '{target_field}' for AI suggestion."

    prompt = f"""
    You are an expert resume writer. Based on the full resume data provided below and for the target job role of "{job_role}", perform the following task:

    TASK:
    {task_instruction}

    FULL RESUME DATA (for context):
    {json.dumps(resume_data, indent=2)}

    INSTRUCTIONS:
    - Your response must be ONLY the generated text for the requested field.
    - Do NOT include any introductory phrases, explanations, or JSON formatting.
    - For experience descriptions, start each bullet point with '- '.
    """

    try:
        logger.info("Sending targeted request to OpenRouter API...")
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "mistralai/mistral-7b-instruct", "messages": [{"role": "user", "content": prompt}]}
        )
        response.raise_for_status()
        
        raw_response_text = response.text
        logger.info(f"Successfully received response from OpenRouter API. Raw text: {raw_response_text}")

        response_json = response.json()
        
        if 'choices' in response_json and response_json['choices']:
            content = response_json['choices'][0]['message']['content']
            if "```" in content:
                content = content.split("```")[1].strip()
            return content.strip()
        else:
            error_message = response_json.get('error', {}).get('message', 'The AI did not return any content.')
            logger.error(f"API response did not contain valid 'choices'. Full response: {raw_response_text}")
            return f"Error: {error_message}"

    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to OpenRouter API: {e}", exc_info=True)
        return f"Error connecting to OpenRouter API: {e}"
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from API response. Raw text was: {raw_response_text}")
        return f"Error: API returned invalid JSON. See logs for the raw response."
    except Exception as e:
        logger.error(f"An unexpected error occurred processing the API response: {e}", exc_info=True)
        return "An unexpected error occurred. Check the application logs."


def get_ats_score_and_feedback(api_key, job_description, resume_data):
    """
    Asks the AI to act as an ATS, scoring the resume against a job description.
    Returns a structured JSON string with the score, strengths, and weaknesses.
    """
    logger.info("Requesting ATS score and feedback from AI.")
    if not api_key:
        return "Error: API key is not set."

    resume_data_copy = resume_data.copy()
    if 'name' in resume_data_copy: resume_data_copy['name'] = "Candidate"
    if 'email' in resume_data_copy: resume_data_copy['email'] = "[REDACTED]"
    if 'phone' in resume_data_copy: resume_data_copy['phone'] = "[REDACTED]"
    
    prompt = f"""
    You are a professional hiring manager and an expert Applicant Tracking System (ATS) simulator. Your task is to analyze the provided resume against the given job description.

    JOB DESCRIPTION:
    ---
    {job_description}
    ---

    CANDIDATE'S RESUME DATA:
    ---
    {json.dumps(resume_data_copy, indent=2)}
    ---

    INSTRUCTIONS:
    1.  **Analyze Keywords:** Compare the skills, technologies, and responsibilities in the resume with those in the job description.
    2.  **Assess Relevance:** Evaluate how well the candidate's experience aligns with the job requirements.
    3.  **Provide a Score:** Give an overall ATS match score out of 100.
    4.  **Give Feedback:** Detail the strengths and weaknesses of the resume for this specific role.
    5.  **Suggest Keywords:** List critical keywords from the job description that are missing from the resume.
    
    Your response MUST be a valid JSON object and nothing else, following this exact structure:
    {{
      "score": <integer>,
      "match_summary": "<string>",
      "strengths": ["<string>", "<string>", ...],
      "weaknesses": ["<string>", "<string>", ...],
      "keyword_suggestions": ["<string>", "<string>", ...]
    }}
    """

    try:
        logger.info("Sending ATS check request to OpenRouter API...")
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "mistralai/mistral-7b-instruct", "messages": [{"role": "user", "content": prompt}]}
        )
        response.raise_for_status()
        
        raw_response_text = response.text
        logger.info(f"Successfully received ATS response from OpenRouter API.")

        return raw_response_text

    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to OpenRouter API: {e}", exc_info=True)
        return json.dumps({"error": f"Error connecting to API: {e}"})
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return json.dumps({"error": "An unexpected error occurred. Check logs."})