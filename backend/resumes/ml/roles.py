"""
Predict the most suitable job roles for a candidate from their skills.
Each role has core skills (weight 2) and bonus skills (weight 1).
The live-job search uses the top predicted role as its search keyword.
"""

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
}


def predict_roles(skills, top_n=3):
    have = {s.lower() for s in skills}
    results = []
    for role, (core, bonus) in ROLES.items():
        max_pts = len(core) * 2 + len(bonus)
        pts = sum(2 for s in core if s.lower() in have) + sum(1 for s in bonus if s.lower() in have)
        if pts == 0:
            continue
        missing_core = [s for s in core if s.lower() not in have]
        results.append({
            "role": role,
            "fit": round(pts / max_pts * 100),
            "missing_core_skills": missing_core,
        })
    results.sort(key=lambda r: r["fit"], reverse=True)
    return results[:top_n]
