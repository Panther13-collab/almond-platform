import os
import json
import re

INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")

def update_seo():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update <title> and meta tags to reinforce both 'Almond Jobs' and 'almond jobs'
    old_title = '<title>Almond Jobs — 3.3M+ Direct Enterprise Job Openings | 0% Recruiter Spread | Move First. Apply Unseen.</title>'
    new_title = '<title>Almond Jobs — 3.3M+ Direct Enterprise Job Openings | Official Career Platform | 0% Recruiter Spread</title>'
    if old_title in html:
        html = html.replace(old_title, new_title)
        print("Updated <title> tag.")

    # 2. Put the brand identity pill directly INSIDE the <h1> tag for maximum keyword weight
    old_h1_pattern = r'<!-- Enterprise Authority Identity Pill -->\s*<div class="inline-flex items-center gap-2 px-3\.5 py-1\.5 rounded-full bg-slate-900/5 border border-slate-900/10 text-slate-800 text-xs font-bold mb-3 shadow-2xs">\s*<img src="/static/logo\.png"[^>]*>\s*<span>Almond Jobs &mdash; 3,315,000\+ Direct Enterprise ATS Feeds</span>\s*<span class="w-1\.5 h-1\.5 rounded-full bg-emerald-500 animate-pulse"></span>\s*</div>\s*<!-- Perfectly Centered Horizontal Dual Headline \(Responsive Scale\) -->\s*<h1 class="tracking-tight max-w-4xl mx-auto mb-4 sm:mb-5 text-center select-none flex flex-col items-center justify-center">\s*<span class="block text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-slate-950 tracking-tight leading-\[1\.08\] sm:leading-\[1\.06\] whitespace-nowrap">Move first\.</span>\s*<span class="block text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-violet-600 tracking-tight leading-\[1\.08\] sm:leading-\[1\.06\] mt-1 sm:mt-2 whitespace-nowrap">Apply unseen!</span>\s*</h1>'
    
    new_h1 = '''<!-- Perfectly Centered Horizontal Dual Headline with Embedded Brand Identity (Responsive Scale) -->
                    <h1 class="tracking-tight max-w-4xl mx-auto mb-4 sm:mb-5 text-center select-none flex flex-col items-center justify-center">
                        <span class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/5 border border-slate-900/10 text-slate-800 text-xs font-bold mb-3 shadow-2xs">
                            <img src="/static/logo.png" alt="Almond Logo" class="w-3.5 h-3.5 object-contain">
                            <span>Almond Jobs &mdash; 3,315,000+ Direct Enterprise ATS Feeds</span>
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                        </span>
                        <span class="block text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-slate-950 tracking-tight leading-[1.08] sm:leading-[1.06] whitespace-nowrap">Move first.</span>
                        <span class="block text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-violet-600 tracking-tight leading-[1.08] sm:leading-[1.06] mt-1 sm:mt-2 whitespace-nowrap">Apply unseen!</span>
                    </h1>'''

    match = re.search(old_h1_pattern, html, flags=re.DOTALL)
    if match:
        html = html[:match.start()] + new_h1 + html[match.end():]
        print("Embedded brand pill into <h1> tag.")
    else:
        print("Warning: old_h1_pattern not matched via regex.")

    # 3. Add Google for Jobs JobPosting schemas to homepage JSON-LD
    job_postings_schema = ''',
        {
          "@type": "JobPosting",
          "@id": "https://almondjobs.com/jobs/software-engineer#job",
          "title": "Software Engineer — Direct Enterprise ATS Postings",
          "description": "<p>Almond Jobs (almondjobs.com) provides unadvertised direct software engineer job openings ingested directly from corporate internal ATS servers (Ashby, Greenhouse, Lever, Workday) with 0% recruiter spread. High-paying backend, frontend, and full-stack positions with 100% direct application links.</p>",
          "datePosted": "2026-11-01",
          "validThrough": "2027-11-01",
          "employmentType": "FULL_TIME",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Almond Jobs Enterprise Feeds",
            "sameAs": "https://almondjobs.com",
            "logo": "https://almondjobs.com/static/logo.png"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "@type": "PostalAddress",
              "addressCountry": "IN",
              "addressLocality": "Remote / Nationwide"
            }
          },
          "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "INR",
            "value": {
              "@type": "QuantitativeValue",
              "minValue": 1200000,
              "maxValue": 4500000,
              "unitText": "YEAR"
            }
          },
          "directApply": true,
          "url": "https://almondjobs.com/jobs/software-engineer"
        },
        {
          "@type": "JobPosting",
          "@id": "https://almondjobs.com/jobs/ai-ml-specialist#job",
          "title": "AI/ML Specialist & LLM Engineer — Direct Corporate Feeds",
          "description": "<p>Direct corporate machine learning, generative AI, PyTorch, and LLM engineering positions on Almond Jobs. Direct links to employer internal ATS infrastructure with zero third-party agency cuts.</p>",
          "datePosted": "2026-11-01",
          "validThrough": "2027-11-01",
          "employmentType": "FULL_TIME",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Almond Jobs Enterprise Feeds",
            "sameAs": "https://almondjobs.com",
            "logo": "https://almondjobs.com/static/logo.png"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "@type": "PostalAddress",
              "addressCountry": "IN",
              "addressLocality": "Remote / Hybrid"
            }
          },
          "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "INR",
            "value": {
              "@type": "QuantitativeValue",
              "minValue": 1800000,
              "maxValue": 6000000,
              "unitText": "YEAR"
            }
          },
          "directApply": true,
          "url": "https://almondjobs.com/jobs/ai-ml-specialist"
        },
        {
          "@type": "JobPosting",
          "@id": "https://almondjobs.com/jobs/direct-internships-2026#job",
          "title": "Direct Corporate Internships 2026 (5,100+ Live Student Portals)",
          "description": "<p>Summer, winter, and off-cycle direct corporate internships for college students and freshers across top tech and Fortune 500 enterprises on Almond Jobs (almondjobs.com). Zero middleman fees, 100% direct application links.</p>",
          "datePosted": "2026-11-01",
          "validThrough": "2027-11-01",
          "employmentType": "INTERN",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Almond Jobs Enterprise Feeds",
            "sameAs": "https://almondjobs.com",
            "logo": "https://almondjobs.com/static/logo.png"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "@type": "PostalAddress",
              "addressCountry": "IN",
              "addressLocality": "Remote / Nationwide"
            }
          },
          "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "INR",
            "value": {
              "@type": "QuantitativeValue",
              "minValue": 30000,
              "maxValue": 120000,
              "unitText": "MONTH"
            }
          },
          "directApply": true,
          "url": "https://almondjobs.com/jobs/direct-internships-2026"
        },
        {
          "@type": "JobPosting",
          "@id": "https://almondjobs.com/jobs/immediate-joiners#job",
          "title": "Immediate Joiner & 15-Day Notice Tech Roles — Almond Jobs Direct",
          "description": "<p>Fast-track corporate hiring pipeline for software developers, engineers, and tech professionals available for immediate joining or within a 15-day notice period. Zero recruiter delays, direct employer connection on Almond Jobs.</p>",
          "datePosted": "2026-11-01",
          "validThrough": "2027-11-01",
          "employmentType": "FULL_TIME",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Almond Jobs Enterprise Feeds",
            "sameAs": "https://almondjobs.com",
            "logo": "https://almondjobs.com/static/logo.png"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "@type": "PostalAddress",
              "addressCountry": "IN",
              "addressLocality": "Remote / Nationwide"
            }
          },
          "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "INR",
            "value": {
              "@type": "QuantitativeValue",
              "minValue": 1400000,
              "maxValue": 4000000,
              "unitText": "YEAR"
            }
          },
          "directApply": true,
          "url": "https://almondjobs.com/jobs/immediate-joiners"
        }'''

    # Insert JobPostings right after FAQPage closing brace in @graph
    faq_end_target = '''            }
          ]
        }
      ]
    }
    </script>'''

    new_faq_end = '''            }
          ]
        }''' + job_postings_schema + '''
      ]
    }
    </script>'''

    if faq_end_target in html and "Almond Jobs Enterprise Feeds" not in html:
        html = html.replace(faq_end_target, new_faq_end)
        print("Added Google for Jobs schema items to index.html.")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print("Successfully updated index.html with Google for Jobs and <h1> targeting!")

if __name__ == "__main__":
    update_seo()
