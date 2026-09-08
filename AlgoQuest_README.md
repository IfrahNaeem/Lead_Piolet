# AlgoQuest — AI-Powered DSA Learning Platform

> Learn Data Structures, Algorithms, and LeetCode problem-solving — level by level, like a game. No teacher needed.

---

## What Is AlgoQuest?

AlgoQuest is a full-stack, ML-powered web app that guides students from zero Python knowledge to confidently solving LeetCode problems. It uses adaptive ML to detect skill level, recommend problems, evaluate solutions, and nudge students to the next level — all without a human teacher.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript |
| Styling | Tailwind CSS + Framer Motion |
| Backend | FastAPI (Python) |
| Database | PostgreSQL (via Supabase) |
| Auth | Supabase Auth (JWT) |
| ML Models | scikit-learn + custom heuristics |
| Code Execution | Judge0 API (sandboxed runner) |
| Hosting | Vercel (frontend) + Railway (backend) |
| State | Zustand (client) |

---

## Color Scheme

```
Primary Background:  #0D0F1A  (deep space navy)
Card Surface:        #161929  (dark slate)
Accent Purple:       #7C3AED  (electric violet — primary CTA)
Accent Cyan:         #06B6D4  (neon cyan — highlights, badges)
Success Green:       #10B981  (correct answers, level-up)
Warning Amber:       #F59E0B  (hints, partial credit)
Error Red:           #EF4444  (wrong answer, failed tests)
Text Primary:        #F1F5F9  (near white)
Text Muted:          #94A3B8  (slate 400)
Border:              #1E2940  (subtle card borders)
```

Typography:
- Display: `Space Grotesk` (headings, level names)
- Body: `Inter` (readable, clean)
- Code: `JetBrains Mono` (all code blocks)

---

## App Levels & Roadmap

### 🟢 Beginner
- Python crash course (variables, loops, functions, OOP)
- Basic data structures: Arrays, Strings, HashMaps, Stacks
- 30 hand-picked Easy LeetCode problems
- Visual step-by-step walkthroughs for every problem

### 🔵 Intermediate
- Recursion, Two Pointers, Sliding Window, Binary Search
- Trees, Linked Lists, Queues
- 40 Medium LeetCode problems
- Time/Space complexity analysis for each solution

### 🔴 Advanced
- Graphs (BFS/DFS), Dynamic Programming, Tries, Heaps
- System Design fundamentals
- 30 Hard + real interview problems from top companies
- Mock interview mode with time pressure

---

## ML Features (Where Machine Learning Is Used)

### 1. Adaptive Level Progression
- **Model:** Logistic Regression + sliding window accuracy tracker
- **How:** If a student gets 2–3 consecutive correct answers above a certain quality threshold, the model triggers a "Ready to level up?" suggestion
- **Features used:** accuracy rate, time-to-solve, hint usage count, solution quality score

### 2. Solution Quality Scorer
- **Model:** Rule-based heuristics + TF-IDF pattern matching on code
- **How:** Evaluates student code for time complexity, space complexity, code style, and edge case handling. Returns a score 0–100 and a detailed breakdown
- **Output:** "Your solution is O(n²) — there's an O(n) approach using a HashMap. Score: 63/100"

### 3. Personalized Problem Recommender
- **Model:** Collaborative Filtering (user-based) + content-based fallback
- **How:** Based on what problems similar users solved next, recommends the ideal next problem for the current student
- **Cold start:** Falls back to difficulty-tagged content filtering for new users

### 4. Struggle Detector
- **Model:** Anomaly detection (Isolation Forest on session behavior)
- **How:** If a student spends >15 min on a problem, uses 3+ hints, or submits wrong answers repeatedly, the system proactively surfaces an explanation video and simplified version of the problem

### 5. Hint Personalization
- **Model:** Simple NLP (keyword extraction from student code)
- **How:** Analyzes what the student has written so far and generates a targeted hint, not a generic one

---

## File & Folder Structure

