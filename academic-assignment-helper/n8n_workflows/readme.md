# **📚 Academic Assignment Helper System Documentation (n8n)**

This document describes a two-part automated workflow designed to handle academic assignment submissions securely and reliably. The system ensures files are processed correctly, students are given a unique submission link, and instructors receive the final, validated assignment with full logging of the delivery status.

## **System Overview**

The entire process is separated into two sequential workflows:

| Workflow | Primary Goal | Entry Point | Output Trigger |
| :---- | :---- | :---- | :---- |
| **Flow 1 (Initial Processing)** | Receive file, extract content, and prepare data for the next phase (e.g., Plagiarism Analysis). | Webhook (/assignment) | HTTP Request (Triggers Flow 2\) |
| **Flow 2 (Submission & Logging)** | Generate unique student link, receive final submission, email instructor, notify student, and log results. | Webhook (/notify-analysis-done) & Form Webhook | Database Insert |

## **1\. Flow 1: Initial File Processing and Content Extraction**

**Goal:** Receive the raw submission details, retrieve the physical file, extract its text content, and trigger the next system phase (e.g., Plagiarism Analysis or Link Generation).

| Node Name | Type | Key Action | Configuration Notes |
| :---- | :---- | :---- | :---- |
| **Webhook** | Webhook | **Entry Point:** Starts the workflow upon receiving a new assignment submission payload. | Configured to listen on the /assignment path and expects data like filename, student\_id, etc. |
| **Read/Write Files from Disk** | File System | **File Retrieval:** Reads the physical assignment file using the path provided in the webhook payload. | **File Selector:** \=/app/data/uploads/{{ $json.body.filename }}. |
| **If** | If | **Conditional Branching:** Determines the file type to choose the correct content extraction method. | Condition likely checks if the filename ends with .docx. |
| **DOCX to Text (Path: True)** | DOCX to Text | **DOCX Conversion:** If the file is a DOCX, converts the binary data into clean, readable text. | Essential for accurate extraction from Microsoft Word files. |
| **Extract from File (Path: False)** | File Extraction | **Generic Extraction:** Handles all other file types (e.g., PDF, TXT) by attempting to extract text content directly. | Used as a fallback for simpler formats. |
| **Merge** | Merge (Combine) | **Data Consolidation:** Combines the data stream from the two conditional branches back into a single item stream. | Ensures the subsequent HTTP Request receives one consistent payload. |
| **HTTP Request** | HTTP Request | **Final Trigger:** Sends the processed assignment data (including extracted text and file path) to trigger **Flow 2**. | This URL must point to the Webhook URL of Flow 2\. |

## **2\. Flow 2: Link Generation, Final Submission, and Logging**

This flow is divided into two distinct parts: **Phase 1: Link Generation** (triggered by Flow 1\) and **Phase 2: Submission Handling** (triggered by the student).

### **Phase 1: Link Generation and Student Notification**

**Triggered by:** HTTP Request from **Flow 1**.

| Node Name | Type | Key Action |
| :---- | :---- | :---- |
| **Webhook (notify-analysis-done)** | Webhook | Starts the flow upon receiving analyzed assignment metadata (including plagiarism\_score). |
| **Generate Form URL & Prepare DB Data** | Function | **Core Logic:** Generates a unique, secure token and constructs the student-facing submission URL (BASE\_URL?token=UNIQUE\_TOKEN). |
| **Set Form URL** | Set | Extracts the final, ready-to-use form URL. |
| **Insert row1** | Database Insert | **Database Write:** Saves the unique token, assignment details, and student info into the assignment\_form\_links tracking table. |
| **Edit Fields3** | Set | Configures the email fields for the student notification. |
| **Send email** | Email | Sends the student an email containing the **unique form submission URL**. |

### **Phase 2: Submission Handling and Logging**

**Triggered by:** Student clicking the unique form URL and submitting.

| Node Name | Type | Key Action |
| :---- | :---- | :---- |
| **Form Webhook Trigger** | Webhook | Receives the student submission payload, including the unique token. |
| **Prepare Token for Retrieval** | Function | Extracts the token from the webhook parameters. |
| **Select Assignment Details** | Database Read | **Database Read:** Retrieves the full student record and file details from the tracking database using the token. |
| **Split Out1** | Split Out | Prepares data for parallel processing. |
| **Generate Instructor Email** | Function | Creates the To, Subject, and highly stylized HTML Body for the instructor, including the submission testimonial and plagiarism score. |
| **Set Email Fields** | Set | Finalizes the email parameters. |
| **Read File** | Read Binary | Reads the actual assignment file from the specified storage path (using the filename retrieved from the database). |
| **Merge1** | Merge (Combine) | **CRITICAL:** Combines the JSON email item and the Binary file item (data) into a **single output item** required for the Email Send node. |
| **Send email to instructor** | Email | Sends the final submission email **with the file attached** to the instructor. Outputs the delivery status ($json.response). |
| **Email Succeeded?** | IF | Checks for successful email delivery: {{ $json.response }} starts with 250 2.0.0. |
| **SUCCESS BRANCH (Logging & Notification)** |  |  |
| **Merge2** | Merge (Append) | Temporarily combines student data (Item 0\) and the email response (Item 1). |
| **Email Sent Successfully** | Function | Formats and prepares the positive success notification email to the student. |
| **Send email1** | Email | Sends the final submission success confirmation to the student. |
| **Prepare Log Record** | Function | **Logging Logic:** Combines data from both merged items into a clean log\_submission\_record object. |
| **Insert row1** | Database Insert | **Database Write:** Inserts the final log\_submission\_record into the dedicated log\_submission table for auditing. |

## **3\. Database Requirements**

The system requires two dedicated data tables:

1. **assignment\_form\_links (Tracking Table):** Stores initial data and the generated unique token.  
2. **log\_submission (Logging Table):** Stores the outcome of every final submission attempt for auditing.