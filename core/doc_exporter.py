import os
import csv
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import asyncio
from playwright.async_api import async_playwright

def add_hyperlink(paragraph, url, text, color="B47B38", underline=True):
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    if color:
        c = OxmlElement('w:color')
        c.set(qn('w:val'), color)
        rPr.append(c)
    if underline:
        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        rPr.append(u)
    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink

def export_to_docx(candidate_profile, jobs, output_path):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    logo_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "logo.png")
    if os.path.exists(logo_file):
        try:
            doc.add_picture(logo_file, width=Inches(0.65))
        except Exception:
            pass

    title = doc.add_paragraph()
    r = title.add_run("Almond AI — Verified Career Matches & Direct Application Dossier")
    r.font.name = "Calibri"
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(35, 23, 15)

    subtitle = doc.add_paragraph()
    cand_name = candidate_profile.get("name", "Candidate")
    r_sub = subtitle.add_run(f"Prepared for: {cand_name} | {len(jobs)} Direct ATS Verified Postings (100% Broker-Free)")
    r_sub.font.size = Pt(10.5)
    r_sub.font.color.rgb = RGBColor(146, 91, 36)

    doc.add_paragraph("—" * 50)

    # Candidate Summary
    doc.add_heading("1. Candidate Profile Overview", level=1)
    p = doc.add_paragraph()
    p.add_run("Candidate Name: ").bold = True
    p.add_run(f"{candidate_profile.get('name', 'N/A')}\n")
    p.add_run("Contact: ").bold = True
    p.add_run(f"{candidate_profile.get('phone', '')} | {candidate_profile.get('email', '')} | {candidate_profile.get('location', '')}\n")
    p.add_run("Target Role: ").bold = True
    p.add_run(f"{candidate_profile.get('current_role', 'N/A')} ({candidate_profile.get('years_experience', 0)}+ Years Experience)\n")
    p.add_run("Identified Skills: ").bold = True
    p.add_run(f"{', '.join(candidate_profile.get('skills', []))}\n")

    doc.add_heading("2. Verified Direct ATS Postings", level=1)
    for i, j in enumerate(jobs, 1):
        p_job = doc.add_paragraph()
        r_num = p_job.add_run(f"#{i}: {j.get('title')}\n")
        r_num.bold = True
        r_num.font.size = Pt(11.5)
        r_num.font.color.rgb = RGBColor(180, 123, 56)

        p_job.add_run("Company: ").bold = True
        p_job.add_run(f"{j.get('company')} | ")
        p_job.add_run("ATS System: ").bold = True
        p_job.add_run(f"{j.get('source')} | ")
        p_job.add_run("Match Score: ").bold = True
        p_job.add_run(f"{j.get('cvmatch_score', 0)}%\n")

        p_job.add_run("Location: ").bold = True
        p_job.add_run(f"{j.get('location_tag', j.get('location', 'Remote'))} ({j.get('work_mode', 'N/A')})\n")

        p_job.add_run("Package: ").bold = True
        r_comp = p_job.add_run(f"{j.get('comp_display', 'Competitive')}\n")
        r_comp.font.color.rgb = RGBColor(22, 101, 52)
        r_comp.bold = True

        p_job.add_run("Direct ATS Link: ").bold = True
        add_hyperlink(p_job, j.get("url", "#"), f"Open {j.get('company')} {j.get('source')} Portal")
        doc.add_paragraph("." * 40)

    doc.save(output_path)
    return output_path

