# Academic Assignment Helper & Plagiarism Detector (RAG-Powered)

This repository contains the complete implementation for a **RAG-Powered Academic Assignment Helper & Plagiarism Detector**. The system is built with a **FastAPI** backend, **n8n** for workflow orchestration, **PostgreSQL with pgvector** for data and vector storage, and is fully containerized using **Docker Compose**.

As a candidate for the applied backend role, this project demonstrates proficiency in:

* Secure API design (FastAPI + JWT Authentication)[cite: 15].
* Complex automation and data transformation (n8n Workflow)[cite: 6, 39].
* Advanced LLM integration using Retrieval-Augmented Generation (RAG)[cite: 10, 46].
* Database design and vector database implementation (PostgreSQL with `pgvector`)[cite: 68, 105].
* Multi-service orchestration and environment management (Docker Compose)[cite: 13, 112].

---

## 🚀 Key Features

* **Secure Assignment Upload**: Students upload assignments via a JWT-authenticated API endpoint (`POST /upload`)[cite: 5, 15, 31].
* **n8n Workflow Orchestration**: A webhook triggers a multi-step analysis workflow[cite: 6, 40].
* **RAG-Powered Source Suggestions**: The system queries a vector database of academic papers to retrieve relevant context and generate source suggestions using an LLM[cite: 10, 47, 56].
* **AI Analysis**: An LLM (OpenAI/Claude) is used to extract the assignment topic, research questions, and assess the academic level[cite: 49, 52, 53, 54].
* **Plagiarism Detection**: Assignment text is compared against stored academic sources in the vector database to flag potential plagiarism with similarity scores[cite: 11, 59, 60].
* **Structured Storage**: All analysis results, including suggested sources and plagiarism scores, are transformed into structured JSON and stored in PostgreSQL[cite: 12, 63, 64, 86, 89, 90].
* **Secure Authentication**: All core API endpoints are protected with JWT-based authentication for student roles[cite: 15, 17, 18].

---

## 🛠️ Project Components

The application is orchestrated via a `docker-compose.yml` file and consists of the following services[cite: 112, 113]:

| Component            | Technology          | Description                                                                                                                                                                                        |
| :------------------- | :------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Backend**    | FastAPI, Python     | Handles student authentication, assignment file uploads, and retrieval of analysis results (`/upload`, `/analysis/{id}`, `/auth/login`, `/auth/register`)[cite: 20, 21].      |
| **n8n**        | Workflow Automation | Triggers on webhook, handles text extraction, RAG, AI analysis, plagiarism detection, and storage of results[cite: 39, 40].                                                           |
| **PostgreSQL** | Database            | Primary data store for student accounts, assignments, and analysis results[cite: 68]. Includes the `pgvector` extension for storing vector embeddings[cite: 105, 117]. |
| **pgadmin**    | (Optional) GUI      | Web interface for managing the PostgreSQL database[cite: 118].                                                                                                                        |

---

## ⚙️ Setup and Installation

### Prerequisites

* Docker
* Docker Compose

### 1\. Configure Environment Variables

Create a file named `.env` in the root directory (`academic-assignment-helper/`) based on the provided `.env.example`.

```bash
# .env file content
OPENAI_API_KEY=your_key_here
POSTGRES_DB=academic_helper
POSTGRES_USER=student
POSTGRES_PASSWORD=secure_password
JWT_SECRET_KEY=your_jwt_secret
N8N_WEBHOOK_URL=http://n8n:5678/webhook/assignment
```

### 2\. Prepare RAG Data

The **academic\_sources** table requires pre-population with embeddings for the RAG pipeline[cite: 106].

* Run the necessary setup script (not detailed in the specification, but implied by the RAG implementation) to generate embeddings from the data in `data/sample_academic_sources.json` and insert them into the PostgreSQL database[cite: 107, 109, 139].

### 3\. Run the Services

Start all services using Docker Compose:

```bash
docker-compose up --build -d
```

### 4\. Service Access

| Service                   | Access URL                |
| :------------------------ | :------------------------ |
| **FastAPI Backend** | `http://localhost:8000` |
| **n8n Workflow UI** | `http://localhost:5678` |

---

## 💻 API Endpoints

The backend is built with **FastAPI** and requires **JWT authentication** for secured routes[cite: 15].

| Route              | Method   | Security               | Description                                                                                                 |
| :----------------- | :------- | :--------------------- | :---------------------------------------------------------------------------------------------------------- |
| `/auth/register` | `POST` | Open                   | Registers a new student account[cite: 29].                                                     |
| `/auth/login`    | `POST` | Open                   | Validates credentials and returns a JWT[cite: 24, 25].                                         |
| `/upload`        | `POST` | **JWT Required** | Accepts an assignment file, saves it, and triggers the n8n analysis webhook[cite: 31, 37, 38]. |
| `/analysis/{id}` | `GET`  | **JWT Required** | Retrieves the analysis results and suggestions for a specific assignment[cite: 31, 33].        |
| `/sources`       | `GET`  | **JWT Required** | Search academic sources via the RAG pipeline[cite: 32, 34].                                    |

---

## 📂 Project Structure

```
academic-assignment-helper/
├── backend/
│   ├── main.py             # FastAPI application entry point
│   ├── auth.py             # JWT and authentication logic
│   ├── models.py           # Database models and Pydantic schemas
│   ├── rag_service.py      # RAG pipeline implementation (querying pgvector)
│   ├── Dockerfile
│   └── requirements.txt
├── workflows/
│   └── assignment_analysis_workflow.json  # Exported n8n workflow
├── data/
│   └── sample_academic_sources.json       # Source data for RAG database
├── docker-compose.yml                     # Multi-service orchestration
├── .env.example
└── README.md
```

---

## 🧠 Technical Documentation Highlights

Detailed technical documents covering the following aspects are available[cite: 169]:

### RAG Pipeline Architecture [cite: 170]

1. **Ingestion**: Academic source text chunks are transformed into vector **embeddings** using **OpenAI's `text-embedding-ada-002`** and stored in the `academic_sources` table in PostgreSQL (via `pgvector`)[cite: 103, 107, 109].
2. **Query Processing**: An incoming assignment's text is converted to a vector embedding[cite: 110].
3. **Context Retrieval**: A **similarity search** is performed against the `academic_sources` table to retrieve the **Top-k** most relevant documents, which are then passed to the LLM as context[cite: 111].

### Security Implementation [cite: 170]

* **Authentication**: JWT (JSON Web Token) is implemented for all secure endpoints[cite: 15, 18].
* **Authorization**: On login, a JWT is issued with student role permissions[cite: 17].
* **Sensitive Data**: Passwords are stored as `password_hash` in the `students` table[cite: 73].

### Database Schema Reasoning [cite: 170]

* The schema is normalized across four tables (`students`, `assignments`, `analysis_results`, `academic_sources`)[cite: 69, 70, 77, 86, 95].
* `analysis_results` uses **JSONB** for `suggested_sources` and `flagged_sections` to provide flexible storage for AI-generated and structured data[cite: 89, 91].
* `academic_sources` includes an `embedding VECTOR(1536)` column, leveraging `pgvector` for efficient similarity searching required by the RAG and Plagiarism Detection systems[cite: 103].
