def generate_star_pitch(candidate_profile, job):
    cand_name = candidate_profile.get("name", "Applicant")
    cand_role = candidate_profile.get("current_role", "Software Engineer")
    cand_yoe = candidate_profile.get("years_experience", 3)
    cand_skills = candidate_profile.get("skills", [])
    cand_loc = candidate_profile.get("location", "India")
    cand_email = candidate_profile.get("email", "")
    cand_phone = candidate_profile.get("phone", "")

    job_title = job.get("title", "Software Engineer")
    company = job.get("company", "the Hiring Team")
    job_skills = job.get("skills", [])
    enr = job.get("enrichment") or {}
    summary = enr.get("summary", "")

    # Tailor based on role type
    title_lower = job_title.lower()

    if any(k in title_lower for k in ["scrap", "crawl", "extraction"]):
        focus_bullets = [
            "• Scaled Web Crawling: Architected resilient Python web crawlers parsing complex HTML, dynamic JavaScript DOMs, and JSON responses across hundreds of site variations.",
            "• Anti-Bot & Stability: Implemented robust user-agent rotation, dynamic wait logic, session/cookie handling, and pagination controls to maintain high crawler uptime.",
            "• Enterprise Data Integrity: Built automated validation pipelines using Pandas, NumPy, and SQL, persisting verified datasets into Amazon S3 storage."
        ]
        opening = f"With {cand_yoe}+ years of dedicated experience developing scalable Python web crawlers and data extraction pipelines, I specialize in extracting structured data at enterprise scale from dynamic, JavaScript-heavy targets."

    elif any(k in title_lower for k in ["ai", "automation", "agent", "llm"]):
        focus_bullets = [
            "• Applied AI & Workflow Automation: Architected end-to-end automated pipelines and agentic integrations leveraging LLMs, REST APIs, and automated triggers.",
            "• Rapid Application Execution: Built and shipped working mobile and web applications translating complex user requirements into production-ready software.",
            "• Enterprise Reliability: Combined rigorous CI/CD, Docker containerization, and monitoring with modern AI tools to ensure zero-downtime automation."
        ]
        opening = f"With {cand_yoe}+ years of engineering experience spanning enterprise infrastructure and modern AI application development, I bridge the critical gap between backend reliability and rapid AI workflow automation."

    elif any(k in title_lower for k in ["mobile", "flutter", "ios", "android", "swift", "react native"]):
        focus_bullets = [
            "• Cross-Platform & Native Mobile Architecture: Built responsive, high-performance mobile applications translating complex UX flows into smooth interactive experiences.",
            "• State Management & API Integration: Expertly implemented scalable state architectures (BLOC/Redux), local caching, and robust REST/GraphQL networking layers.",
            "• App Store Deployment & Lifecycle: Managed complete release cycles, code signing, CI build automation, and performance profiling."
        ]
        opening = f"With {cand_yoe}+ years of dedicated engineering experience building production-grade mobile applications, I specialize in crafting performant, intuitive mobile user experiences backed by clean architecture."

    elif any(k in title_lower for k in ["devops", "cloud", "infra", "sre", "kubernetes"]):
        focus_bullets = [
            "• Cloud & Container Infrastructure: Architected resilient cloud deployments utilizing Docker, Kubernetes, and Infrastructure as Code (Terraform).",
            "• CI/CD & Automation: Implemented automated build, test, and release pipelines drastically reducing deployment lead times and operational friction.",
            "• Observability & High Availability: Configured comprehensive monitoring, metrics collection, and alerting stacks to ensure zero-downtime reliability."
        ]
        opening = f"With {cand_yoe}+ years of enterprise infrastructure and DevOps experience, I specialize in building resilient, secure cloud systems and automated CI/CD deployment pipelines."

    elif any(k in title_lower for k in ["cad", "catia", "design engineer", "mechanical", "trim", "plastic", "nx", "solidworks", "creo", "automotive", "tooling"]):
        focus_bullets = [
            "• Automotive Plastic & Trim Design: 3+ years at Larsen & Toubro Technology Services specializing in interior trim components (Center Pillar Module - Pad-A, Pad-B, Lid-D) and B-surface engineering features (clip towers, ribs, doghouses, screw bosses).",
            "• CAD Modeling & Tooling Feasibility: Highly proficient in CATIA V5 (Part Design, Generative Shape Design, Assembly) and UG NX, executing master section development, draft analysis, mold parting direction, and clearance checks.",
            "• DFMEA, DMDR & PLM Integration: Rigorous application of Design for Manufacturing/Assembly (DMDR), failure mode avoidance (DFMEA), and end-to-end design lifecycle tracking within enterprise PLM systems."
        ]
        opening = f"With {cand_yoe}+ years of dedicated engineering experience in automotive interior trim and plastic component design at L&T Technology Services, I specialize in full-lifecycle 3D CAD modeling, master sections, and tooling feasibility using CATIA V5 and UG NX."

    else:
        focus_bullets = [
            "• Core Backend & Automation: Proficient in building modular, maintainable, and high-performance software systems.",
            "• Data Pipelines & APIs: Experienced in architecting robust REST endpoints, schema validation, and cloud storage integrations.",
            "• Production Best Practices: Thoroughly grounded in automated testing, containerization, and agile engineering best practices."
        ]
        opening = f"With {cand_yoe}+ years of professional engineering experience, I specialize in building reliable applications, automated services, and scalable production workflows."
    bullets_text = "\n".join(focus_bullets)

    pitch = f"""Dear Hiring Team at {company},

I am writing to express my strong interest in the {job_title} position. {opening}

Key highlights of my background:
{bullets_text}

I am confident that my technical experience and proactive problem-solving approach will add immediate value to your team. I welcome the opportunity to discuss how my skill set aligns with {company}'s current technical initiatives.

Sincerely,
{cand_name}
{cand_loc} | {cand_phone} | {cand_email}"""

    return pitch.strip()
