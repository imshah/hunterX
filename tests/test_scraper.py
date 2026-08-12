import httpx
import pytest
import respx

from hunterx.scraper import fetch_job_description


@respx.mock
def test_extracts_from_job_description_class():
    html = """
    <html><body>
    <nav>Navigation links</nav>
    <div class="job-description">
        <h2>About the Role</h2>
        <p>We are looking for a software engineer with 5+ years of experience
        building scalable distributed systems.</p>
        <ul><li>Python expertise</li><li>Kubernetes experience</li></ul>
    </div>
    <footer>Footer content</footer>
    </body></html>
    """
    respx.get("https://example.com/job/123").mock(
        return_value=httpx.Response(200, text=html)
    )
    result = fetch_job_description("https://example.com/job/123")
    assert "software engineer" in result
    assert "Python expertise" in result
    assert "Navigation" not in result
    assert "Footer" not in result


@respx.mock
def test_extracts_from_article_tag():
    html = """
    <html><body>
    <nav>Nav</nav>
    <article>
        <h1>Senior Backend Engineer</h1>
        <p>Join our team to build amazing products. We need someone who has
        experience with cloud infrastructure and microservices architecture.</p>
    </article>
    </body></html>
    """
    respx.get("https://example.com/job").mock(
        return_value=httpx.Response(200, text=html)
    )
    result = fetch_job_description("https://example.com/job")
    assert "Senior Backend Engineer" in result
    assert "microservices" in result


@respx.mock
def test_falls_back_to_body():
    html = """
    <html><body>
    <div>
        <p>This is a job posting for a data scientist who will work on
        machine learning pipelines and statistical modeling projects.</p>
    </div>
    </body></html>
    """
    respx.get("https://example.com/job").mock(
        return_value=httpx.Response(200, text=html)
    )
    result = fetch_job_description("https://example.com/job")
    assert "data scientist" in result
    assert "machine learning" in result


@respx.mock
def test_removes_script_and_style():
    html = """
    <html><body>
    <article>
        <style>.hidden { display: none; }</style>
        <script>alert('xss')</script>
        <p>Actual job description content here about a product manager role
        with strong analytical skills and stakeholder management experience.</p>
    </article>
    </body></html>
    """
    respx.get("https://example.com/job").mock(
        return_value=httpx.Response(200, text=html)
    )
    result = fetch_job_description("https://example.com/job")
    assert "product manager" in result
    assert "alert" not in result
    assert ".hidden" not in result


@respx.mock
def test_cleans_excessive_whitespace():
    html = """
    <html><body>
    <article>
        <p>Line one</p>



        <p>Line two</p>




        <p>Line three</p>
    </article>
    </body></html>
    """
    respx.get("https://example.com/job").mock(
        return_value=httpx.Response(200, text=html)
    )
    result = fetch_job_description("https://example.com/job")
    assert "\n\n\n" not in result
    assert "Line one" in result
    assert "Line three" in result


@respx.mock
def test_raises_on_http_error():
    respx.get("https://example.com/missing").mock(
        return_value=httpx.Response(404)
    )
    with pytest.raises(httpx.HTTPStatusError):
        fetch_job_description("https://example.com/missing")


@respx.mock
def test_follows_redirects():
    respx.get("https://example.com/short").mock(
        return_value=httpx.Response(
            301, headers={"Location": "https://example.com/job/full"}
        )
    )
    respx.get("https://example.com/job/full").mock(
        return_value=httpx.Response(
            200,
            text="""<html><body><article>
            <p>Full job description for a frontend developer building
            React applications with TypeScript and modern tooling.</p>
            </article></body></html>""",
        )
    )
    result = fetch_job_description("https://example.com/short")
    assert "frontend developer" in result
