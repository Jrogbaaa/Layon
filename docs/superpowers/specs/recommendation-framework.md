# Emotionally Intelligent Creative Recommendations Framework

This framework establishes the research-backed principles and implementation specifications for generating creative recommendations for talent at You First Gersh.

---

## 1. Distilled Research Framework & Principles

Our recommendation engine is built upon academic research in affective computing and viral sharing, combined with industry best practices in creator growth.

### A. The Lesson-Extraction Loop (Creator Lab)
*   **Principle:** Analyze past performance to extract the abstract *mechanism* of success, rather than recommending literal replication. 
*   **Mechanism vs. Copying:** For every winning post, the engine identifies the structural loop: **Repeat** the underlying mechanism, **Avoid** direct content cloning (which leads to fatigue), and **Improve** the execution variables (e.g., hooks, pacing).
*   **Citation:** *Creator Lab: Growth Tactics & Fatigue (2024)*.

### B. Format-Swap & Concept Abstraction
*   **Principle:** Decouple the core concept from its original presentation format to keep content fresh and prevent creative exhaustion.
*   **Application:** If a concept succeeds as a carousel of text reflections, the next action should abstract that concept (e.g., "revealing the preparation process" or "sharing personal resilience") and express it in a different format (e.g., a direct-to-camera short reel or a high-production photo set with an editorial caption).

### C. Explore/Exploit Split
*   **Principle:** Maintain audience engagement by balancing "exploitation" (repeating proven formats and themes) and "exploration" (testing new formats, topics, or timely trend hooks).
*   **Application:** Recommendations are limited strictly to exactly two types:
    1.  **Exploit (Past Success Re-expressed):** Leveraging historically proven mechanisms in a new form.
    2.  **Explore (Trend-Tied Idea):** Persona-aligned, culturally relevant trends.

### D. Rotation Eligibility & Retirement Rules
*   **Principle:** Prevent creative and audience fatigue by rotating themes. 
*   **Application:** Once a theme (e.g., "behind-the-scenes recovery") is recommended and executed, it enters a cooldown cycle. A single post topic should never be suggested consecutively. Recommendations must retire from immediate rotation after a set period or after showing declining engagement over successive posts.

### E. Trend-Fit Filter
*   **Principle:** Do not force generic or off-brand trends.
*   **Application:** Trends must be matched to the influencer's specific tier, industry, and style. If a trend does not naturally align with the creator's persona boundaries (e.g., premium presenter vs. professional athlete vs. sketch comedian), the trend recommendation must be skipped entirely rather than forced.

### F. Emotional-Appropriateness Guardrail (Leite et al.; Berger & Milkman)
*   **Principle:** Vulnerable, intimate, or highly personal topics (e.g., grief, illness, breakups, personal struggles) require strict boundaries. Recommending tactical repetition of these topics is counterproductive.
*   **Mechanism:**
    *   **Intimacy Fatigue (Leite et al.):** Repeatedly sharing negative or vulnerable personal situations for the sake of engagement ("tactical intimacy") damages the creator's long-term credibility and authenticity. Empathy must not be gamified.
    *   **Arousal-Valence Framework (Berger & Milkman):** Sharing is driven by physiological arousal. Sadness is a *low-arousal* (deactivating) emotion that reduces the propensity to share, whereas awe, excitement, anger, and anxiety are *high-arousal* (activating) emotions. Tactical repetition of low-arousal sad content fails to sustain viral reach and alienates followers.
*   **Rule:** Personal struggle or grief can serve as evidence that the audience values *authenticity*, but it must **never** be recommended for tactical repetition.
*   **Citations:** 
    *   Leite, I., Paiva, A. et al. *Social Presence and Empathy in Long-Term HRI (2013)*.
    *   Berger, J., & Milkman, K. L. *What Makes Online Content Viral? Journal of Marketing Research (2012)*.

---

## 2. Audit of Current Database Output

Based on the latest recommendations retrieved from Supabase on July 13, 2026, the current engine output displays significant failures when measured against this framework.

### Worked Example: @cristipedroche
*   **Persona:** Elite/polished TV presenter; premium, aesthetic content. No meme dances or low-fi trends.
*   **Current Recommendations and Scores:**

| Recommendation Bullet | Score | Violations Identified |
| :--- | :--- | :--- |
| **1. Create a heartfelt reel sharing a personal milestone or emotional reflection about her partner or family.** | **FAIL** | **Tactics of Intimacy:** Recommends repeating vulnerable family/relationship milestones for engagement.<br>**Mechanism Cloning:** Suggests direct copy-paste of DVQQG8FiDPb rather than abstracting the mechanism. |
| **2. Post a sophisticated carousel offering personal insights... linking to the recent Shakira news.** | **FAIL** | **Forced Trend Fit:** Forcibly links her personal resilience to celebrity AI rumor news (Shakira), which is off-brand for an elite TV presenter. |
| **3. Share a carousel post detailing a personal journey... similar to breastfeeding and milk donation.** | **FAIL** | **Tactics of Intimacy:** Direct violation of Leite et al. Recommends tactical repetition of intimate medical/parenting journeys because they got high engagement. |
| **4. Produce a polished reel showcasing 'a day in her life'...** | **PASS** | Formats match her profile, though the recommendation is generic and lacks concept abstraction. |

