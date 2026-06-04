import google.generativeai as genai
import json, re

genai.configure(api_key="AIzaSyCxcakvw5doRpzwmpZO5BSLOgPaD9_DubQ")
model = genai.GenerativeModel("models/gemini-2.5-flash")

titles = [
    "They will chase you and beg to be with you",
    "MANIFEST YOUR DREAM RELATIONSHIP OVERNIGHT",
    "Stop TRYING to Manifest Love You Are PUSHING Him Away",
]

titles_text = "\n".join(["- " + t for t in titles])

prompt = f"""Create 2 remix versions for each title below using the 80/20 rule (keep 80% original, change 20%).
Reply ONLY with a JSON array like this:
[{{"original": "title", "remix1": "remix version 1", "remix2": "remix version 2"}}]

Titles:
{titles_text}"""

try:
    response = model.generate_content(prompt)
    text = response.text.strip()
    print("RAW RESPONSE:")
    print(text[:800])
    print()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        data = json.loads(match.group())
        for d in data:
            print("Original:", d.get("original"))
            print("  Remix1:", d.get("remix1"))
            print("  Remix2:", d.get("remix2"))
            print()
    else:
        print("NO JSON FOUND in response")
except Exception as e:
    print(f"ERROR: {e}")
