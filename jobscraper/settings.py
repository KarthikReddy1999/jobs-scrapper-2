"""
Django settings for jobscraper project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-ev2v8)lpuedaa%r*zbq)+jm3z8omymu%pox)rd1*+sn5hxqn)s",
)

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "jobs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "jobscraper.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "jobscraper.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 60,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ALLOWED_ATS = [
    "greenhouse.io",
    "lever.co",
    "myworkdayjobs.com",
    "myworkdaysite.com",
    "ashbyhq.com",
    "smartrecruiters.com",
    "bamboohr.com",
    "icims.com",
    "jobvite.com",
    "taleo.net",
    "oraclecloud.com",
    "successfactors.com",
    "pinpointhq.com",
    "amazon.jobs",
    "careers.microsoft.com",
]

MAX_PAGES_PER_KEYWORD = 40

KEYWORDS = [
    # Software & Development
    "Software engineer",
    "Software developer",
    "Backend developer",
    "Full stack developer",
    "Frontend developer",
    "Platform engineer",
    "System engineer",
    "Java backend developer",
    "Java developer",
    "iOS developer",
    "Android developer",
    "React native developer",
    "Python developer",
    "Python engineer",
    "React developer",
    "React engineer",
    "Node.js developer",
    "Golang developer",
    "Go developer",
    "Rust developer",
    "C++ developer",
    "C# developer",
    "Angular developer",
    "Vue developer",
    "Typescript developer",
    "Javascript developer",
    "Web developer",
    "Mobile developer",
    "Microservices engineer",
    "API developer",
    "Game developer",
    "Unity developer",
    "Blockchain developer",
    "Robotics engineer",
    "Graphics engineer",
    "Embedded systems engineer",
    "Firmware engineer",
    "Hardware engineer",
    ".NET developer",
    "Power Platform developer",
    # Cloud & DevOps
    "Cloud engineer",
    "Devops engineer",
    "Cloud developer",
    "Site reliability engineer",
    "AWS DevOps engineer",
    "AWS Java developer",
    "Infrastructure engineer",
    "Kubernetes engineer",
    "Terraform engineer",
    "Platform operations engineer",
    "Observability engineer",
    "DevSecOps engineer",
    # Data & AI
    "Data analyst",
    "Data engineer",
    "Data science",
    "Machine learning engineer",
    "AI engineer",
    "Gen AI",
    "Analytics engineer",
    "Business intelligence analyst",
    "ETL developer",
    "SQL developer",
    "MLOps engineer",
    "LLMOps engineer",
    "Prompt engineer",
    "LLM engineer",
    "Applied AI engineer",
    "Generative AI engineer",
    "AI infrastructure engineer",
    "Computer vision engineer",
    "NLP engineer",
    "Research engineer",
    "Applied scientist",
    "Research scientist",
    "AI research engineer",
    "Reinforcement learning engineer",
    "Data platform engineer",
    "Data governance analyst",
    "Streaming engineer",
    "Database administrator",
    "Database engineer",
    "Tableau developer",
    "Power BI developer",
    "Big data engineer",
    # Security
    "Security engineer",
    "Cybersecurity analyst",
    "Security analyst",
    "Application security engineer",
    "Network security engineer",
    "Information security analyst",
    "AI safety engineer",
    # QA & Testing
    "QA engineer",
    "Test engineer",
    "Automation test engineer",
    "QA analyst",
    "SDET",
    "Quality engineer",
    "Quality control",
    # Infrastructure & Networking
    "Network engineer",
    "Systems administrator",
    "IT support engineer",
    "Technical support engineer",
    # Product & Design
    "Product manager",
    "Product owner",
    "Product analyst",
    "UI designer",
    "UX designer",
    "UI UX designer",
    "Product designer",
    "Engineering manager",
    "Program manager",
    "Project manager",
    "Technical program manager",
    "AI product manager",
    # Customer & Solutions
    "Solutions engineer",
    "Solutions architect",
    "Cloud solutions architect",
    "Forward deployed engineer",
    "Customer success engineer",
    "Implementation engineer",
    "Integration engineer",
    "Technical account manager",
    "Sales engineer",
    "Developer advocate",
    "Developer relations engineer",
    # Business & Operations
    "Business analyst",
    "Finance analyst",
    "Risk analyst",
    "Finance manager",
    "Marketing manager",
    "Marketing analyst",
    "Supply chain",
    "Supply chain manager",
    "Supply chain analyst",
    "Revenue operations analyst",
    "Growth analyst",
    # SAP & Salesforce & ERP
    "SAP developer",
    "SAP",
    "SAP MM",
    "SAP EWM",
    "Salesforce developer",
    "Salesforce administrator",
    "ServiceNow developer",
    "Workday consultant",
    "Oracle developer",
    # Quantitative & Finance Tech
    "Quantitative analyst",
    "Quantitative developer",
    "Quantitative researcher",
    # Healthcare & Life Sciences
    "Clinical research scientist",
    "Drug safety associate",
    "Clinical data analyst",
    "Health informatics analyst",
    "Biomedical engineer",
    "Healthcare data analyst",
    "Clinical trial manager",
    "Pharmacovigilance analyst",
    "Medical device engineer",
    "Regulatory affairs specialist",
    "Bioinformatics engineer",
    "Computational biologist",
    "Genomics data scientist",
    # Allied Health
    "Physical therapist",
    "Occupational therapist",
    "Speech language pathologist",
    "Radiologic technologist",
    "Medical laboratory scientist",
    # Civil & Construction
    "Civil engineer",
    "Construction engineer",
    "Structural engineer",
    "Geotechnical engineer",
    "Transportation engineer",
    "Environmental engineer",
    "Urban planner",
    "Construction manager",
    # Mechanical & Manufacturing
    "Mechanical engineer",
    "Manufacturing engineer",
    "Process engineer",
    "Industrial engineer",
    "Automation engineer",
    "Materials engineer",
    "Thermal engineer",
    "HVAC engineer",
    "Tooling engineer",
    # Electronics & Electrical
    "Electrical engineer",
    "Electronics engineer",
    "FPGA engineer",
    "PCB designer",
    "Power electronics engineer",
    "Signal processing engineer",
    "RF engineer",
    "Semiconductor engineer",
    "VLSI engineer",
    "Photonics engineer",
    # Aerospace & Defense
    "Aerospace engineer",
    "Avionics engineer",
    "Propulsion engineer",
    "Flight software engineer",
    "Autonomous systems engineer",
    # HR & People Operations
    "HR analyst",
    "Human resources analyst",
    "People operations manager",
    "Talent acquisition specialist",
    "Recruiter",
    "Compensation analyst",
    "HR business partner",
    "Workforce analyst",
    "Learning development specialist",
    # Geospatial
    "Geospatial engineer",
    "GIS developer",
    "GIS analyst",
]

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "scraper.log",
            "formatter": "verbose",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "scraper": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
