from hunterx.utils.markdown import (
    count_quantified_bullets,
    estimate_pages,
    extract_sections,
    find_missing_sections,
)


def test_extract_sections(sample_resume):
    sections = extract_sections(sample_resume)
    assert "professional summary" in sections
    assert "work experience" in sections
    assert "technical skills" in sections
    assert "education" in sections


def test_find_missing_sections_complete(sample_resume):
    missing = find_missing_sections(sample_resume)
    assert missing == []


def test_find_missing_sections_incomplete():
    resume = "# Name\n\n## Experience\n- Did stuff\n"
    missing = find_missing_sections(resume)
    assert "Summary/Objective" in missing
    assert "Education" in missing
    assert "Skills" in missing


def test_count_quantified_bullets(sample_resume):
    total, quantified = count_quantified_bullets(sample_resume)
    assert total > 0
    assert quantified > 0
    assert quantified <= total


def test_count_quantified_bullets_with_metrics():
    text = """
- Increased revenue by 40%
- Managed a team
- Saved $50,000 annually
- Processed 10000 users daily
"""
    total, quantified = count_quantified_bullets(text)
    assert total == 4
    assert quantified == 3


def test_estimate_pages_short():
    resume = "# Name\n\n## Summary\nShort resume.\n\n## Experience\n- Did stuff\n"
    pages = estimate_pages(resume)
    assert pages < 1.0


def test_estimate_pages_long():
    lines = ["- Bullet point number {}".format(i) for i in range(120)]
    resume = "# Name\n\n" + "\n".join(lines)
    pages = estimate_pages(resume)
    assert pages > 2.0