async def export_to_pdf_async(candidate_profile, jobs, output_path):
    import html as htmllib
    cand_name_esc = htmllib.escape(str(candidate_profile.get('name', 'Candidate')))
    cand_role_esc = htmllib.escape(str(candidate_profile.get('current_role', 'N/A')))
    cand_email_esc = htmllib.escape(str(candidate_profile.get('email', '')))
    cand_phone_esc = htmllib.escape(str(candidate_profile.get('phone', '')))
    cand_loc_esc = htmllib.escape(str(candidate_profile.get('location', '')))
    cand_skills_esc = htmllib.escape(', '.join(str(s) for s in candidate_profile.get('skills', [])))
    cand_yoe_esc = htmllib.escape(str(candidate_profile.get('years_experience', 0)))

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page {{ size: A4; margin: 14mm; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 9.5pt; line-height: 1.45; color: #23170f; background: #faf7f2; }}
    .header {{ border-bottom: 2.5px solid #b47b38; padding-bottom: 8px; margin-bottom: 12px; }}
    h1 {{ font-size: 17pt; margin: 0 0 3px 0; color: #1c120c; }}
    .subtitle {{ font-size: 10pt; color: #8c5825; font-weight: 600; }}
    .brand-pill {{ display: inline-block; background: #faeed7; color: #925b24; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 8.5pt; margin-bottom: 4px; border: 1px solid #ebd09c; }}
    .profile-card {{ background: #ffffff; border: 1px solid #e8dbce; border-radius: 6px; padding: 10px 14px; margin-bottom: 14px; }}
    .job-card {{ background: #ffffff; border: 1px solid #e8dbce; border-radius: 6px; padding: 10px 12px; margin-bottom: 10px; page-break-inside: avoid; }}
    .job-title {{ font-weight: bold; color: #925b24; font-size: 10.5pt; }}
    .badge-comp {{ background: #dcfce7; color: #15803d; font-weight: bold; padding: 2px 6px; border-radius: 4px; font-size: 8.5pt; display: inline-block; margin-top: 4px; }}
    .badge-score {{ background: #faeed7; color: #8c5825; font-weight: bold; padding: 2px 6px; border-radius: 4px; font-size: 8.5pt; border: 1px solid #ebd09c; }}
    .apply-btn {{ display: inline-block; background: #b47b38; color: white !important; text-decoration: none; padding: 4px 10px; font-size: 8.5pt; font-weight: bold; border-radius: 4px; margin-top: 6px; }}
</style>
</head>
<body>
<div class="header">
    <div class="brand-pill">Almond AI Intelligence Report</div>
    <h1>Verified Career Matches & Direct Application Dossier</h1>
    <div class="subtitle">Prepared for {cand_name_esc} | {len(jobs)} Verified Direct ATS Postings (Zero Broker Middlemen)</div>
</div>

<div class="profile-card">
    <strong>Candidate:</strong> {cand_name_esc} ({cand_role_esc} · {cand_yoe_esc}+ YOE)<br>
    <strong>Contact:</strong> {cand_email_esc} | {cand_phone_esc} | {cand_loc_esc}<br>
    <strong>Skills:</strong> {cand_skills_esc}
</div>

<h3 style="color: #23170f; margin-bottom: 8px;">Direct ATS Postings</h3>
"""
    for i, j in enumerate(jobs, 1):
        j_title_esc = htmllib.escape(str(j.get('title', '')))
        j_comp_esc = htmllib.escape(str(j.get('company', '')))
        j_src_esc = htmllib.escape(str(j.get('source', 'ATS')))
        j_loc_esc = htmllib.escape(str(j.get('location_tag', j.get('location', 'Remote'))))
        j_mode_esc = htmllib.escape(str(j.get('work_mode', 'N/A')))
        j_comp_disp_esc = htmllib.escape(str(j.get('comp_display', 'Market Competitive')))
        j_url_esc = htmllib.escape(str(j.get('url', '#')))
        j_score = int(j.get('cvmatch_score', 0))

        html += f"""
<div class="job-card">
    <div class="job-title">#{i}: {j_title_esc} @ {j_comp_esc} <span class="badge-score">Match: {j_score}%</span></div>
    <div style="font-size: 8.5pt; color: #574133; margin-top: 2px;">
        ATS Portal: <strong>{j_src_esc}</strong> | Location: <strong>{j_loc_esc}</strong> ({j_mode_esc})
    </div>
    <div class="badge-comp">{j_comp_disp_esc}</div><br>
    <a href="{j_url_esc}" class="apply-btn" target="_blank">Direct ATS Application Link &rarr;</a>
</div>
"""

    html += "</body></html>"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")
            await page.pdf(path=output_path, format="A4", print_background=True)
            await browser.close()
        return output_path
    except Exception as pw_err:
        print(f"[DOC_EXPORTER] Notice: Playwright browser launch unavailable ({pw_err}). Using pure-Python PDF synthesizer.")
        return _export_pdf_pure_python(candidate_profile, jobs, output_path)

def _export_pdf_pure_python(candidate_profile, jobs, output_path):
    """Zero-dependency pure-Python PDF generation fallback for cloud containers."""
    from fpdf import FPDF

    class DossierPDF(FPDF):
        def header(self):
            logo_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "logo.png")
            if os.path.exists(logo_file):
                try:
                    self.image(logo_file, x=10, y=7, w=7)
                    self.set_x(19)
                except Exception:
                    pass
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(15, 23, 42)
            self.cell(0, 8, 'Almond AI — Verified Career Matches & Direct ATS Dossier', new_x='LMARGIN', new_y='NEXT')
            self.set_draw_color(226, 232, 240)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)

        def footer(self):
            self.set_y(-12)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(148, 163, 184)
            self.cell(0, 8, f'Page {self.page_no()}/{{nb}} — Almond AI (100% Broker-Free Direct Endpoints)', align='C')

    pdf = DossierPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    cand_name = candidate_profile.get("name", "Candidate")
    yoe = candidate_profile.get("years_experience", 3)
    role = candidate_profile.get("current_role", "Software Engineer")
    skills = ", ".join(candidate_profile.get("skills", [])[:10])

    pdf.set_fill_color(248, 250, 252)
    pdf.rect(10, pdf.get_y(), 190, 20, 'F')
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 5, f'Candidate: {cand_name} | Role: {role} ({yoe}+ Years Verified)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 4.5, f'Core Skills: {skills}')
    pdf.ln(4)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, f'Verified Direct ATS Postings ({len(jobs)} Opportunities)', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    for idx, j in enumerate(jobs, 1):
        if pdf.get_y() > 245:
            pdf.add_page()

        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(30, 58, 138)
        title = f"#{idx}: {j.get('title', '')} @ {j.get('company', '')}"
        score = f"{j.get('cvmatch_score', 0)}% Match"
        pdf.cell(150, 5.5, title[:65], new_x='RIGHT')
        pdf.set_font('Helvetica', 'B', 8.5)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(40, 5.5, score, align='R', new_x='LMARGIN', new_y='NEXT')

        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(71, 85, 105)
        portal = (j.get('source') or 'ATS').upper()
        loc = j.get('location_tag', j.get('location', 'Remote'))
        mode = j.get('work_mode', 'Remote')
        comp = j.get('comp_display', 'Market Competitive')
        pdf.cell(0, 4.5, f'Portal: {portal} | Location: {loc} ({mode}) | Package: {comp}', new_x='LMARGIN', new_y='NEXT')

        url = j.get('url', '')
        if url and url.startswith('http'):
            pdf.set_font('Helvetica', 'U', 7.5)
            pdf.set_text_color(79, 70, 229)
            pdf.cell(0, 4.5, 'Direct Apply URL: ' + url[:90], link=url, new_x='LMARGIN', new_y='NEXT')

        pdf.ln(2.5)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    pdf.output(output_path)
    return output_path

def export_to_pdf(candidate_profile, jobs, output_path):
    asyncio.run(export_to_pdf_async(candidate_profile, jobs, output_path))
    return output_path

def export_to_csv(jobs, output_path):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Company", "Role", "ATS Portal", "Location", "Work Mode", "Package", "Match Score", "Direct Apply URL", "Status", "Notes"])
        for j in jobs:
            writer.writerow([
                j.get("company", ""),
                j.get("title", ""),
                j.get("source", ""),
                j.get("location_tag", j.get("location", "")),
                j.get("work_mode", ""),
                j.get("comp_display", ""),
                f"{j.get('cvmatch_score', 0)}%",
                j.get("url", ""),
                "Ready to Apply",
                f"Matched skills: {', '.join(j.get('matched_skills', []))}"
            ])
    return output_path
