# AlgoQuest — Feature Specification

## Authentication & Onboarding

### Registration
- [ ] Email + password signup (Supabase Auth)
- [ ] Google OAuth signup
- [ ] Email verification required before dashboard access
- [ ] Username picker after signup
- [ ] Password strength indicator on signup form
- [ ] Terms of Service + Privacy Policy checkbox

### Login
- [ ] Email + password login
- [ ] Google OAuth login
- [ ] "Remember me" (30-day session)
- [ ] Forgot password → email reset link
- [ ] Rate limiting: 5 failed attempts → 15-min lockout

### Onboarding Quiz (ML Cold Start)
- [ ] 3-question skill assessment shown immediately after signup
- [ ] Questions: prior coding experience, array knowledge, LeetCode history
- [ ] ML assigns starting level based on answers
- [ ] Animated level assignment screen ("You're starting at Beginner!")
- [ ] Skip option (defaults to Beginner)

---

## Dashboard

- [ ] Current level badge (Beginner / Intermediate / Advanced) with animated glow
- [ ] XP progress bar (current level XP / XP needed to unlock next level)
- [ ] Daily streak counter with flame icon
- [ ] "Continue where you left off" → last visited problem/lesson
- [ ] ML-recommended next problem card ("Based on your progress, try this next")
- [ ] Recent submissions list (last 5, with score and status)
- [ ] Weekly activity summary (problems solved this week)
- [ ] Motivational quote (rotates daily)

---

## Learning System

### Lessons (per topic)
- [ ] Beginner topics: Variables & Types, Loops, Functions, OOP, Lists, Dicts, Sets
- [ ] Intermediate topics: Recursion, Two Pointers, Sliding Window, Binary Search, Stacks, Queues, Linked Lists, Trees
- [ ] Advanced topics: Graphs, BFS/DFS, Dynamic Programming, Tries, Heaps, Greedy
- [ ] Each lesson rendered as MDX with syntax-highlighted code blocks
- [ ] Inline runnable code snippets (mini playground)
- [ ] Concept visualizer (animated diagrams for stack, queue, tree traversal, etc.)
- [ ] End-of-lesson quiz (3–5 MCQ questions)
- [ ] Lesson completion awards XP

### Animated Visualizers
- [ ] Stack push/pop animation
- [ ] Queue enqueue/dequeue animation
- [ ] Binary search stepping through array
- [ ] Tree traversal (in-order, pre-order, BFS)
- [ ] Two-pointer technique animation
- [ ] Sorting algorithm visualizer (bubble, merge, quick)

---

## Problem System

### Problem Bank
- [ ] 100 total problems: 30 Easy, 40 Medium, 30 Hard
- [ ] Each problem tagged with: level, topics, estimated time, company tags
- [ ] Problems filtered/locked by current user level
- [ ] Filterable by: difficulty, topic, status (solved/attempted/unsolved), company

### Problem Solver Page
- [ ] Split-pane layout: problem statement (left) + Monaco code editor (right)
- [ ] Monaco Editor with Python syntax highlighting and autocomplete
- [ ] Font: JetBrains Mono, font size adjustable
- [ ] Dark theme matching app palette
- [ ] Run button → executes code against visible test cases (Judge0)
- [ ] Submit button → runs against all hidden test cases
- [ ] Test case panel below editor: shows input, expected output, your output
- [ ] Pass/fail indicators per test case
- [ ] Runtime and memory display after submission

### Hint System
- [ ] 3 progressive hints per problem (Hint 1 → gentle nudge, Hint 2 → approach, Hint 3 → near-solution)
- [ ] Each hint costs 5 XP (deducted on reveal)
- [ ] Hints are personalized: ML analyzes student's code before suggesting
- [ ] Hint panel slides in from right

### Solution Feedback (ML-powered)
- [ ] Score 0–100 displayed after every submission
- [ ] Score breakdown: Correctness (50pts), Time Complexity (25pts), Space Complexity (15pts), Code Style (10pts)
- [ ] Color-coded score: red/amber/cyan/green
- [ ] "Best Solution" vs "Your Solution" side-by-side comparison (after submit)
- [ ] Complexity badge: O(n), O(n²), O(log n) detected automatically
- [ ] Verdict label: "Brute Force", "Optimal", "Good Approach", "Wrong Approach"
- [ ] Detailed explanation of optimal solution