```
algoquest/
├── frontend/                        # Next.js App
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   ├── signup/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── learn/[topic]/page.tsx
│   │   │   ├── problems/page.tsx
│   │   │   ├── problems/[id]/page.tsx
│   │   │   ├── profile/page.tsx
│   │   │   ├── roadmap/page.tsx
│   │   │   └── layout.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx                 # Landing page
│   ├── components/
│   │   ├── ui/                      # Reusable UI primitives
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Progress.tsx
│   │   │   └── Toast.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── SignupForm.tsx
│   │   ├── editor/
│   │   │   ├── CodeEditor.tsx       # Monaco Editor wrapper
│   │   │   ├── TestCasePanel.tsx
│   │   │   └── SolutionFeedback.tsx
│   │   ├── learning/
│   │   │   ├── LessonCard.tsx
│   │   │   ├── ConceptVisualizer.tsx
│   │   │   └── QuizBlock.tsx
│   │   ├── problems/
│   │   │   ├── ProblemCard.tsx
│   │   │   ├── ProblemStatement.tsx
│   │   │   ├── HintPanel.tsx
│   │   │   └── SolutionComparison.tsx
│   │   ├── roadmap/
│   │   │   ├── RoadmapTree.tsx
│   │   │   └── LevelGate.tsx
│   │   └── layout/
│   │       ├── Navbar.tsx
│   │       ├── Sidebar.tsx
│   │       └── LevelBadge.tsx
│   ├── lib/
│   │   ├── supabase.ts
│   │   ├── api.ts                   # API client
│   │   └── store.ts                 # Zustand store
│   ├── types/
│   │   └── index.ts
│   ├── public/
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── package.json
│
├── backend/                         # FastAPI Python backend
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── problems.py
│   │   │   ├── submissions.py
│   │   │   ├── lessons.py
│   │   │   └── ml.py
│   │   ├── models/                  # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── problem.py
│   │   │   ├── submission.py
│   │   │   └── progress.py
│   │   ├── schemas/                 # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── problem.py
│   │   │   └── submission.py
│   │   ├── ml/
│   │   │   ├── scorer.py            # Solution quality scorer
│   │   │   ├── recommender.py       # Problem recommender
│   │   │   ├── level_detector.py    # Level-up trigger logic
│   │   │   ├── struggle_detector.py # Anomaly detection
│   │   │   └── hint_generator.py   # Smart hints
│   │   └── services/
│   │       ├── judge0.py            # Code execution service
│   │       └── progress.py         # Progress tracking
│   ├── requirements.txt
│   ├── Makefile
│   └── Dockerfile
│
├── data/
│   └── problems.json                # Seeded problem bank
│
├── .env.example
├── .gitignore
├── vercel.json
└── README.md
```

---

## Key Pages & Features

### Landing Page `/`
- Hero: animated code snippet typing effect
- "Start for Free" CTA → signup
- Feature highlights, level preview, testimonials

### Signup `/signup`
- Email + password or Google OAuth
- After signup: onboarding quiz (3 questions) → ML assigns starting level

### Login `/login`
- Email/password or Google
- Remember me, forgot password

### Dashboard `/dashboard`
- Current level badge (Beginner / Intermediate / Advanced)
- XP bar and streak counter
- "Continue where you left off" card
- ML recommendation: "Try this next problem"
- Recent submissions with scores

### Learn `/learn/[topic]`
- Lesson content (MDX rendered)
- Embedded code playground for each concept
- Quiz at end of each lesson
- Animated concept visualizer (e.g., how a stack works)

### Problems `/problems`
- Filterable by: level, topic, status (solved/unsolved/attempted)
- Each card shows: difficulty badge, topic tags, your best score, estimated time

### Problem Solver `/problems/[id]`
- Split-pane: Problem statement (left) + Monaco code editor (right)
- Run code against test cases (via Judge0)
- Submit → ML scorer returns: score, complexity rating, best/worst comparison
- Hint system (3 progressive hints, each costs 5 XP)
- "See optimal solution" unlocks after submission

### Roadmap `/roadmap`
- Visual node-based map (like a game map)
- Locked nodes for higher levels
- Each node = one topic cluster
- Progress ring on each node

### Profile `/profile`
- Stats: problems solved, accuracy %, average score, level
- Heatmap of daily activity
- Badges earned
- Level-up history

---

## ML Level-Up Logic

```python
# Pseudo-code for level-up detection
def check_level_up(user_id):
    recent = get_last_5_submissions(user_id)
    consecutive_correct = 0
    for sub in reversed(recent):
        if sub.score >= 70 and sub.passed_all_tests:
            consecutive_correct += 1
        else:
            break
    
    if consecutive_correct >= 3:
        suggest_level_up(user_id)
```

The ML model refines this with:
- Time spent per problem (faster = more confident)
- Hint usage (fewer hints = stronger understanding)
- Solution quality score (not just pass/fail)

---

## Vercel Deployment

Frontend deploys to Vercel automatically on `git push`.

```json
// vercel.json
{
  "framework": "nextjs",
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "installCommand": "cd frontend && npm install",
  "env": {
    "NEXT_PUBLIC_SUPABASE_URL": "@supabase_url",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase_anon_key",
    "NEXT_PUBLIC_API_URL": "@backend_api_url"
  }
}
```

Backend deploys to Railway (FastAPI doesn't run on Vercel serverless well for long-running ML inference).

---

## Onboarding Quiz (ML Cold Start)

3 questions shown at signup:
1. "Have you coded before?" → Yes / No / A little
2. "Do you know what an array is?" → Yes / No
3. "Have you solved any LeetCode problems?" → Never / 1–10 / 10+

Based on answers, ML assigns initial level. If "No / No / Never" → Beginner. If "Yes / Yes / 1–10" → Intermediate. Etc.
