"""
Predict the most suitable job roles for a candidate from their skills.
Each role has core skills (weight 2) and bonus skills (weight 1).
The live-job search uses the top predicted role as its search keyword.
"""
import re

ROLES = {
    "Python Developer": (["Python", "Django", "SQL"], ["Flask", "FastAPI", "Django REST Framework", "PostgreSQL", "REST API", "Git", "Docker", "Celery", "Redis"]),
    "Full Stack Developer": (["JavaScript", "React", "Node.js", "SQL", "HTML", "CSS"], ["Python", "Django", "MongoDB", "PostgreSQL", "REST API", "Git", "Docker", "TypeScript"]),
    "Frontend Developer": (["HTML", "CSS", "JavaScript", "React"], ["TypeScript", "Redux", "Next.js", "Tailwind CSS", "Angular", "Vue.js", "Figma"]),
    "Backend Developer": (["REST API", "SQL", "Git"], ["Python", "Django", "Java", "Spring Boot", "Node.js", "PostgreSQL", "Redis", "Docker", "Microservices"]),
    "Java Developer": (["Java", "Spring Boot", "SQL"], ["Hibernate", "Microservices", "REST API", "MySQL", "OOP", "Git"]),
    "Data Analyst": (["SQL", "Excel", "Data Analysis"], ["Python", "Pandas", "Power BI", "Tableau", "Statistics", "Matplotlib"]),
    "Data Scientist": (["Python", "Machine Learning", "Statistics", "Pandas"], ["Scikit-learn", "Deep Learning", "NumPy", "SQL", "TensorFlow", "PyTorch", "Data Science"]),
    "Machine Learning Engineer": (["Python", "Machine Learning", "Deep Learning"], ["TensorFlow", "PyTorch", "Scikit-learn", "NLP", "Computer Vision", "Docker", "AWS"]),
    "AI / GenAI Engineer": (["Python", "Generative AI", "NLP"], ["LangChain", "Prompt Engineering", "Deep Learning", "PyTorch", "FastAPI", "Docker"]),
    "DevOps Engineer": (["Linux", "Docker", "CI/CD"], ["Kubernetes", "AWS", "Jenkins", "Terraform", "Git", "Bash", "Nginx", "Azure"]),
    "Cloud Engineer": (["AWS", "Linux"], ["Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Python"]),
    "Android Developer": (["Android", "Kotlin"], ["Java", "Firebase", "REST API", "Git"]),
    "Mobile App Developer": (["Flutter", "Dart"], ["React Native", "Firebase", "Android", "iOS", "REST API"]),
    "QA / Test Engineer": (["Manual Testing"], ["Selenium", "Unit Testing", "Postman", "Jira", "Java", "Python", "Agile"]),
    "Cyber Security Analyst": (["Cyber Security", "Computer Networks"], ["Linux", "Python", "Bash"]),
    "Technical Support Engineer": (["Technical Support", "Troubleshooting", "Customer Service"],
                                   ["Ticketing Tools", "Windows", "Computer Networks", "ITIL", "SLA", "Remote Support",
                                    "Linux", "SQL", "Communication"]),
    "IT Support / Helpdesk": (["Troubleshooting", "Windows", "Hardware"],
                              ["Computer Networks", "Active Directory", "Ticketing Tools", "Remote Support", "MS Office",
                               "ITIL", "Customer Service"]),
    "Customer Support Executive": (["Customer Service", "Communication"],
                                   ["CRM", "Ticketing Tools", "Email & Chat Support", "MS Office", "Excel",
                                    "Problem Solving", "Time Management"]),
    "Business Analyst": (["Business Analysis", "SQL", "Excel"],
                         ["Power BI", "Tableau", "Agile", "Jira", "Communication", "Data Analysis"]),
    "UI/UX Designer": (["UI/UX Design", "Figma"], ["HTML", "CSS", "Communication"]),
    "Database Administrator": (["SQL", "PostgreSQL"], ["MySQL", "Oracle", "Linux", "Redis", "MongoDB", "Bash"]),
    "Network Engineer": (["Computer Networks", "Linux"], ["Cyber Security", "Windows", "Bash", "AWS"]),

    # ---------------- non-IT roles
    "Accountant": (["Accounting", "Tally", "GST"], ["TDS", "Taxation", "Excel", "Payroll", "Financial Analysis", "Auditing", "SAP"]),
    "Finance / Audit Executive": (["Financial Analysis", "Auditing", "Excel"], ["Accounting", "Taxation", "SAP", "GST", "Power BI"]),
    "Banking Executive": (["Banking Operations"], ["Sales", "Customer Service", "Excel", "CRM", "Communication", "Accounting"]),
    "Sales Executive": (["Sales"], ["Communication", "Business Development", "CRM", "Negotiation", "Telecalling", "Customer Service", "Excel", "Retail"]),
    "Business Development Executive": (["Business Development", "Sales"], ["Negotiation", "CRM", "Communication", "Marketing", "MS Office"]),
    "Digital Marketing Executive": (["Digital Marketing", "SEO"], ["Content Writing", "Marketing", "Graphic Design", "Excel", "Communication"]),
    "Content Writer": (["Content Writing"], ["SEO", "Digital Marketing", "MS Office", "Communication"]),
    "HR Executive / Recruiter": (["Recruitment", "HR Operations"], ["Payroll", "Communication", "MS Office", "Excel", "Training & Development"]),
    "Teacher / Trainer": (["Teaching"], ["Communication", "Counselling", "MS Office", "Training & Development", "Leadership"]),
    "Back Office / Data Entry Executive": (["Back Office"], ["MS Office", "Excel", "Communication", "Time Management", "CRM"]),
    "Office Administrator": (["Office Administration"], ["MS Office", "Excel", "Communication", "Back Office", "Time Management"]),
    "Operations / Supply Chain Executive": (["Supply Chain"], ["Excel", "SAP", "Back Office", "Communication", "Negotiation"]),
    "Telecaller / Customer Care Executive": (["Telecalling"], ["Communication", "Customer Service", "Sales", "CRM", "Email & Chat Support"]),
    "Retail Store Executive": (["Retail"], ["Sales", "Customer Service", "Communication", "MS Office"]),
    "Mechanical Engineer": (["Mechanical Engineering", "AutoCAD"], ["SolidWorks", "CATIA", "Quality Control", "Six Sigma", "Excel"]),
    "Civil Engineer": (["Civil Engineering", "AutoCAD"], ["Excel", "Quality Control", "MS Office", "Leadership"]),
    "Electrical Engineer": (["Electrical Engineering"], ["AutoCAD", "Quality Control", "MS Office"]),
    "Quality Control Executive": (["Quality Control"], ["Six Sigma", "Excel", "Mechanical Engineering", "MS Office"]),
    "Graphic Designer": (["Graphic Design"], ["Video Editing", "UI/UX Design", "Figma", "Digital Marketing", "Content Writing"]),
    "Nurse / Healthcare Staff": (["Patient Care"], ["Communication", "Lab Technician", "MS Office", "Teamwork"]),
    "Medical Coder": (["Medical Coding"], ["Patient Care", "Excel", "MS Office"]),
    "Pharmacist / Medical Representative": (["Pharmacy"], ["Sales", "Communication", "Patient Care"]),
    "Lab Technician": (["Lab Technician"], ["Patient Care", "MS Office", "Communication"]),
    "Hotel / Hospitality Executive": (["Hospitality"], ["Customer Service", "Communication", "Sales"]),

    # ---------------- science graduates (Chemistry, Microbiology, Pharma)
    "QC Chemist / Analytical Chemist": (["Analytical Chemistry", "HPLC"],
                                        ["Gas Chromatography", "Spectroscopy", "Titration", "Wet Chemistry", "GLP", "GMP",
                                         "Method Validation", "SOP Documentation", "Lab Safety"]),
    "R&D Chemist": (["Organic Synthesis"], ["Analytical Chemistry", "HPLC", "Spectroscopy", "Method Validation",
                                            "Lab Safety", "SOP Documentation"]),
    "Production Chemist": (["Chemical Process"], ["GMP", "SOP Documentation", "Lab Safety", "Quality Control",
                                                  "Titration", "Six Sigma"]),
    "Lab Chemist": (["Wet Chemistry", "Titration"], ["Analytical Chemistry", "Spectroscopy", "Lab Safety", "GLP",
                                                     "SOP Documentation", "MS Office"]),
    "Microbiologist": (["Microbiology"], ["PCR", "Cell Culture", "GLP", "GMP", "SOP Documentation", "Lab Safety"]),
    "QA Executive (Pharma)": (["GMP", "SOP Documentation"], ["Quality Control", "Method Validation", "GLP", "Auditing",
                                                             "Regulatory Affairs"]),
}


def predict_roles(skills, top_n=3, text=""):
    """
    Rank roles by how many of their skills the candidate has.
    A role needs at least one of its must-have (core) skills to be suggested.
    If the resume text itself names the role (e.g. "Sales Executive", "Teacher"), it gets a small boost.
    """
    have = {s.lower() for s in skills}
    low = (text or "").lower()
    results = []
    for role, (core, bonus) in ROLES.items():
        if not any(s.lower() in have for s in core):
            continue
        max_pts = len(core) * 2 + len(bonus)
        pts = sum(2 for s in core if s.lower() in have) + sum(1 for s in bonus if s.lower() in have)
        fit = pts / max_pts * 100
        if low and any(len(t.strip()) >= 4 and re.search(r"\b" + re.escape(t.strip()) + r"\b", low)
                       for t in role.lower().split("/")):
            fit = min(100, fit + 15)
        missing_core = [s for s in core if s.lower() not in have]
        results.append({
            "role": role,
            "fit": round(fit),
            "missing_core_skills": missing_core,
        })
    results.sort(key=lambda r: r["fit"], reverse=True)
    return results[:top_n]
