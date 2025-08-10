# Life Coach GPT 🌱

**Live Demo:** [https://lifecoachgpt-mcp.onrender.com](https://lifecoachgpt-mcp.onrender.com)  
**Hackathon:** Puch AI Hackathon 🚀  

Life Coach GPT is your **AI-powered personal life coach** — offering personalized advice, motivation, and actionable guidance to help you grow in different areas of life, including career, health, relationships, and personal development.

Built using **Gemini 2.0 API** and deployed on **Render**, this app delivers a conversational experience that’s intuitive, supportive, and available 24/7.

---

## ✨ Features

- 🧠 **AI-Powered Conversations** — Powered by Google’s Gemini 2.0 API for natural, empathetic responses.
- 🎯 **Personalized Advice** — Tailored suggestions based on your goals and challenges.
- ⏳ **Real-Time Interaction** — Get instant responses without page reloads.
- 🌐 **Fully Deployed** — Accessible online for anyone.
- 🛠 **Custom Backend** — Handles API calls securely using environment variables.
- 📱 **Responsive UI** — Works on desktop and mobile.

---

## 🚀 How It Works

1. **User enters a query** (e.g., “I’m feeling unmotivated, what should I do?”).
2. The **frontend** sends the request to the backend.
3. The **backend** calls the Gemini 2.0 Flash API securely using your API key.
4. The AI processes the query and returns a **supportive, actionable response**.
5. The user receives **instant, human-like guidance**.

---

## 🛠 Tech Stack

- **Frontend:** HTML, CSS, JavaScript (FastAPI templating)
- **Backend:** Python (FastAPI)
- **AI Model:** Google Gemini 2.0 Flash API
- **Deployment:** Render
- **Version Control:** Git + GitHub

---

## 📂 Project Structure

life-coach-gpt/
│
├── app.py # FastAPI app entry point
├── main.py # Gemini API integration logic
├── templates/ # HTML templates
├── static/ # CSS and JavaScript files
├── requirements.txt # Python dependencies
├── .env # Environment variables (not pushed to GitHub)
└── README.md # Project documentation


## ⚡ Local Setup

1️⃣ Clone the repo
```bash
git clone https://github.com/Asharu369/-lifecoachgpt-mcp.git
cd life-coach-gpt

2️⃣ Create a virtual environment
bash
Copy code
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows

3️⃣ Install dependencies
bash
Copy code
pip install -r requirements.txt
4️⃣ Add environment variables
Create a .env file in the root folder:

GEMINI_API_KEY=your_gemini_api_key_here
BACKEND_URL=http://127.0.0.1:8000

5️⃣ Run the app
uvicorn app:app --reload

Visit http://127.0.0.1:8000 in your browser.

🌍 Deployment
The app is deployed on Render.
You can try it live here:
🔗 https://lifecoachgpt-mcp.onrender.com

📜 License
This project is licensed under the MIT License — feel free to use and adapt it.

🙌 Acknowledgments
Google AI — For Gemini API.

FastAPI — For an awesome Python web framework.

Render — For free and easy deployment.

Puch AI Hackathon — For providing the platform to innovate.