import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "space"))
from utils import (  # noqa: E402
    validate_text, normalize_sentiment, normalize_emotions, text_stats, clean_caption, MAX_TEXT_CHARS,
)


class TestValidateText(unittest.TestCase):
    def test_strips(self):
        self.assertEqual(validate_text("  hi  "), "hi")

    def test_empty(self):
        for bad in (None, "", "   "):
            with self.assertRaises(ValueError):
                validate_text(bad)

    def test_too_long(self):
        with self.assertRaises(ValueError):
            validate_text("a" * (MAX_TEXT_CHARS + 1))


class TestNormalize(unittest.TestCase):
    def test_sentiment_nested_and_mapped(self):
        raw = [[{"label": "LABEL_2", "score": 0.9}, {"label": "LABEL_0", "score": 0.05}, {"label": "LABEL_1", "score": 0.05}]]
        out = normalize_sentiment(raw)
        self.assertEqual(out["label"], "positive")
        self.assertEqual(list(out["scores"])[0], "positive")

    def test_sentiment_named(self):
        out = normalize_sentiment([{"label": "negative", "score": 0.7}, {"label": "positive", "score": 0.3}])
        self.assertEqual(out["label"], "negative")

    def test_emotions_topk(self):
        raw = [[{"label": "joy", "score": 0.6}, {"label": "anger", "score": 0.1},
                {"label": "fear", "score": 0.2}, {"label": "sadness", "score": 0.1}]]
        out = normalize_emotions(raw, top_k=2)
        self.assertEqual([e["emotion"] for e in out], ["joy", "fear"])

    def test_stats(self):
        self.assertEqual(text_stats("Hello world. How are you?"), {"characters": 25, "words": 5, "sentences": 2})

    def test_caption(self):
        self.assertEqual(clean_caption([{"generated_text": "a dog on a beach"}]), "A dog on a beach.")
        self.assertEqual(clean_caption([]), "")


if __name__ == "__main__":
    unittest.main()
