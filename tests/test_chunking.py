from packages.core.ingest import chunk_markdown

def test_chunk_markdown_splits_headings_and_bounds_size():
    md = "# Title\n\n" + ("a " * 2000) + "\n\n## Section\n\n" + ("b " * 2000)
    chunks = chunk_markdown(md, max_chars=500, overlap=0)
    assert len(chunks) > 2
    assert all(len(c) <= 500 for c in chunks)

def test_chunk_markdown_keeps_heading_context():
    md = "# UTM Policy\n\nUse utm_source.\n\n## Examples\n\nExample text."
    chunks = chunk_markdown(md, max_chars=2000, overlap=0)
    assert any("UTM Policy" in c for c in chunks)