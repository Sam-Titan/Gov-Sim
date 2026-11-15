from scripts.parse_sample_sizes import parse_sample


def test_parse_sample_sentence_across_line_break() -> None:
    text = "In Patna, information was gathered from 897 households,\n 1,942 women, and 143 men."
    assert parse_sample(text) == (897, 1942, 143)


def test_parse_sample_missing() -> None:
    assert parse_sample("nothing here") is None
