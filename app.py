from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import redirect
from openai import OpenAI
from google import genai
import os
from dotenv import load_dotenv
from ddgs import DDGS
import requests
import pymysql

from werkzeug.utils import secure_filename
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

app = Flask(__name__)

# Upload Folder Config
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

load_dotenv()
# API KEY LOAD
gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Mail Config
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD")
)
mail = Mail(app)

# Secret Key
app.secret_key = os.getenv("SECRET_KEY")
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
db = SQLAlchemy(app)

# Uploads list
uploaded_pdfs = []

# ================= MODELS =================

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    msg = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(12), nullable=True)

# ================= Function for DDGS (DuckDuckGO) engine =================

def research_topic(topic):
    research_results = []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(topic, max_results=5))

            print("Search Results:", results)

            for result in results:
                research_results.append({
                    "title": result.get("title"),
                    "body": result.get("body"),
                    "link": result.get("href")
                })

    except Exception as e:
        print("Search Error:", e)

    return research_results

# ================= Function for PDF Processing =================

def create_vector_store(pdf_path):

    try:

        print("Loading PDF...")

        loader = PyPDFLoader(pdf_path)

        docs = loader.load()

        print("PDF Loaded")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        chunks = splitter.split_documents(docs)

        print("Chunks Created")

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        print("Embeddings Ready")

        vector_db = FAISS.from_documents(
            chunks,
            embeddings
        )

        print("FAISS Created")

        # CREATE FOLDER IF NOT EXISTS
        os.makedirs("vectorstore", exist_ok=True)

        vector_db.save_local("vectorstore")

        print("Vectorstore Saved Successfully")

        return True

    except Exception as e:

        import traceback
        traceback.print_exc()

        return False

# ================= Function for Retrieval =================

def search_pdf_content(query):

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Load vector DB
    db = FAISS.load_local(
        "vectorstore",
        embeddings,
        allow_dangerous_deserialization=True
    )

    # Search similar chunks
    results = db.similarity_search(
        query,
        k=3
    )

    return results

# ================= Function for Google search engine =================

def google_search_topic(topic):
    search_results = []

    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": topic
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        print(data)

        items = data.get("items", [])

        for item in items[:5]:
            search_results.append({
                "title": item.get("title"),
                "body": item.get("snippet"),
                "link": item.get("link")
            })

    except Exception as e:
        print("Google Search Error:", e)

    return search_results

# ================= ROUTES =================

@app.route('/')
def home():
    posts = Posts.query.order_by(Posts.id.desc()).limit(5).all()
    return render_template("home.html", posts=posts)


