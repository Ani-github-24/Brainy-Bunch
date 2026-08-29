from app.transcription import scrub_pii

def test_scrub_pii():
    """Verify that the PII scrubber correctly redacts email addresses and phone numbers."""
    
    # Text with both email and phone number
    sample_text = (
        "Hello class, my email is professor.smith123@university.edu and you can "
        "reach my office at (555) 123-4567. We will cover chapter 4 today."
    )
    
    scrubbed = scrub_pii(sample_text)
    
    # Email and phone number should be redacted
    assert "professor.smith123@university.edu" not in scrubbed
    assert "(555) 123-4567" not in scrubbed
    
    # They should be replaced with [REDACTED]
    assert scrubbed.count("[REDACTED]") == 2
    
    # Rest of the text should remain untouched
    assert "Hello class, my email is [REDACTED] and you can reach my office at [REDACTED]. We will cover chapter 4 today." == scrubbed

def test_scrub_pii_edge_cases():
    """Test other formats and edge cases."""
    
    cases = [
        ("My email is simple@test.com", "My email is [REDACTED]"),
        ("Call +1 800-555-1234 now.", "Call [REDACTED] now."),
        ("No PII here, just normal text 12345.", "No PII here, just normal text 12345."),
        ("Phone: 123.456.7890", "Phone: [REDACTED]"),
    ]
    
    for original, expected in cases:
        assert scrub_pii(original) == expected
