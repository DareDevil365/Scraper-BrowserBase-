from engine.deep_extractor import is_youtube_video, score_source_quality

def test_youtube_verification():
    # 1. Test is_youtube_video
    valid_watch = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    valid_shorts = "https://youtube.com/shorts/dQw4w9WgXcQ"
    valid_embed = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    valid_shortened = "https://youtu.be/dQw4w9WgXcQ"
    
    invalid_playlist = "https://www.youtube.com/playlist?list=PLy7Nr20"
    invalid_channel = "https://www.youtube.com/c/LinusTechTips"
    invalid_user = "https://www.youtube.com/user/marquesbrownlee"
    invalid_handle = "https://www.youtube.com/@mkbhd"
    
    assert is_youtube_video(valid_watch) is True, "Valid watch URL failed validation"
    assert is_youtube_video(valid_shorts) is True, "Valid shorts URL failed validation"
    assert is_youtube_video(valid_embed) is True, "Valid embed URL failed validation"
    assert is_youtube_video(valid_shortened) is True, "Valid shortened URL failed validation"
    
    assert is_youtube_video(invalid_playlist) is False, "Playlist URL passed validation incorrectly"
    assert is_youtube_video(invalid_channel) is False, "Channel URL passed validation incorrectly"
    assert is_youtube_video(invalid_user) is False, "User URL passed validation incorrectly"
    assert is_youtube_video(invalid_handle) is False, "Handle URL passed validation incorrectly"
    
    print("[PASS] is_youtube_video tests passed!")

def test_youtube_scoring():
    # 2. Test score_source_quality with conceptual / educational intent
    res_conceptual = score_source_quality(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="How to integrate Shiprocket API step by step",
        snippet="A tutorial walkthrough explaining the basics of Shiprocket API integration",
        research_subject="Shiprocket API",
        intent="general"
    )
    print("Conceptual Video score details:", res_conceptual)
    assert res_conceptual["score"] >= 85, f"Expected >= 85, got {res_conceptual['score']}"
    assert res_conceptual["tier"] == "TIER_2", f"Expected TIER_2, got {res_conceptual['tier']}"
    
    # 3. Test score_source_quality with pricing / numeric intent
    res_pricing = score_source_quality(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Shiprocket rate card comparison and surcharge tariffs",
        snippet="Review of Shiprocket pricing cost and fees",
        research_subject="Shiprocket pricing",
        intent="market"
    )
    print("Pricing Video score details:", res_pricing)
    assert 40 <= res_pricing["score"] <= 60, f"Expected between 40 and 60, got {res_pricing['score']}"
    assert res_pricing["tier"] == "TIER_4", f"Expected TIER_4, got {res_pricing['tier']}"
    
    # 4. Test score_source_quality with non-video YouTube URL
    res_playlist = score_source_quality(
        url="https://www.youtube.com/playlist?list=PLy7Nr20",
        title="Shiprocket Playlists",
        snippet="A collection of videos",
        research_subject="Shiprocket Integration",
        intent="general"
    )
    print("Playlist URL score details:", res_playlist)
    assert res_playlist["score"] == 0, f"Expected 0, got {res_playlist['score']}"
    assert res_playlist["tier"] == "Blocked", f"Expected Blocked, got {res_playlist['tier']}"

    print("[PASS] YouTube intent-aware scoring tests passed!")

if __name__ == "__main__":
    test_youtube_verification()
    test_youtube_scoring()
    print("\n[PASS] YouTube Intent-Aware Filtering & Scoring tests passed successfully!")
