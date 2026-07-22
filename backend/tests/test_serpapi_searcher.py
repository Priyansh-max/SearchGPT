import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.serpapi_searcher import SerpApiSearcher  # noqa: E402


def test_google_parser_uses_knowledge_graph_and_drops_favicon_images():
    searcher = SerpApiSearcher()
    results = searcher._parse_google_results({
        "knowledge_graph": {
            "title": "Rahul Dravid",
            "description": "Indian cricket coach and former captain.",
            "born": "11 January 1973",
            "source": {"name": "Wikipedia", "link": "https://en.wikipedia.org/wiki/Rahul_Dravid"},
            "thumbnail": "https://example.com/dravid.jpg",
        },
        "organic_results": [
            {
                "title": "Rahul Dravid",
                "link": "https://en.wikipedia.org/wiki/Rahul_Dravid",
                "snippet": "Duplicate organic result.",
                "favicon": "https://www.google.com/s2/favicons?domain=wikipedia.org&sz=64",
            },
            {
                "title": "Rahul Dravid profile",
                "link": "https://www.espncricinfo.com/cricketers/rahul-dravid-28114",
                "snippet": "Career profile.",
                "thumbnail": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320/lsci/db/PICTURES/CMS/128400/128439.png",
            },
        ],
    })

    assert results[0]["title"] == "Rahul Dravid"
    assert "Born: 11 January 1973" in results[0]["snippet"]
    assert results[0]["image"] == "https://example.com/dravid.jpg"
    assert [item["url"] for item in results].count("https://en.wikipedia.org/wiki/Rahul_Dravid") == 1
    assert results[1]["image"].startswith("https://img1.hscicdn.com")


def test_content_image_filter_rejects_favicons():
    assert SerpApiSearcher._is_content_image("https://www.google.com/s2/favicons?domain=x.com&sz=64") is False
    assert SerpApiSearcher._is_content_image("https://example.com/favicon.ico") is False
    assert SerpApiSearcher._is_content_image("https://example.com/photo.jpg") is True