# 🔹 SIGNUP
@app.route('/signup/', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip()
        password = request.form.get('psw')
        cpassword = request.form.get('cpsw')

        if not name or not email or not password:
            return "All fields are required!"

        if password != cpassword:
            return "Passwords do not match!"

        if len(password) < 6:
            return "Password must be at least 6 characters!"

        user = Users.query.filter_by(email=email).first()
        if user:
            return "Email already exists!"

        entry = Users(name=name, email=email, password=password, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        return redirect('/user-login/')

    return render_template("signup.html")


@app.route('/about/')
def about():
    return render_template("about.html")


# 🔹 CONTACT
@app.route('/contact/', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        content = request.form.get('content')

        entry = Contact(name=name, email=email, msg=content, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        mail.send_message(
            'New message from ' + name,
            sender=email,
            recipients=['guin.preeti.19bsd010@gmail.com'],
            body=content
        )

    return render_template("contact.html")


# 🔹 BLOG VIEW
@app.route('/blogs/<string:post_slug>')
def blogs_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("blogs.html", post=post)


# ================= ADMIN =================

@app.route('/dashboard/', methods=['GET', 'POST'])
def dashboard():
    if "user" in session and session['user'] == 'preeti':
        posts = Posts.query.all()
        return render_template("dashboard.html", posts=posts)

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "preeti" and password == "guin":
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", posts=posts)

    return render_template("login.html")


# ================= USER LOGIN =================

@app.route('/user-login/', methods=['GET', 'POST'])
def user_login():

    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')

        if not email or not password:
            return "All fields are required!"

        user = Users.query.filter_by(email=email).first()

        if user:
            if user.password == password:
                session['user'] = user.email
                return redirect('/user-dashboard/')
            else:
                return "Incorrect password!"
        else:
            return "User not found!"

    return render_template("user_login.html")


# ================= USER DASHBOARD =================

@app.route('/user-dashboard/')
def user_dashboard():
    if 'user' not in session:
        return redirect('/user-login/')

    user = Users.query.filter_by(email=session['user']).first()
    posts = Posts.query.filter_by(user_id=user.id).all()

    return render_template("user_dashboard.html", user=user, posts=posts)


# ================= ADD / EDIT =================

@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def edit(id):

    if 'user' not in session:
        return redirect('/user-login/')

    user = Users.query.filter_by(email=session['user']).first()

    if request.method == "POST":
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')

        if id == '0':
            post = Posts(
                title=title,
                slug=slug,
                content=content,
                date=datetime.now(),
                user_id=user.id
            )
            db.session.add(post)
            db.session.commit()
            return redirect('/user-dashboard/')

        else:
            post = Posts.query.filter_by(id=id).first()

            if post.user_id != user.id:
                return "Not allowed!"

            post.title = title
            post.slug = slug
            post.content = content
            db.session.commit()

            return redirect('/user-dashboard/')

    post = Posts.query.filter_by(id=id).first()
    return render_template("edit.html", id=id, post=post)

# ================= Gen AI Blog =================

@app.route('/generate-blog-ai/', methods=['POST'])
def generate_blog_ai():

    if 'user' not in session:
        return redirect('/user-login/')

    topic = request.form.get("topic")
    post_id = request.form.get("post_id", "0")

    if not topic:
        return "Please enter a topic"

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            Write a professional blog article on: {topic}

            Strictly return output in this format:

            Title: <generated title>

            Content:
            <blog content only>
            """
        )

        generated_text = response.text

        # Split title and content
        ai_title = topic
        ai_content = generated_text

        if "Content:" in generated_text:
            parts = generated_text.split("Content:", 1)

            title_part = parts[0].replace("Title:", "").strip()
            content_part = parts[1].strip()

            ai_title = title_part
            ai_content = content_part

        generated_slug = ai_title.lower().replace(" ", "-")

        return render_template(
            "edit.html",
            id=post_id,
            uploaded_pdfs=uploaded_pdfs,
            post={
                "title": ai_title,
                "slug": generated_slug,
                "content": ai_content
            }
        )

    except Exception as e:
        print(e)
        return "AI service busy. Please try again later."

# ================= Reframe with AI Option =================

@app.route('/reframe-blog-ai/', methods=['POST'])
def reframe_blog_ai():

    if 'user' not in session:
        return redirect('/user-login/')

    post_id = request.form.get("post_id")
    title = request.form.get("title")
    slug = request.form.get("slug")
    content = request.form.get("content")

    if not content:
        return "Please enter content first"

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            Rewrite and improve this blog content.
            Make it professional and engaging.

            {content}
            """
        )

        reframed_content = response.text

        return render_template(
            "edit.html",
            id=post_id,
            uploaded_pdfs=uploaded_pdfs,
            post={
                "title": title,
                "slug": slug,
                "content": reframed_content
            }
        )

    except Exception as e:
        print(e)
        return "AI service busy. Try again later."

# ================= Agentic AI =================

# ================= Agent using DDGS =================
@app.route('/research-blog-agent/', methods=['POST'])
def research_blog_agent():

    if 'user' not in session:
        return redirect('/user-login/')

    topic = request.form.get("topic")
    post_id = request.form.get("post_id", "0")

    if not topic:
        return "Please enter topic"

    try:
        # Step 1: Search latest information
        search_results = research_topic(topic)

        if not search_results:
            return "No research results found."

        research_data = ""

        for result in search_results:
            research_data += f"""
            Article Title: {result['title']}
            Summary: {result['body']}
            Source: {result['link']}
            
            """

        print(research_data)

        # Step 2: Ask Gemini to process research
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            You are an autonomous blog research agent.

            Topic:
            {topic}

            Latest research data:
            {research_data}

            Your tasks:
            1. Analyze research
            2. Summarize latest findings
            3. Write professional blog
            4. Generate SEO title
            5. Generate meta description
            6. Generate blog tags

            Return strictly in this format:

            Title: <blog title>

            Meta Description:
            <meta description>

            Tags:
            <comma separated tags>

            Content:
            <full blog content>
            """
        )

        agent_output = response.text

        # Parse title/content
        ai_title = topic
        ai_content = agent_output

        if "Content:" in agent_output:
            parts = agent_output.split("Content:", 1)

            title_part = parts[0]
            content_part = parts[1]

            if "Title:" in title_part:
                ai_title = title_part.split("Title:")[1].split("Meta Description:")[0].strip()

            ai_content = content_part.strip()

        generated_slug = ai_title.lower().replace(" ", "-")

        return render_template(
            "edit.html",
            id=post_id,
            uploaded_pdfs=uploaded_pdfs,
            post={
                "title": ai_title,
                "slug": generated_slug,
                "content": ai_content
            }
        )

    except Exception as e:
        print(e)
        return "Research Agent failed. Try again later."

# ================= Agent using Google =================

@app.route('/google-blog-agent/', methods=['POST'])
def google_blog_agent():

    if 'user' not in session:
        return redirect('/user-login/')

    topic = request.form.get("topic")
    post_id = request.form.get("post_id", "0")

    if not topic:
        return "Please enter topic"

    try:
        # Step 1: Search Google
        search_results = google_search_topic(topic)

        if not search_results:
            return "No Google search results found."

        research_data = ""

        for result in search_results:
            research_data += f"""
            Article Title: {result['title']}
            Summary: {result['body']}
            Source: {result['link']}
            
            """

        print(research_data)

        # Step 2: Gemini processing
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            You are a Google research AI agent.

            Topic:
            {topic}

            Google search research:
            {research_data}

            Tasks:
            1. Analyze search results
            2. Summarize findings
            3. Write professional blog
            4. Generate SEO title
            5. Generate meta description
            6. Generate blog tags

            Return strictly in this format:

            Title: <blog title>

            Meta Description:
            <meta description>

            Tags:
            <comma separated tags>

            Content:
            <full blog content>
            """
        )

        agent_output = response.text

        ai_title = topic
        ai_content = agent_output

        if "Content:" in agent_output:
            parts = agent_output.split("Content:", 1)

            title_part = parts[0]
            content_part = parts[1]

            if "Title:" in title_part:
                ai_title = title_part.split("Title:")[1].split("Meta Description:")[0].strip()

            ai_content = content_part.strip()

        generated_slug = ai_title.lower().replace(" ", "-")

        return render_template(
            "edit.html",
            id=post_id,
            uploaded_pdfs=uploaded_pdfs,
            post={
                "title": ai_title,
                "slug": generated_slug,
                "content": ai_content
            }
        )

    except Exception as e:
        print(e)
        return "Google Agent failed. Try again later."        

# ================= PDF Upload Route =================

@app.route('/upload-pdf/', methods=['POST'])
def upload_pdf():

    global uploaded_pdfs

    if 'user' not in session:
        return redirect('/user-login/')

    post_id = request.form.get("post_id", "0")
    file = request.files['pdf_file']

    if file.filename == '':
        return "Please select PDF"

    filename = secure_filename(file.filename)

    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    # Save PDF
    file.save(filepath)

    # Add to uploaded list
    if filename not in uploaded_pdfs:
        uploaded_pdfs.clear()
        uploaded_pdfs.append(filename)

    # Process PDF
    success = create_vector_store(filepath)

    if success:

        return render_template(
            "edit.html",
            id=post_id,
            uploaded_pdfs=uploaded_pdfs,
            active_pdf=filename
        )

    else:
        return "PDF processing failed."

# ================= PDF Upload Route =================

@app.route('/rag-blog-agent/', methods=['POST'])
def rag_blog_agent():

    if 'user' not in session:
        return redirect('/user-login/')

    topic = request.form.get("topic")
    post_id = request.form.get("post_id", "0")

    if not topic:
        return "Please enter topic"
        
    # CHECK VECTORSTORE
    if not os.path.exists("vectorstore/index.faiss"):
        return "Please upload PDF first for RAG."    

    try:
        # Retrieve relevant chunks
        docs = search_pdf_content(topic)
        context = ""
        for doc in docs:
            context += doc.page_content + "\n"
        print(context)
        # Generate blog using Gemini
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            You are a RAG AI Blog Writer.
            Use ONLY the following PDF content:
            {context}
            Write a professional blog on:
            {topic}
            Return in this format:
            Title: <title>
            Content:
            <content>
            """
        )

        output = response.text
        ai_title = topic
        ai_content = output

        if "Content:" in output:
            parts = output.split("Content:", 1)
            title_part = parts[0]
            content_part = parts[1]
            if "Title:" in title_part:
                ai_title = title_part.replace(
                    "Title:",
                    ""
                ).strip()

            ai_content = content_part.strip()
        generated_slug = ai_title.lower().replace(" ", "-")
        return render_template(
            "edit.html",
            id=post_id,
            uploaded_pdfs=uploaded_pdfs,
            post={
                "title": ai_title,
                "slug": generated_slug,
                "content": ai_content
            }
        )

    except Exception as e:
        print(e)
        return "RAG Agent failed"

# ================= DELETE =================

@app.route('/delete/<string:id>')
def delete(id):

    if 'user' not in session:
        return redirect('/user-login/')

    user = Users.query.filter_by(email=session['user']).first()
    post = Posts.query.filter_by(id=id).first()

    if post.user_id != user.id:
        return "Not allowed!"

    db.session.delete(post)
    db.session.commit()

    return redirect('/user-dashboard/')


# ================= LOGOUT =================

@app.route('/logout/')
def logout():
    session.clear()
    return redirect('/')


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)