def first_text(response) -> str:
    """Return the first text block from a Messages API response.

    Some models (e.g. Kimi k2.6) emit a leading ``thinking`` block before the
    ``text`` block, so ``response.content[0]`` is not always the answer text.
    """
    for block in response.content:
        if getattr(block, "type", None) == "text":
            return block.text
    raise ValueError("Model response contained no text block")
