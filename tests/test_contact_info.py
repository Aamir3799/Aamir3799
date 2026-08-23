from rental_search.parsing import extract_contact_info


def test_extracts_agency_name_phone_and_email():
    text = (
        "Aangeboden door Jansen Makelaardij. Bel 020-1234567 of mail "
        "info@jansenmakelaardij.nl voor meer informatie."
    )
    name, phone, email = extract_contact_info(text)
    assert name == "Jansen Makelaardij"
    assert phone == "020-1234567"
    assert email == "info@jansenmakelaardij.nl"


def test_extracts_mobile_number_and_email_without_agency_phrase():
    text = "Contact: Maria de Vries, +31 6 12 34 56 78, maria@example.com"
    name, phone, email = extract_contact_info(text)
    assert name is None
    assert phone == "+31 6 12 34 56 78"
    assert email == "maria@example.com"


def test_recognizes_offered_by_case_insensitively():
    text = "Offered by City Living Rentals. Call 06-98765432."
    name, phone, email = extract_contact_info(text)
    assert name == "City Living Rentals"
    assert phone == "06-98765432"


def test_no_false_positive_on_price_only_text():
    text = "A lovely furnished room, priced at 895 euros per month, available now."
    name, phone, email = extract_contact_info(text)
    assert name is None
    assert phone is None
    assert email is None
