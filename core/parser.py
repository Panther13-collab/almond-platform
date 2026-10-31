import re
import os
from pypdf import PdfReader
import docx

# Comprehensive Global Tech Taxonomy (200+ Skills across all domains)
CANONICAL_SKILLS = {
    # Programming Languages
    "python", "javascript", "typescript", "go", "golang", "java", "c++", "cpp", "c#", "csharp",
    ".net", "dotnet", "rust", "ruby", "ruby on rails", "php", "laravel", "sql", "r", "swift",
    "kotlin", "scala", "shell", "bash", "dart", "perl", "elixir",

    # Mobile Development
    "flutter", "react native", "swiftui", "objective-c", "android", "ios", "xcode",
    "android studio", "jetpack compose", "bloc", "mobile app development",

    # Web Scraping & Browser Automation
    "web scraping", "playwright", "beautifulsoup", "selenium", "puppeteer", "scrapy",
    "requests", "httpx", "automation", "xpath", "css selectors", "headless browser",
    "proxy rotation", "anti-bot", "cloudflare", "user-agent", "session management",
    "browser automation", "crawling", "data extraction", "data mining",

    # AI, ML & LLMs (Modern GenAI & Agents)
    "ai", "artificial intelligence", "machine learning", "deep learning", "llm",
    "large language models", "gemini", "chatgpt", "openai", "claude", "anthropic",
    "langchain", "langgraph", "llamaindex", "rag", "vector database", "pinecone",
    "weaviate", "chromadb", "agentic ai", "prompt engineering", "nlp", "natural language processing",
    "computer vision", "pytorch", "tensorflow", "keras", "hugging face", "transformers",
    "fine-tuning", "ollama", "local llm", "autonomous agents",

    # Web, Frontend & Frameworks
    "fastapi", "flask", "django", "nodejs", "node.js", "express", "react", "react.js",
    "vue", "vue.js", "angular", "svelte", "nextjs", "next.js", "nuxt", "tailwind",
    "bootstrap", "rest", "rest api", "graphql", "html", "css", "json", "xml",
    "microservices", "grpc", "websocket", "spring boot", "nestjs",

    # Cloud, DevOps & SRE
    "aws", "amazon web services", "amazon s3", "ec2", "lambda", "gcp", "google cloud",
    "azure", "docker", "kubernetes", "k8s", "ci/cd", "ci-cd", "github actions", "gitlab",
    "terraform", "ansible", "helm", "linux", "ubuntu", "git", "bitbucket", "monitoring",
    "grafana", "prometheus", "datadog", "splunk", "elk", "nginx", "devops",

    # Data Engineering & Analytics
    "pandas", "numpy", "scipy", "pyspark", "spark", "hadoop", "databricks", "kafka",
    "airflow", "etl", "elt", "data pipelines", "data cleaning", "dbt", "snowflake",
    "bigquery", "redshift", "data warehouse", "lakehouse", "power bi", "tableau",

    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite", "elasticsearch",
    "cassandra", "dynamodb", "supabase", "firebase",

    # Quality Assurance, Testing & Tools
    "pytest", "unittest", "jest", "cypress", "postman", "qa", "test automation",
    "agile", "scrum", "jira", "figma",

    # Mechanical, Automotive & CAD/CAM/CAE Design
    "catia", "catia v5", "ug nx", "unigraphics", "nx", "solidworks", "creo", "pro/e",
    "autocad", "cad", "cam", "cae", "ansys", "dfmea", "dmdr", "plm", "gd&t", "gdt",
    "plastic trim", "interior trim", "automotive design", "injection molding",
    "tolerance stackup", "tolerance stack up", "tolerance stack-up", "product design",
    "cpm", "master section", "doghouse", "clip tower", "mold parting", "class a surface",
    "trim design", "mechanical design", "mechanical engineering", "sheet metal",
    "tool design", "instrument panel", "cockpit", "bom", "bill of materials"
}

def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    try:
        if ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        elif ext in [".docx", ".doc"]:
            doc = docx.Document(file_path)
            for p in doc.paragraphs:
                text += p.text + "\n"
        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        print(f"[PARSER] Warning: Error parsing {file_path}: {e}")
        return ""
    return text.strip()

