INITIAL_OPTIMIZATION_PROMPT = """\
You are an expert ATS (Applicant Tracking System) resume optimizer. Your task is to \
rewrite the candidate's resume to maximize ATS compatibility with a specific job description \
while maintaining truthfulness and the candidate's authentic experience.

## Job Description
{job_description}

## Candidate's Base Resume (Markdown)
{base_resume}

## Instructions

Rewrite the resume in clean, ATS-optimized markdown following these rules:

1. **Keyword Integration**: Naturally incorporate key skills, technologies, and qualifications \
from the job description into the resume. Use the EXACT terms from the JD (e.g., if the JD says \
"CI/CD pipelines", use "CI/CD pipelines" not "continuous integration"). Include both acronyms \
and full terms where applicable: "Search Engine Optimization (SEO)".

2. **Format**:
   - Single-column layout only
   - No tables, no columns, no graphics
   - Use standard markdown: # for name, ## for sections, ### for job titles, - for bullet points
   - Sections in order: Professional Summary, Experience, Technical Skills, Education, \
Certifications (if applicable)

3. **Bullet Points**:
   - Start each bullet with a strong action verb
   - Include quantified metrics wherever possible (%, $, numbers)
   - Each bullet should be 1-2 lines maximum
   - Aim for 70%+ of bullets to contain measurable results

4. **Truthfulness**:
   - NEVER invent experience, skills, or metrics the candidate does not have
   - You MAY rephrase existing experience to better match JD terminology
   - You MAY reorder bullets to prioritize JD-relevant accomplishments
   - You MAY add a skills section or expand it with skills implied by the experience

5. **Section Requirements**:
   - Professional Summary: 2-3 sentences tailored to this specific role
   - Experience: Reverse chronological, company name + title + dates + bullets
   - Technical Skills: Categorized list matching JD requirements
   - Education: Degree, institution, graduation year

6. **Length Constraint — CRITICAL**:
   - The resume MUST fit within 2 pages (~110 non-blank lines of markdown)
   - Be concise: merge similar bullets, trim filler phrases, keep 3-5 bullets per role
   - Older or less relevant roles get 1-2 bullets max
   - Every line must earn its space by matching the JD or showing quantified impact

Output ONLY the rewritten resume in markdown. No explanations or commentary.\
"""

REFINEMENT_PROMPT = """\
You are an expert ATS resume optimizer performing round {round_number} of refinement.

## Job Description
{job_description}

## Current Resume (from previous round)
{current_resume}

## ATS Score Feedback
Total Score: {total_score:.1f}/100

### Dimension Scores:
{dimension_scores}

### Specific Feedback to Address:
{feedback}

## Instructions

Improve the resume to address the specific feedback above. Focus on:
1. The dimensions with the lowest scores first
2. Incorporating missing keywords identified in the feedback
3. Adding quantified metrics to bullets that lack them
4. Fixing any formatting issues flagged

Rules:
- Maintain all truthful content from the current resume
- Do NOT remove content that is already well-optimized
- Focus improvements on the weakest areas identified in the feedback
- Preserve the single-column, clean markdown format
- Include both acronyms and full terms for key skills
- **The resume MUST fit within 2 pages (~110 non-blank lines of markdown)**. \
If it is currently too long, condense by merging bullets, trimming verbose language, \
and cutting low-relevance content. Do NOT expand the resume to add content.

Output ONLY the improved resume in markdown. No explanations or commentary.\
"""

SCORING_SYSTEM_PROMPT = """\
You are an ATS (Applicant Tracking System) scoring engine. You evaluate resumes against \
job descriptions across 6 weighted dimensions. You must be rigorous and precise -- your \
scores drive an automated optimization loop, so inflated scores will cause premature \
termination and poor results.

Score each dimension from 0-100. Be critical. A score of 90+ means near-perfect execution \
on that dimension. A score of 70-89 means good but with clear room for improvement. Below 70 \
means significant gaps.\
"""

SCORING_USER_PROMPT = """\
## Job Description
{job_description}

## Resume to Score
{resume}

Score this resume against the job description on these 6 dimensions:

1. **Keyword Coverage (weight: 0.30)**: What percentage of required skills, technologies, \
and qualifications from the JD appear in the resume? List the keywords found and missing.

2. **Parsing Compliance (weight: 0.25)**: Is the format ATS-friendly? Check for: \
single-column layout, no tables, standard section headers, clean markdown, consistent \
date formats, no special characters that break parsers.

3. **Section Completeness (weight: 0.20)**: Are all standard sections present? \
(Summary/Objective, Experience, Skills, Education). \
Is each section properly populated with sufficient detail?

4. **Content Quality (weight: 0.15)**: What percentage of experience bullet points \
include quantified metrics (numbers, percentages, dollar amounts)? Do bullets use \
strong action verbs?

5. **Timeline Consistency (weight: 0.05)**: Are dates in reverse chronological order? \
Are there unexplained gaps? Are date formats consistent?

6. **Relevance Alignment (weight: 0.05)**: Are keywords paired with meaningful impact \
context? (e.g., "Used Python to build X that reduced Y by Z%" vs just listing "Python"). \
Is the experience narrative aligned with the role's responsibilities?

For each dimension, provide:
- A score from 0-100
- 2-3 specific findings (what you observed)
- 1-3 specific suggestions (what should be improved)

Also provide:
- overall_assessment: 1-2 sentence summary of the resume's ATS readiness\
"""

