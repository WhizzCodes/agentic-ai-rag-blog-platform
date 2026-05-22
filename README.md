# Agentic AI RAG Blogging Platform

An AI-powered blogging platform built using Flask, LangChain, Gemini LLMs, FAISS, and MySQL featuring Agentic AI workflows, semantic search, PDF-aware Retrieval-Augmented Generation (RAG), and intelligent blog generation using live web research and uploaded documents.

---

# Features

* AI-powered blog generation using Gemini LLMs
* Agentic AI workflows for autonomous research and summarization
* Google Search API + DuckDuckGo Search integration
* Retrieval-Augmented Generation (RAG) using uploaded PDFs
* Semantic search using FAISS vector database
* HuggingFace embeddings for contextual retrieval
* AI-assisted blog reframing and SEO optimization
* User authentication and session management
* CRUD operations for blog management
* Responsive Flask + MySQL full-stack architecture

---

# Technologies Used

* Python
* Flask
* MySQL
* LangChain
* Gemini API
* FAISS Vector Database
* HuggingFace Embeddings
* Google Search API
* DuckDuckGo Search
* HTML / CSS / Bootstrap

---

# How to Run Locally

## Step 1 — Clone Repository

```bash
git clone https://github.com/your-username/agentic-ai-rag-blog-platform.git
```

---

## Step 2 — Open Project Folder

```bash
cd agentic-ai-rag-blog-platform
```

---

## Step 3 — Create Virtual Environment

```bash
python -m venv venv
```

Activate virtual environment:

### Windows

```bash
venv\Scripts\activate
```

### Mac/Linux

```bash
source venv/bin/activate
```

---

## Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Database Setup (XAMPP)

## Step 5 — Start XAMPP

Open XAMPP Control Panel and start:

* Apache
* MySQL

---

## Step 6 — Open phpMyAdmin

Open:

```text
http://localhost/phpmyadmin/
```

---

## Step 7 — Create Database

Create a database named:

```text
pythonca2
```

---

## Step 8 — Import Database

Import SQL file from:

```text
import db/pythonca2.sql
```

---

# Environment Variables Setup

## Step 9 — Create .env File

Create a file named:

```text
.env
```

Add the following variables:

```env
GEMINI_API_KEY=your_gemini_api_key

GOOGLE_SEARCH_API_KEY=your_google_search_api_key

GOOGLE_SEARCH_ENGINE_ID=your_google_search_engine_id

MAIL_USERNAME=your_email@gmail.com

MAIL_PASSWORD=your_app_password

SECRET_KEY=your_secret_key

DATABASE_URL=mysql+pymysql://root:@localhost/pythonca2
```

---

# Run Application

## Step 10 — Start Flask Server

```bash
python app.py
```

---

## Step 11 — Open Application

Open browser and visit:

```text
http://127.0.0.1:5000/
```

---

# AI Features

## Generate with AI

Creates blogs using Gemini LLMs.

## Research Agent

Performs live web research using DuckDuckGo Search and generates context-aware blogs.

## Google Agent

Uses Google Search API for real-time information retrieval and blog generation.

## RAG Agent

Uses uploaded PDFs with semantic retrieval and FAISS vector search to generate context-grounded content.

---

# Project Architecture

* Flask Backend API
* MySQL Database
* LangChain Orchestration
* FAISS Vector Store
* HuggingFace Embeddings
* Gemini LLM Integration
* Semantic Retrieval Pipelines
* Agentic AI Workflows
* Retrieval-Augmented Generation (RAG)

---

# Author

Developed by Preeti Guin
