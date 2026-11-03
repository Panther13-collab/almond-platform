import datetime

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

def generate_tailored_cover_letter(candidate_profile, job):
    """
    Generates a formal, tailored executive cover letter grounded in candidate profile
    and mapped directly to the target company and role.
    """
    today_str = datetime.date.today().strftime("%B %d, %Y")
    cand_name = candidate_profile.get("name", "Applicant")
    cand_role = candidate_profile.get("current_role", "Software Engineer")
    cand_yoe = candidate_profile.get("years_experience", 3)
    cand_skills = candidate_profile.get("skills", [])
    cand_loc = candidate_profile.get("location", "India")
    cand_email = candidate_profile.get("email", "")
    cand_phone = candidate_profile.get("phone", "")

    job_title = job.get("title", "Software Engineer")
    company = job.get("company", "Hiring Organization")
    job_loc = job.get("location", "Remote / Onsite")
    enr = job.get("enrichment") or {}
    job_skills = job.get("skills", [])
    if not job_skills and enr.get("tech_stack"):
        job_skills = enr.get("tech_stack")

    # Match common skills between candidate and job
    matched_skills = [s for s in cand_skills if any(js.lower() in s.lower() or s.lower() in js.lower() for js in job_skills)]
    if not matched_skills:
        matched_skills = cand_skills[:4] if cand_skills else ["Full-Stack Architecture", "System Design", "Cloud Infrastructure"]

    skills_highlight = ", ".join(matched_skills[:4])
    title_lower = job_title.lower()

    if any(k in title_lower for k in ["cad", "catia", "design engineer", "mechanical", "trim", "plastic", "nx", "solidworks", "creo", "automotive"]):
        domain_narrative = (
            f"Over the course of {cand_yoe}+ years specializing in mechanical engineering and automotive interior trim design at L&T Technology Services, "
            f"I have led end-to-end 3D CAD modeling, master section development, and manufacturing tooling feasibility for complex plastic components "
            f"including Center Pillar modules, trim panels, and B-surface structural attachments (ribs, doghouses, screw bosses, and clip towers)."
        )
        impact_narrative = (
            f"At {company}, technical precision and Design for Manufacturing & Assembly (DFMEA/DMDR) standards are vital. "
            f"My deep fluency in CATIA V5 and UG NX—combined with rigorous draft analysis, mold parting direction verification, "
            f"and strict adherence to OEM engineering tolerances—ensures rapid prototyping and seamless handover to tooling suppliers with minimal revision cycles."
        )
    elif any(k in title_lower for k in ["ai", "automation", "agent", "llm"]):
        domain_narrative = (
            f"With {cand_yoe}+ years of focused engineering experience building production automation and intelligent agentic workflows, "
            f"I bridge the critical gap between state-of-the-art LLM capabilities and high-availability enterprise backend infrastructure. "
            f"My day-to-day focus centers on deploying fault-tolerant microservices, robust API integrations, and scalable data processing pipelines."
        )
        impact_narrative = (
            f"What attracts me specifically to {company} is your commitment to modern engineering velocity and high-impact automation. "
            f"Leveraging my hands-on background in {skills_highlight}, I bring a structured approach to designing resilient autonomous tasks, "
            f"optimizing context pipelines, and safeguarding system reliability under real-world load."
        )
    elif any(k in title_lower for k in ["mobile", "flutter", "ios", "android", "swift", "react native"]):
        domain_narrative = (
            f"With {cand_yoe}+ years dedicated to architecting and publishing high-performance mobile applications, "
            f"I have delivered cross-platform and native solutions that balance fluid, responsive UX with clean, modular system architecture. "
            f"My technical toolkit includes advanced state management, offline-first data synchronization, and automated CI/CD deployment pipelines."
        )
        impact_narrative = (
            f"In reviewing {company}'s current technical landscape, the {job_title} role aligns directly with my core competency. "
            f"I bring deep practical experience building with {skills_highlight}, ensuring that every user-facing interaction "
            f"is intuitive, battery-efficient, and engineered to enterprise reliability standards."
        )
    else:
        domain_narrative = (
            f"Over {cand_yoe}+ years of software engineering experience, I have developed and deployed mission-critical systems, "
            f"scalable backend services, and automated data pipelines. My engineering philosophy is anchored in clean architecture, "
            f"defensive error handling, and building tools that empower users with exceptional reliability."
        )
        impact_narrative = (
            f"The opportunity to contribute to {company} as {job_title} stands out because of the high technical bar and impact of your products. "
            f"With proven mastery across {skills_highlight}, I am prepared to step in, ramp up quickly, and deliver immediate value across your engineering roadmap."
        )

    contact_info_line = f"{cand_email}"
    if cand_phone:
        contact_info_line += f" • {cand_phone}"
    if cand_loc:
        contact_info_line += f" • {cand_loc}"

    cover_letter = f"""{cand_name}
{contact_info_line}

{today_str}

Hiring Team / Engineering Leadership
{company}
{job_loc}

RE: Application for {job_title} (Verified Direct ATS Position)

Dear Hiring Team,

I am writing to submit my application for the {job_title} position at {company}. Having followed {company}'s industry trajectory and engineering initiatives, I am eager to contribute my technical foundation and execution rigor to your engineering team.

{domain_narrative}

{impact_narrative}

Throughout my career, I have prided myself on ownership, cross-functional collaboration, and the ability to solve ambiguous engineering problems with surgical clarity. Whether optimizing database query latency, engineering robust CAD assemblies, or deploying cloud automations, I maintain an unrelenting focus on system longevity and end-user excellence.

I would welcome the opportunity to speak with you regarding how my technical background in {skills_highlight} directly supports {company}'s current goals for the {job_title} position. Thank you for your time, consideration, and dedication to direct, merit-based hiring.

Sincerely,

{cand_name}
{cand_email} | {cand_phone}"""

    return cover_letter.strip()

