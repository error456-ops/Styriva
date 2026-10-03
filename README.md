# STYRIVA

**AI Styling Concierge — Turn your wardrobe into personalized looks.**

STYRIVA is an AI-powered personal styling platform that helps users create personalized outfit recommendations based on their clothes, occasion, visual vibe, and weather.

Instead of simply suggesting individual clothing items, STYRIVA analyzes the user's available choices and creates a complete, coordinated look.

## ✨ What STYRIVA Does

Users provide their styling preferences and upload clothing options. STYRIVA then uses AI-powered analysis to determine the most suitable combination.

### Core flow

```text
User Input
    ↓
Clothing Images
    ↓
Vision Analysis
    ↓
Outfit Combinations
    ↓
Style Scoring
    ↓
AI Stylist
    ↓
Best Look
```

## 🧠 AI Styling Pipeline

STYRIVA uses a multi-stage styling pipeline:

1. **Input Module**
   Collects the occasion, vibe, weather, and uploaded clothing.

2. **Vision Analysis**
   Analyzes the uploaded clothing images.

3. **Outfit Combination Engine**
   Generates possible combinations from the user's available pieces.

4. **Outfit Scoring Engine**
   Scores combinations using factors such as:

   * Occasion
   * Vibe
   * Weather
   * Color harmony
   * Formality
   * Season
   * Material
   * Fit balance
   * Style compatibility

5. **AI Stylist**
   Selects and explains the strongest styling recommendation.

6. **Look Rendering**
   Presents the final recommended look to the user.

## 🚀 Features

* AI-powered outfit recommendations
* Clothing image analysis
* Occasion-aware styling
* Weather-aware recommendations
* Visual vibe matching
* Color harmony analysis
* Complete outfit combination
* AI-generated styling explanations
* Style evolution experiments
* Responsive web interface

## 🛠️ Tech Stack

* **Python**
* **Django**
* **OpenCV**
* **OpenAI APIs**
* **HTML**
* **CSS**
* **JavaScript**
* **PostgreSQL** for production
* Custom background job/worker architecture

## 🏗️ Architecture

STYRIVA separates the styling process into dedicated modules so that each stage can be developed and improved independently.

```text
                    ┌─────────────────┐
                    │   User Input    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  Input Module   │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  Vision Model   │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Outfit Engine   │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Scoring Engine  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │   AI Stylist   │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Look Renderer   │
                    └─────────────────┘
```

## 💡 Why STYRIVA?

Most styling tools focus on recommending products to buy.

STYRIVA takes a different approach:

> **Style what you already have.**

The goal is to help users make better use of their existing wardrobe while receiving personalized styling guidance.

## 🔮 Future Plans

STYRIVA is being developed toward a more complete AI styling experience, including:

* Personalized style profiles
* Style history
* Improved visual understanding
* Advanced style evolution
* Personalized wardrobe intelligence
* More sophisticated outfit generation
* Better image-based look visualization

## 📸 Screenshots

*Add screenshots or a short demo here.*

## ⚙️ Running Locally

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/STYRIVA.git
cd STYRIVA
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment variables and configure the required API keys.

Run migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## 🔐 Environment Variables

Never commit API keys or other secrets to GitHub.

Example:

```env
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
DEBUG=True
```

## 📌 Project Status

**STYRIVA is currently under active development.**

The project is evolving from an AI styling prototype into a more complete personal styling platform.

## 👩‍💻 Built By

**Sania Naz**

AI Developer building AI-powered products and experimenting with computer vision, LLMs, and intelligent web applications.

---

**STYRIVA — Your AI Styling Concierge.**
