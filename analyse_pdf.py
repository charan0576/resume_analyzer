import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

configuration = {
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain"
}

model = genai.GenerativeModel(
    model_name="models/gemini-3-flash-preview",
    generation_config=configuration
)


def analyse_resume_gemini(resume_content, job_description):
    prompt = f"""
You are a professional resume analyzer and resume writer.

Resume:
{resume_content}

Job Description:
{job_description}

Tasks:
- Analyze the resume against the job description
- Give an ATS match score out of 100
- Identify missing skills
- Suggest improvements
- Rewrite the resume in a professional, ATS-optimized format

Return the result in EXACTLY this format:

Match Score: XX/100

Missing Skills:
- ...

Suggestions:
- ...

Summary:
- ...

<<<START_UPDATED_RESUME>>>
(full rewritten ATS-optimized resume text)
<<<END_UPDATED_RESUME>>>
"""

    response = model.generate_content(prompt)
    text = response.text.strip()

    # ✅ Extract match score
    score_match = re.search(r"Match Score:\s*(\d{1,3})/100", text)
    score = int(score_match.group(1)) if score_match else 0

    # ✅ Extract updated resume
    updated_resume_match = re.search(
        r"<<<START_UPDATED_RESUME>>>(.*?)<<<END_UPDATED_RESUME>>>",
        text,
        re.DOTALL
    )

    updated_resume = (
        updated_resume_match.group(1).strip()
        if updated_resume_match
        else "Updated resume could not be generated."
    )

    # ✅ CLEAN updated resume (remove # and *)
    updated_resume = updated_resume.replace("#", "").replace("*", "")

    # ✅ Remove updated resume section from analysis text
    clean_result = re.sub(
        r"<<<START_UPDATED_RESUME>>>.*?<<<END_UPDATED_RESUME>>>",
        "",
        text,
        flags=re.DOTALL
    ).strip()

    return {
        "score": score,
        "result": clean_result,
        "updated_resume": updated_resume
    }