### Level-Up Detection (ML)
- [ ] After every submission, check if last 3 were ≥70 score + all tests passed
- [ ] If yes: animated "Ready to Level Up?" modal
- [ ] Modal shows: current level, next level, what unlocks, CTA to proceed
- [ ] Confetti animation on level-up confirmation
- [ ] Level-up awards bonus XP (100 XP)

---

## Roadmap Page

- [ ] Visual game-map style node graph (react-flow)
- [ ] Nodes organized in topic clusters per level
- [ ] Completed nodes: green checkmark, filled
- [ ] In-progress nodes: cyan glow, pulsing
- [ ] Locked nodes: gray, padlock icon
- [ ] Click node → goes to that lesson/problem cluster
- [ ] Progress ring around each node (% of cluster completed)
- [ ] Level sections clearly separated (Beginner zone → Intermediate zone → Advanced zone)
- [ ] "Path to Advanced" highlighted with a glowing trail

---

## Profile Page

- [ ] Avatar (auto-generated from initials or uploaded)
- [ ] Username, join date, current level
- [ ] Stats grid: Problems Solved, Accuracy %, Average Score, Current Streak
- [ ] Activity heatmap (like GitHub contribution graph)
- [ ] Badges section: earned badges displayed as cards
- [ ] Level history timeline
- [ ] Topic breakdown: radar chart showing strength per topic
- [ ] Edit profile: display name, avatar

---

## Badge System

| Badge | Trigger |
|---|---|
| First Blood | Solve first problem |
| Hot Streak | 7-day streak |
| Perfect Score | Get 100/100 on any problem |
| Hint-Free | Solve 5 problems without any hints |
| Speed Demon | Solve a problem in under 5 minutes |
| Level Up! | Reach Intermediate |
| Algorithm Master | Reach Advanced |
| Clean Coder | Get A+ on code style 10 times |
| Night Owl | Submit at midnight |
| Comeback Kid | Solve a problem after 3+ wrong attempts |

---

## XP & Gamification

- [ ] XP awarded: Easy=10, Medium=25, Hard=50
- [ ] Hint penalty: -5 XP per hint used
- [ ] Perfect score bonus: +15 XP
- [ ] Daily first solve bonus: +20 XP
- [ ] Streak bonus: +5 XP per day in streak
- [ ] Level-up requires: Beginner→Intermediate: 500 XP, Intermediate→Advanced: 1500 XP
- [ ] XP bar animates on every award
- [ ] Toast notification on XP gain

---

## ML Features (Detailed)

### 1. Adaptive Level Progression
- Tracks last N submissions with a sliding window
- Features: score, correctness, time_to_solve, hints_used
- Triggers level-up suggestion when 3 consecutive strong submissions detected
- Model: Logistic Regression (fast, interpretable)

### 2. Solution Quality Scorer
- Input: student's Python code + problem's optimal solution
- Static analysis: AST parsing for complexity estimation
- Pylint score for style
- Pattern matching for known optimal patterns (HashMap usage, two-pointer setup)
- Output: 0–100 score with breakdown

### 3. Personalized Problem Recommender
- User-based collaborative filtering using submission history
- Content-based fallback: problem topic + difficulty tags
- Cold start: onboarding quiz result → rule-based level assignment
- Updated daily via batch job

### 4. Struggle Detector
- Monitors: time on problem (>15 min), hint usage (3+ hints), wrong attempts (5+)
- Flags user as "struggling"
- Triggers: proactive explanation panel, simplified problem variant link, encouragement message

### 5. Smart Hint Generator
- Analyzes student's current code via AST
- Identifies what approach they're trying
- Generates a targeted hint: "It looks like you're using a nested loop — try thinking about a way to avoid checking the same element twice using a data structure that gives O(1) lookups."

---

## Vercel Deployment Checklist

- [ ] `vercel.json` configured at repo root
- [ ] All `NEXT_PUBLIC_*` env vars added to Vercel project settings
- [ ] Backend URL added as `NEXT_PUBLIC_API_URL` in Vercel
- [ ] Supabase credentials added to Vercel
- [ ] Custom domain configured (optional)
- [ ] Preview deployments enabled for PRs
- [ ] Backend deployed to Railway with `railway up`
- [ ] Railway env vars set (DATABASE_URL, SECRET_KEY, JUDGE0_API_KEY)
- [ ] CORS_ORIGINS in backend includes Vercel production URL
