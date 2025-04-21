# postprocess.py
import os
import json
from openai import OpenAI
import re

gemini_client = OpenAI(
    api_key="AIzaSyAgWCLeLKK4YRVAqjOqE15uxGwXRPcswDM",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def clean_abbr_with_llm(abbr_map: dict[str, str]) -> dict[str, str]:
    """
    Send the raw abbreviation map to the LLM and get back a cleaned JSON map.
    The model is instructed to output ONLY the JSON mapping codes→full-form.
    """
    # Build the user prompt
    prompt = f"""
I have the following raw plumbing abbreviations mapping (with some entries
missing or containing extra bleed‑through text). Please correct each code to
its proper full form. Return ONLY a JSON object mapping each code to its
clean full phrase, with no extra commentary.

Raw map:
```json
{json.dumps(abbr_map, indent=2)}
The canonical plumbing abbreviations you should include (even if blank above) are: CFS, CHWP, CHWR, CHWS, CWP, CWR, CWS, DN, ET, FCU, HUH, HHWR, HHWS, HX, MAU, VAV. 
"""

    resp = gemini_client.chat.completions.create(model="gemini-2.0-flash", messages=[
        {"role": "system", "content": "You are a helpful assistant that cleans plumbing abbreviation dictionaries."}, {"role": "user", "content": prompt}], temperature=0)

    # The assistant’s content should be just the JSON
    content = resp.choices[0].message.content.strip()
    
    # Remove ```json and ``` markers
    if content.startswith("```"):
        # Remove leading ```json\n or ```
        content = re.sub(r"^```(?:json)?\s*\n", "", content)
        # Remove trailing ```
        content = re.sub(r"\n```$", "", content)

    try:
        cleaned = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"LLM output not valid JSON:\n{content}")
    print("cleaned abbr map: ", cleaned)
    return cleaned
