Here is a structured test report based on the provided Swagger UI screen capture and the copied webpage content for the **Academic Assignment Helper** API.

This report summarizes the endpoints, executed test cases, and their corresponding results.

## API Overview

| Detail | Value |
| :--- | :--- |
| **API Title** | [cite_start]Academic Assignment Helper [cite: 1] |
| **Version** | 0.1.0 |
| **OpenAPI Spec** | OAS 3.1 |
| **Base URL** | `http://localhost:8001/` |
| **Main Sections** | [cite_start]Authentication, Assignment Upload, Analysis Results, default [cite: 2, 3, 4, 5] |

---

## Endpoint Test Results

### 1. Root Health Check

| Detail | Value |
| :--- | :--- |
| **Endpoint** | [cite_start]**GET** `/` (Root) [cite: 5] |
| **Description** | Simple health-check endpoint to verify server is running. |
| **Request URL** | `http://localhost:8001/` |
| **Execution Status** | Successful |
| **Response Code** | **200** |
| **Response Body** | [cite_start]`{"message": "Backend running —> Academic Assignment Helper"}` [cite: 11] |

---

### 2. Authentication

#### A. Register Student

| Detail | Value |
| :--- | :--- |
| **Endpoint** | **POST** `/auth/register` |
| **Description** | Register Student |
| **Request Body** | `{"email": "afritioalberts1216@gmail.com", "password": "nati123", "full_name": "Natinael Samuel", "student_id": "WCU13d/1366"}` |
| **Execution Status** | Successful |
| **Response Code** | **200** |
| **Response Body** | `{"id": 4, "email": "afritioalberts1216@gmail.com", "full_name": "Natinael Samuel"}` |

#### B. Login

| Detail | Value |
| :--- | :--- |
| **Endpoint** | **POST** `/auth/login` |
| **Description** | Login |
| **Request Body** | `username=afritioalberts1216@gmail.com`, `password=nati123` (using `application/x-www-form-urlencoded`) |
| **Execution Status** | Successful |
| **Response Code** | **200** |
| **Response Body** | Contains `access_token` (JWT) and `"token_type": "bearer"` |

---

### 3. Assignment Upload

| Detail | Value |
| :--- | :--- |
| **Endpoint** | **POST** `/upload/` |
| **Description** | [cite_start]Upload Assignment [cite: 3] |
| **Request Body** | File: `The Role of Quantum Computing in Accelerating Drug Discovery and Materials Science.pdf` (using `multipart/form-data`) |
| **Authorization** | **Bearer Token** (Required and used) |
| **Execution Status** | Successful (Upload & Processing Started) |
| **Response Code** | **201** |
| **Response Body** | `{"message": "Assignment uploaded successfully and processing started.", "assignment_id": 15, "file_path": "/app/data/uploads/The Role of Quantum Computing in Accelerating Drug Discovery and Materials Science.pdf"}` |

---

### 4. Analysis Results

#### A. Get Analysis

| Detail | Value |
| :--- | :--- |
| **Endpoint** | **GET** `/analysis/{assignment_id}` |
| **Description** | [cite_start]Return latest analysis result or status. [cite: 4] |
| **Path Parameter** | `assignment_id = 15` |
| **Authorization** | **Bearer Token** (Required and used) |
| **Execution Status** | Successful |
| **Response Code** | **200** |
| **Response Body** | Detailed Analysis Report: |
| | - `status`: `"done"` |
| | - `plagiarism_score`: `75.12` |
| | - `flagged_sections`: Contains a section with `similarity: 0.7512` and `source_title: Quantum Machine Learning for Drug Discovery` |
| | - `suggested_sources`: Includes `Quantum Machine Learning for Drug Discovery` |
| | - `research_suggestions`: Provides four points of research guidance. |
| | - `citation_recommendations`: Includes `Quantum Computing in Chemistry: Progress and Challenges`, etc. |

#### B. Run Analysis Manual (Trigger RAG)

| Detail | Value |
| :--- | :--- |
| **Endpoint** | **POST** `/analysis/run/{assignment_id}` |
| **Description** | Allow manual RAG analysis trigger. |
| **Path Parameter** | `assignment_id = 14` |
| **Authorization** | **Bearer Token** (Required and used) |
| **Execution Status** | Failed (Expected Assignment Not Found) |
| **Response Code** | **404** (Undocumented in success schema) |
| **Response Body** | `{"detail": "Assignment not found"}` |

#### C. Embed Sources Endpoint

| Detail | Value |
| :--- | :--- |
| **Endpoint** | **POST** `/analysis/embed-sources` |
| **Description** | Manually regenerate embeddings for academic sources. |
| **Execution Status** | Successful |
| **Response Code** | **200** |
| **Response Body** | `{"message": "Embedding process completed."}` |

#### D. Create Vector Index

| Detail | Value |
| :--- | :--- |
| **Endpoint** | **POST** `/analysis/index-sources` |
| **Description** | Create pgvector index for academic sources. |
| **Execution Status** | Successful |
| **Response Code** | **200** |
| **Response Body** | `{"message": "Vector index created or already exists."}` |

#### E. Search Similar Academic Sources

| Detail | Value |
| :--- | :--- |
| **Endpoint** | **GET** `/analysis/search-similar` |
| **Description** | Search semantically similar academic sources. |
| **Query Parameters** | `query = Machine learning models enable personalized learning experiences`, `top_k = 3` |
| **Authorization** | **Bearer Token** (Required and used) |
| **Execution Status** | Successful (No results found for the query) |
| **Response Code** | **200** |
| **Response Body** | `{"results": []}` |

---

## API Schemas Summary

The Swagger documentation defines several key data schemas:

* **StudentCreate**: Used for registration, includes `email`, `password`, `full_name`, and `student_id`.
* **StudentOut**: Used in a successful registration response, includes `id`, `email`, and `full_name`.
* **Token**: Used for successful login response, includes `access_token` and `token_type` (bearer).
* **HTTPValidationError** / **ValidationError**: Standard schemas for 422 responses, providing details on location (`loc`), message (`msg`), and type (`type`) of the validation error.
* **Body\_upload\_assignment\_upload\_\_post**: Defines the file field (`file`) for the assignment upload endpoint, expected as a binary string.