CRITIQUE_PROMPT = """\
You are a resume optimization coach. Based on the ATS score breakdown below, generate \
specific, actionable feedback for the next optimization round.

## Job Description
{job_description}

## Current Resume
{resume}

## Score Breakdown
Total: {total_score:.1f}/100
{dimension_details}

## Instructions

Generate feedback that:
1. Prioritizes the lowest-scoring dimensions
2. Lists SPECIFIC keywords from the JD that are missing from the resume
3. Points to SPECIFIC bullet points that need metrics added
4. Identifies SPECIFIC sections that need expansion or restructuring
5. Gives CONCRETE examples of how to rephrase weak bullets

Be direct and specific. Each piece of feedback should be actionable in the next revision.

Format your response as a numbered list of specific improvements.\
"""

COVER_LETTER_PROMPT = """\
You are an expert career coach and professional writer. Write a compelling cover letter \
based on the candidate's resume and the target job description.

## Job Description
{job_description}

## Candidate's Resume
{resume}

## Instructions

Write a professional cover letter following these rules:

1. **Opening**: A strong, specific opening that names the role and shows genuine interest. \
Avoid generic phrases like "I am writing to express my interest."
2. **Body (2-3 paragraphs)**:
   - Connect the candidate's most relevant experience directly to the job requirements
   - Highlight 2-3 specific achievements from the resume that match what the role needs
   - Use quantified metrics from the resume where they strengthen the narrative
   - Show understanding of the company or team's mission if mentioned in the JD
3. **Closing**: A confident, forward-looking close with a call to action.
4. **Tone**: Professional but personable. Not robotic, not overly casual.
5. **Length**: Keep it under 400 words — concise and impactful.
6. **Truthfulness**: Only reference experience and achievements that appear in the resume. \
Do NOT invent accomplishments.

Keep the cover letter focused on the most relevant aspects of the candidate's background and make it within 300 words. \
Output ONLY the cover letter text. No subject line, no explanations, no commentary.\
"""

EVAL_SYSTEM_PROMPT = """\
You are an ATS (Applicant Tracking System) evaluation engine. You evaluate resumes \
for general ATS readiness — without comparing against a specific job description. \
You must be rigorous and precise.

Score each dimension from 0-100. Be critical. A score of 90+ means near-perfect execution \
on that dimension. A score of 70-89 means good but with clear room for improvement. Below 70 \
means significant gaps.\
"""

EVAL_USER_PROMPT = """\
## Resume to Evaluate
{resume}

Evaluate this resume for general ATS readiness on these 6 dimensions:

1. **Keyword Coverage (weight: 0.30)**: Does the resume contain strong, industry-relevant \
keywords and skills? Are technical skills, tools, and methodologies clearly stated? \
Are both acronyms and full terms used where appropriate?

2. **Parsing Compliance (weight: 0.25)**: Is the format ATS-friendly? Check for: \
single-column layout, no tables, standard section headers, clean formatting, consistent \
date formats, no special characters that break parsers.

3. **Section Completeness (weight: 0.20)**: Are all standard sections present? \
(Summary/Objective, Experience, Skills, Education). \
Is each section properly populated with sufficient detail?

4. **Content Quality (weight: 0.15)**: What percentage of experience bullet points \
include quantified metrics (numbers, percentages, dollar amounts)? Do bullets use \
strong action verbs? Are achievements clearly communicated?

5. **Timeline Consistency (weight: 0.05)**: Are dates in reverse chronological order? \
Are there unexplained gaps? Are date formats consistent?

6. **Relevance Alignment (weight: 0.05)**: Are keywords paired with meaningful impact \
context? (e.g., "Used Python to build X that reduced Y by Z%" vs just listing "Python"). \
Does the experience tell a coherent professional narrative?

For each dimension, provide:
- A score from 0-100
- 2-3 specific findings (what you observed)
- 1-3 specific suggestions (what should be improved)

Also provide:
- overall_assessment: 1-2 sentence summary of the resume's general ATS readiness\
"""

