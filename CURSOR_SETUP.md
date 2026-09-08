# AlgoQuest — Cursor Setup Guide
# How to build this project step-by-step using Cursor AI

## Step 0: Initial Setup

1. Create a new folder: `algoquest/`
2. Open it in Cursor
3. Place `.cursorrules` in the root (already provided)
4. Open Cursor Chat (Cmd+L) and paste this to start:

```
I'm building AlgoQuest — an ML-powered LeetCode learning platform.
Read .cursorrules for all project rules and color tokens.
The stack is: Next.js 14 + FastAPI + Supabase + scikit-learn.
Let's start by scaffolding the frontend folder structure.
```

---

## Step 1: Scaffold Frontend

Ask Cursor:
```
Create the full Next.js 14 App Router folder structure for AlgoQuest.
Include: app/(auth)/login, app/(auth)/signup, app/(dashboard)/dashboard,
app/(dashboard)/problems/[id], app/(dashboard)/roadmap, app/(dashboard)/profile.
Create layout.tsx files for both route groups.
Use the color scheme from .cursorrules.
```

---

## Step 2: Build Auth Pages

Ask Cursor:
```
Build the Login page at app/(auth)/login/page.tsx.
Use react-hook-form + zod for validation.
Fields: email, password, remember me checkbox.
Include Google OAuth button.
Use Supabase Auth for the login logic.
Style with the dark theme: bg #0D0F1A, card #161929, accent purple #7C3AED.
Add framer-motion fade-in animation on mount.
```

Then:
```
Build the Signup page at app/(auth)/signup/page.tsx.
Fields: email, username, password, confirm password.
Show password strength indicator.
After signup, redirect to /onboarding quiz page.
Same dark styling.
```

---

## Step 3: Build Onboarding Quiz

Ask Cursor:
```
Build an onboarding quiz page at app/onboarding/page.tsx.
3 questions, one at a time (animated slide transition between questions):
1. "Have you coded before?" → options: Never / A little / Yes
2. "Do you know what an array is?" → options: No idea / Kind of / Yes, clearly
3. "Solved LeetCode before?" → options: Never / 1-10 / 10+
After Q3, call POST /api/v1/ml/assign-level with answers.
Show animated level assignment result with framer-motion.
```

---

## Step 4: Build Dashboard

Ask Cursor:
```
Build the dashboard at app/(dashboard)/dashboard/page.tsx.
Components needed:
- LevelBadge showing current level (Beginner/Intermediate/Advanced) with glow
- XP progress bar
- Streak counter with flame emoji
- "Recommended Next Problem" card from ML API
- Recent submissions list (last 5)
Style: dark surface cards on dark background, cyan + purple accents.
```

---

## Step 5: Build Problem Solver

Ask Cursor:
```
Build the problem solver page at app/(dashboard)/problems/[id]/page.tsx.
Left panel: problem statement, constraints, example test cases, hint button.
Right panel: Monaco Editor (Python, dark theme, JetBrains Mono font).
Bottom: test case results panel.
Buttons: Run Code, Submit.
After submit: show ML score (0-100) with score breakdown card.
If score >= 70 and 3 consecutive correct: show LevelUpModal.
```

---

## Step 6: Build Roadmap

Ask Cursor:
```
Build the roadmap at app/(dashboard)/roadmap/page.tsx using react-flow.
Three sections: Beginner (green), Intermediate (cyan), Advanced (purple).
Each section has topic nodes. Completed = filled. Locked = gray with padlock.
Show progress rings on each node.
Make it look like a game map with a glowing path between unlocked nodes.
```

---

## Step 7: Build FastAPI Backend

Ask Cursor:
```
Scaffold a FastAPI backend in the backend/ folder.
Include: app/main.py with CORS setup, routers for auth/users/problems/submissions/ml.
SQLAlchemy models for: User, Problem, Submission, UserProgress.
Pydantic v2 schemas for all models.
Alembic for migrations.
All routes prefixed with /api/v1/.
Use loguru for logging.
```

---

## Step 8: Build ML Modules

Ask Cursor:
```
Build backend/app/ml/scorer.py.
Function: score_solution(student_code: str, problem_id: int) -> dict
It should:
1. Parse student code with AST to estimate time/space complexity
2. Run pylint on student code for style score
3. Check for known optimal patterns for this problem (from DB)
4. Return: { score: int, breakdown: {correctness, complexity, style}, verdict: str }
```

Then:
```
Build backend/app/ml/level_detector.py.
Function: check_level_up(user_id: UUID, db: Session) -> bool
Get last 5 submissions for user.
Count consecutive submissions with score >= 70 and passed_all_tests = True.
If count >= 3 and user not already at max level: return True.
```

---

## Step 9: Deploy to Vercel

1. Push code to GitHub
2. Go to vercel.com → New Project → Import your repo
3. Framework: Next.js
4. Root directory: `frontend`
5. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL` (your Railway backend URL)
6. Click Deploy

For backend (Railway):
1. Go to railway.app → New Project → Deploy from GitHub
2. Select the repo, set root to `backend`
3. Add env vars from `.env.example`
4. Railway auto-detects FastAPI and deploys

---

## Cursor Tips for This Project

- Use `Cmd+K` on any component to refactor or add features inline
- Use `Cmd+L` to open chat and ask for new features
- When stuck on ML: ask "Explain how I should implement [feature] for the AlgoQuest ML system"
- To add a new problem: ask "Add a new problem to data/problems.json: [problem description]"
- For animations: ask "Add framer-motion animation to [component] that feels like a game level unlock"
