from app.services.recommendation_service import public_url


def test_article_and_course_slugs_resolve_to_official_pages():
    assert public_url("kak-annulirovat-chuzhoj-tovarnyj-znak-osnovaniya-stoimost-ehtapy", "article") == (
        "https://kurs.alfabank.ru/articles/kak-annulirovat-chuzhoj-tovarnyj-znak-osnovaniya-stoimost-ehtapy/"
    )
    assert public_url("internet-marketing-dlya-malogo-biznesa", "course") == (
        "https://kurs.alfabank.ru/courses/internet-marketing-dlya-malogo-biznesa/"
    )


def test_documents_podcasts_and_calculators_resolve():
    assert public_url("akt-vypolnennyh-rabot", "document") == "https://kurs.alfabank.ru/documents/akt-vypolnennyh-rabot/"
    assert public_url("kod-liderstva-intervyu-s-denisom-osinym", "podcast") == "https://kurs.alfabank.ru/podcasts/kod-liderstva-intervyu-s-denisom-osinym/"
    assert public_url("zarplata", "calculator") == "https://kurs.alfabank.ru/calculators/zarplata/"


def test_unknown_or_unsafe_url_is_not_published():
    assert public_url(None, "article") is None
    assert public_url("../admin", "article") is None
    assert public_url("slug", "unknown") is None
    assert public_url("javascript:alert(1)", "article") is None
    assert public_url("https://evil.example/material", "article") is None