---

### Audit of Other Active Influencers

#### @mariavalero (Comedy/sketches)
*   *Bullet 1:* "Crea un nuevo sketch de comedia sobre una ruptura, similar a 'Cuando te dejan antes del verano.'"
    *   **Violation:** Direct replication of a specific post topic/theme ("breakup sketch") rather than abstracting the comedic mechanism (e.g., subverting relationship tropes).
*   *Bullet 3:* "Crea un reel de humor sobre relaciones reaccionando a la ruptura de Ferrán Torres..."
    *   **Violation:** Forced/repetitive relationship content and tactical exploitation of someone else's breakup.

#### @antonlofer (Comedy/sketches)
*   *Bullet 1:* "Crea un sketch cómico parodiando una scene de Jurassic Park, inspirado por el fallecimiento de Sam Neill."
    *   **Violation (CRITICAL):** Direct violation of Leite et al. emotional appropriateness. Recommends capitalizing on someone's death for a comedic sketch.
*   *Bullet 2:* "Produce un sketch... similar a 'la entrega de un paquete como película'."
    *   **Violation:** Literal replication ("do this again") rather than mechanism extraction.

#### @ferminaldeguer_54 (MotoGP Rider)
*   *Bullet 1:* "Share a pensive carousel post conveying your desire to return to racing..."
    *   **Violation:** Recommending literal replication of a specific personal/emotional state (desiring to return to the track during injury/recovery).
*   *Bullet 4:* "Post behind-the-scenes... adding an enigmatic caption or vibe."
    *   **Violation:** Generates low-value, generic advice ("enigmatic vibe") that has no operational mechanism.

#### @dante_caro (Comedy/sketches)
*   *Bullet 4:* "Focus exclusively on comedy Reels; immediately stop posting carousels..."
    *   **Violation:** Generates strategic/meta advice rather than an actionable, creative post recommendation.

---

## 3. Gap List in `scraper/youfirst_scraper/recommendations.py`

Below is the mapping of framework failures to the specific parts of the existing `build_prompt` code in [recommendations.py](file:///Users/JackEllis/Layon/scraper/youfirst_scraper/recommendations.py):

1.  **Failure to Abstract Mechanism (Direct Cloning / "Do it again"):**
    *   *Code Location:* `recommendations.py:114-118`
    *   *Gap:* The prompt explicitly commands: *"Each recommendation must reference the specific top-performing post... e.g. 'Follow up on [post topic]'."* This actively forces the AI to suggest literal copy-pastes and topic cloning instead of extracting structural mechanisms.
2.  **Lack of Pre-classification (Mechanism Extraction):**
    *   *Code Location:* `recommendations.py:29-83` (Prompt data binding)
    *   *Gap:* The prompt feeds raw captions and basic metrics (`post_type`, `likes`, `comments`) but does not ask the LLM to classify or analyze *why* the post succeeded (arousal level, valence, theme, structural hook, authenticity signals) before formatting ideas.
3.  **Absence of Emotional Appropriateness Guardrail:**
    *   *Code Location:* `recommendations.py:97-123` (System instruction)
    *   *Gap:* The prompt completely lacks guardrails regarding sensitive topics. It does not forbid suggestions utilizing grief, death, illness, breakups, or family milestones for engagement.
4.  **No Trend-Fit Exclusivity/Skipping:**
    *   *Code Location:* `recommendations.py:91-94`
    *   *Gap:* The prompt instructs the LLM that if trends do not fit, it should *"base the recommendation on the performance data instead of inventing a trend."* However, it does not explicitly allow the LLM to skip the trend bullet entirely, leading the LLM to force-fit trends (like forcing the Shakira AI image trend onto Cristina Pedroche or Dante Caro).
5.  **Weak Persona & Format Boundary Enforcement:**
    *   *Code Location:* `recommendations.py:56-62`
    *   *Gap:* It instructs the LLM to *"Only suggest formats and trend adaptations that fit this persona."* However, the database personas themselves lack clear boundaries, and the prompt does not list explicit format rules (e.g., "MotoGP athletes do not do TikTok dances/sketches; TV presenters do not do low-fi sketches").
6.  **Unstructured Suggestions (Fluff / Meta-advice):**
    *   *Code Location:* `recommendations.py:122-123`
    *   *Gap:* The output schema does not enforce the type/category of the recommendation. It allows generic account-wide advice ("stop posting carousels") instead of restricting suggestions to exactly two content types: (1) past success re-expressed, and (2) applicable trend.
