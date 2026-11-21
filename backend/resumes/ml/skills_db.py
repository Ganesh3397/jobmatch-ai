"""
Skill taxonomy used by the NLP skill extractor.

Format:  "Canonical Skill": ("category", ["alias 1", "alias 2", ...])
The canonical name itself is always matched, aliases are optional.
Add more skills here any time - the extractor picks them up automatically.
"""

SKILLS = {
    # ---------------- Programming languages
    "Python": ("Programming", ["python3", "py"]),
    "Java": ("Programming", ["core java", "java 8", "java8"]),
    "JavaScript": ("Programming", ["js", "javascript es6", "es6", "ecmascript"]),
    "TypeScript": ("Programming", ["ts"]),
    "C": ("Programming", ["c language", "c programming"]),
    "C++": ("Programming", ["cpp", "c plus plus"]),
    "C#": ("Programming", ["c sharp", "csharp"]),
    "Go": ("Programming", ["golang"]),
    "Rust": ("Programming", []),
    "Kotlin": ("Programming", []),
    "Swift": ("Programming", []),
    "PHP": ("Programming", []),
    "Ruby": ("Programming", []),
    "R": ("Programming", ["r programming", "r language"]),
    "Dart": ("Programming", []),
    "Scala": ("Programming", []),
    "Bash": ("Programming", ["shell scripting", "shell script", "bash scripting"]),

    # ---------------- Frontend
    "HTML": ("Frontend", ["html5"]),
    "CSS": ("Frontend", ["css3"]),
    "React": ("Frontend", ["react.js", "reactjs", "react js"]),
    "Redux": ("Frontend", ["redux toolkit"]),
    "Next.js": ("Frontend", ["nextjs", "next js"]),
    "Angular": ("Frontend", ["angularjs", "angular.js"]),
    "Vue.js": ("Frontend", ["vue", "vuejs", "vue js"]),
    "Tailwind CSS": ("Frontend", ["tailwind", "tailwindcss"]),
    "Bootstrap": ("Frontend", []),
    "jQuery": ("Frontend", []),
    "Material UI": ("Frontend", ["mui", "material-ui"]),

    # ---------------- Backend
    "Django": ("Backend", ["django framework"]),
    "Django REST Framework": ("Backend", ["drf", "django rest", "django-rest-framework"]),
    "Flask": ("Backend", []),
    "FastAPI": ("Backend", ["fast api"]),
    "Node.js": ("Backend", ["nodejs", "node js", "node"]),
    "Express.js": ("Backend", ["express", "expressjs"]),
    "Spring Boot": ("Backend", ["spring", "springboot", "spring framework"]),
    "Hibernate": ("Backend", []),
    "Laravel": ("Backend", []),
    ".NET": ("Backend", ["dotnet", "asp.net", "asp.net core", ".net core"]),
    "REST API": ("Backend", ["rest apis", "restful", "restful api", "rest", "api development"]),
    "GraphQL": ("Backend", []),
    "Microservices": ("Backend", ["microservice", "micro services"]),
    "Celery": ("Backend", []),

    # ---------------- Databases
    "SQL": ("Database", ["structured query language"]),
    "PostgreSQL": ("Database", ["postgres", "postgre sql", "psql"]),
    "MySQL": ("Database", ["my sql"]),
    "MongoDB": ("Database", ["mongo", "mongo db"]),
    "Redis": ("Database", []),
    "SQLite": ("Database", []),
    "Oracle": ("Database", ["oracle db", "pl/sql", "plsql"]),
    "Firebase": ("Database", ["firestore"]),
    "Elasticsearch": ("Database", ["elastic search"]),
    "Cassandra": ("Database", []),

    # ---------------- Cloud / DevOps
    "AWS": ("Cloud & DevOps", ["amazon web services", "ec2", "s3", "aws lambda"]),
    "Azure": ("Cloud & DevOps", ["microsoft azure"]),
    "Google Cloud": ("Cloud & DevOps", ["gcp", "google cloud platform"]),
    "Docker": ("Cloud & DevOps", ["containerization", "dockerfile"]),
    "Kubernetes": ("Cloud & DevOps", ["k8s"]),
    "CI/CD": ("Cloud & DevOps", ["ci cd", "continuous integration", "continuous deployment"]),
    "Jenkins": ("Cloud & DevOps", []),
    "GitHub Actions": ("Cloud & DevOps", []),
    "Terraform": ("Cloud & DevOps", []),
    "Linux": ("Cloud & DevOps", ["ubuntu", "unix"]),
    "Nginx": ("Cloud & DevOps", []),
    "Git": ("Tools", ["github", "gitlab", "version control"]),

    # ---------------- Data / AI / ML
    "Machine Learning": ("AI & Data", ["ml", "machine-learning"]),
    "Deep Learning": ("AI & Data", ["dl", "neural networks", "neural network"]),
    "NLP": ("AI & Data", ["natural language processing"]),
    "Computer Vision": ("AI & Data", ["image processing", "opencv"]),
    "Generative AI": ("AI & Data", ["genai", "gen ai", "llm", "llms", "large language models"]),
    "Prompt Engineering": ("AI & Data", []),
    "LangChain": ("AI & Data", []),
    "TensorFlow": ("AI & Data", ["tensor flow", "keras"]),
    "PyTorch": ("AI & Data", ["torch"]),
    "Scikit-learn": ("AI & Data", ["sklearn", "scikit learn"]),
    "Pandas": ("AI & Data", []),
    "NumPy": ("AI & Data", ["numpy"]),
    "Matplotlib": ("AI & Data", ["seaborn"]),
    "Data Analysis": ("AI & Data", ["data analytics", "data analyst"]),
    "Data Science": ("AI & Data", ["data scientist"]),
    "Power BI": ("AI & Data", ["powerbi"]),
    "Tableau": ("AI & Data", []),
    "Excel": ("AI & Data", ["ms excel", "advanced excel", "microsoft excel"]),
    "Statistics": ("AI & Data", ["statistical analysis"]),
    "Big Data": ("AI & Data", ["hadoop", "spark", "pyspark", "apache spark"]),

    # ---------------- Mobile
    "Android": ("Mobile", ["android development"]),
    "iOS": ("Mobile", ["ios development"]),
    "Flutter": ("Mobile", []),
    "React Native": ("Mobile", ["react-native"]),

    # ---------------- Testing / Tools / Others
    "Selenium": ("Testing", []),
    "Unit Testing": ("Testing", ["pytest", "junit", "jest", "unittest"]),
    "Manual Testing": ("Testing", ["software testing", "qa testing"]),
    "Postman": ("Tools", []),
    "Jira": ("Tools", []),
    "Figma": ("Tools", []),
    "Agile": ("Methodology", ["scrum", "agile methodology"]),
    "DSA": ("Fundamentals", ["data structures", "algorithms", "data structures and algorithms"]),
    "OOP": ("Fundamentals", ["oops", "object oriented programming", "object-oriented"]),
    "DBMS": ("Fundamentals", ["database management"]),
    "Operating Systems": ("Fundamentals", ["os concepts"]),
    "Computer Networks": ("Fundamentals", ["networking", "tcp/ip"]),
    "Cyber Security": ("Security", ["cybersecurity", "information security", "ethical hacking"]),
    "Blockchain": ("Emerging", ["web3", "solidity"]),

    # ---------------- IT / Technical / Customer support
    "Technical Support": ("Support", ["tech support", "technical assistance", "l1 support", "l2 support",
                                      "level 1 support", "level 2 support", "desktop support", "application support"]),
    "Troubleshooting": ("Support", ["troubleshoot", "troubleshooted", "issue resolution", "root cause analysis",
                                    "diagnosing issues", "debugging issues"]),
    "Customer Service": ("Support", ["customer support", "customer handling", "client support", "customer satisfaction",
                                     "csat", "customer queries", "customer issues"]),
    "Ticketing Tools": ("Support", ["servicenow", "freshdesk", "zendesk", "jira service management", "ticketing tool",
                                    "ticketing system", "help desk software", "helpdesk tool"]),
    "ITIL": ("Support", ["itil v4", "incident management", "change management", "problem management"]),
    "SLA": ("Support", ["service level agreement", "slas", "sla compliance"]),
    "Windows": ("Support", ["windows os", "windows 10", "windows 11", "windows server", "windows administration"]),
    "Active Directory": ("Support", ["group policy", "gpo", "user account management"]),
    "Hardware": ("Support", ["hardware troubleshooting", "desktop hardware", "printer", "printers", "laptop repair",
                             "hardware installation", "peripherals"]),
    "Remote Support": ("Support", ["anydesk", "teamviewer", "remote desktop", "rdp", "remote assistance"]),
    "Email & Chat Support": ("Support", ["email support", "chat support", "voice support", "call handling",
                                         "inbound calls", "outbound calls", "voice process", "non-voice process"]),
    "MS Office": ("Tools", ["microsoft office", "ms word", "powerpoint", "outlook", "ms office suite"]),
    "CRM": ("Business", ["salesforce", "hubspot", "zoho crm", "customer relationship management"]),
    "Business Analysis": ("Business", ["requirement gathering", "requirements gathering", "brd", "frd",
                                       "gap analysis", "business requirements", "stakeholder management"]),
    "UI/UX Design": ("Design", ["ui design", "ux design", "user experience", "user interface design", "wireframing",
                                "wireframes", "prototyping", "adobe xd", "user research"]),

    # ---------------- Soft skills
    "Communication": ("Soft Skills", ["communication skills"]),
    "Teamwork": ("Soft Skills", ["team player", "collaboration"]),
    "Leadership": ("Soft Skills", ["team lead", "leading teams"]),
    "Problem Solving": ("Soft Skills", ["problem-solving", "analytical skills"]),
    "Time Management": ("Soft Skills", []),
}

# Aliases that are too short / ambiguous to match in free text on their own.
# They are matched only when they appear in a "skills" style list context.
AMBIGUOUS_ALIASES = {"py", "js", "ts", "ml", "dl", "r", "c", "go", "node", "rest", "spring", "os", "express"}

SOFT_SKILL_CATEGORY = "Soft Skills"


def category_of(skill: str) -> str:
    return SKILLS.get(skill, ("Other", []))[0]
