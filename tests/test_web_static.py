import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebStaticTests(unittest.TestCase):
    def test_setup_uses_clear_baseline_and_movement_language(self):
        html = (ROOT / "web" / "index.html").read_text()

        self.assertIn("Record empty room baseline", html)
        self.assertIn("Record movement at base", html)
        self.assertNotIn(">Create layout<", html)
        self.assertNotIn(">Capture base<", html)

    def test_audio_starts_only_when_game_is_seeking(self):
        js = (ROOT / "web" / "app.js").read_text()

        api_function = js.split("async function api", 1)[1].split("function render", 1)[0]
        self.assertNotIn("ensureAudio()", api_function)
        self.assertIn("const audioActive = state.mode === \"seeking\";", js)
        self.assertIn("setAudioWarmth(warmth, audioActive);", js)
        self.assertIn("stopAudio();", js)


if __name__ == "__main__":
    unittest.main()