def parse_candidate_profile(text: str) -> dict:
    profile = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "years_experience": 0,
        "current_role": "",
        "skills": [],
        "raw_text_length": len(text)
    }

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 1. Email extraction
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        profile["email"] = email_match.group(0)

    # 2. Phone extraction
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4,6}', text)
    if phone_match:
        profile["phone"] = phone_match.group(0).strip()

    # 3. Dynamic Name Extraction
    # Inspect early lines; strip common resume clutter, punctuation, numbers, and URLs
    for l in lines[:5]:
        cleaned = re.sub(r'[\d\+\|@\.:,/#\(\)]', '', l).strip()
        words = cleaned.split()
        lower = cleaned.lower()
        if 2 <= len(words) <= 4 and not any(k in lower for k in ["resume", "curriculum", "vitae", "cv", "page", "developer", "engineer", "experience", "profile"]):
            profile["name"] = cleaned.title()
            break
    if not profile["name"] and lines:
        cleaned_first = re.sub(r'[\d\+\|@\.:,/#\(\)]', '', lines[0]).strip()
        profile["name"] = cleaned_first.title() if cleaned_first else "Candidate"

    # 4. Location extraction (Global / Indian)
    loc_keywords = [
        "salem", "coimbatore", "chennai", "bengaluru", "bangalore", "kochi", "cochin",
        "kerala", "tamil nadu", "karnataka", "hyderabad", "pune", "mumbai", "delhi", "noida",
        "gurgaon", "gurugram", "san francisco", "austin", "new york", "seattle", "london",
        "berlin", "toronto", "vancouver", "singapore", "dubai", "india", "united states", "remote"
    ]
    for l in lines[:15]:
        for kw in loc_keywords:
            if kw in l.lower():
                profile["location"] = l[:60]
                break
        if profile["location"]:
            break
    if not profile["location"]:
        profile["location"] = "Worldwide / Open to Relocation"

    # 5. Experience calculation
    exp_matches = re.findall(r'(\d+)\+?\s*years?(?:\s+of)?(?:\s+(?:combined|professional|hands-on|industry|relevant|software|engineering))?\s+experience', text, re.IGNORECASE)
    if exp_matches:
        profile["years_experience"] = max(int(m) for m in exp_matches)
    else:
        # Detect employment start dates (e.g. 2021, 2022)
        career_years = re.findall(r'\b(201\d|202[0-5])\s*[-–to]+\s*(?:present|current|now|202\d)\b', text, re.IGNORECASE)
        if career_years:
            earliest = min(int(y) for y in career_years)
            profile["years_experience"] = max(2026 - earliest, 1)
        else:
            profile["years_experience"] = 4

    # 6. Target Role identification (Dynamic matching across engineering titles)
    role_patterns = [
        r'(?:senior\s+|lead\s+|principal\s+|staff\s+|junior\s+)?(?:software|frontend|backend|full[\s-]stack|mobile|devops|data|ai|machine learning|automation|cloud|sre|qa|python|flutter|ios|android)\s+(?:engineer|developer|architect|specialist|analyst)',
        r'(?:senior\s+|lead\s+|principal\s+|staff\s+|junior\s+)?(?:design|mechanical|cad|cae|catia|nx|product\s+design|automotive|plastic|interior\s+trim)\s+(?:engineer|designer|specialist|analyst)',
    ]
    for l in lines[:25]:
        found = False
        for p in role_patterns:
            m = re.search(p, l, re.IGNORECASE)
            if m:
                clean_title = m.group(0).strip()
                clean_title = re.sub(r'^(?:profile|summary|accomplished|experienced|dedicated)\s+', '', clean_title, flags=re.IGNORECASE).strip()
                profile["current_role"] = clean_title.title()
                found = True
                break
        if found:
            break

    if not profile["current_role"]:
        # Fallback keyword match
        for l in lines[:25]:
            lower = l.lower()
            if any(k in lower for k in ["engineer", "developer", "architect", "lead", "specialist", "designer"]):
                clean_l = re.sub(r'^(?:profile|summary|accomplished|experienced|dedicated)\s+', '', l, flags=re.IGNORECASE).strip()
                profile["current_role"] = clean_l[:60].title()
                break

    if not profile["current_role"]:
        profile["current_role"] = "Design Engineer"

    # 7. Core Skills Extraction (Dynamic scanning against 200+ canonical taxonomy)
    text_lower = text.lower()
    matched_skills = []
    for s in CANONICAL_SKILLS:
        pattern = r'\b' + re.escape(s) + r'\b'
        if re.search(pattern, text_lower):
            matched_skills.append(s)

    profile["skills"] = sorted(list(set(matched_skills)))
    return profile
