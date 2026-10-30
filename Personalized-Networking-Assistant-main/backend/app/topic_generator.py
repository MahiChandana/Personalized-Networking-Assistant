import re
import random
from transformers import pipeline


class TopicGenerator:
    def __init__(self, use_gpt2_wildcard: bool = False):
        """
        use_gpt2_wildcard: if True, we *attempt* one GPT-2 generated starter
        as a bonus alongside the template-based ones, but only keep it if it
        passes strict coherence validation. Templates are always the
        reliable backbone, since base gpt2 is not instruction-tuned and
        frequently produces incoherent or semantically nonsensical
        continuations even when grammatically valid.
        """
        self.use_gpt2_wildcard = use_gpt2_wildcard
        self.generator = None
        if use_gpt2_wildcard:
            self.generator = pipeline(
                "text-generation",
                model="gpt2",
                pad_token_id=50256
            )

    # ------------------------------------------------------------------
    # Bio parsing
    # ------------------------------------------------------------------
    _STOPWORDS = {
        "i", "am", "a", "an", "the", "and", "or", "to", "in", "on", "of",
        "with", "for", "is", "are", "my", "me", "this", "that", "these",
        "those", "who", "like", "enjoy", "working", "student", "specializing",
        "interested"
    }

    def _extract_interests(self, bio: str, max_items: int = 4) -> list:
        """Pull plausible interest phrases out of a free-text bio."""
        if not bio:
            return []

        chunks = re.split(r",|\band\b|\.", bio)
        candidates = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            words = chunk.split()
            if 1 <= len(words) <= 4:
                lowered = chunk.lower()
                if lowered not in self._STOPWORDS and not all(
                    w.lower() in self._STOPWORDS for w in words
                ):
                    candidates.append(chunk.strip(" ."))

        seen = set()
        deduped = []
        for c in candidates:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        return deduped[:max_items] if deduped else []

    # ------------------------------------------------------------------
    # Event topic extraction (the important part for specificity)
    # ------------------------------------------------------------------
    def _extract_event_topics(self, event_desc: str, max_items: int = 5) -> list:
        """
        Pull concrete named topics out of the event description, e.g.
        'Kubernetes', 'Docker', 'AWS', 'serverless computing' — rather than
        relying only on the broad theme label from the classifier.
        """
        if not event_desc:
            return []

        candidates = []

        # 1. Look for explicit list patterns: "discussing X, Y, and Z"
        list_pattern = re.search(
            r"(?:discussing|covering|focusing on|about|explore[s]?|on)\s+([^.]+)",
            event_desc,
            re.IGNORECASE
        )
        if list_pattern:
            raw_list = list_pattern.group(1)
            # Split on commas and "and"
            items = re.split(r",|\band\b", raw_list)
            for item in items:
                item = item.strip(" .")
                words = item.split()
                if 1 <= len(words) <= 4 and item:
                    candidates.append(item)

        # 2. Also catch standalone acronyms / capitalized tech terms anywhere
        #    in the text (AWS, Azure, Kubernetes, Docker, NLP, etc.)
        acronym_like = re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", event_desc)
        common_words = {"This", "The", "These", "Those", "That", "Event", "Conference"}
        for word in acronym_like:
            if word not in common_words:
                candidates.append(word)

        # De-dupe, preserve order, drop overly generic single words
        generic = {"transportation", "technology", "business", "software"}
        seen = set()
        deduped = []
        for c in candidates:
            key = c.lower()
            if key not in seen and key not in generic and len(c) > 2:
                seen.add(key)
                deduped.append(c)

        return deduped[:max_items]

    # ------------------------------------------------------------------
    # Template-based generation (reliable backbone)
    # ------------------------------------------------------------------
    def _build_template_starters(self, bio: str, themes: list, event_desc: str) -> list:
        theme = themes[0] if themes else "this field"
        interests = self._extract_interests(bio)
        event_topics = self._extract_event_topics(event_desc)

        # Pick a concrete event topic if we found one, else fall back to the theme
        topic_a = random.choice(event_topics) if event_topics else theme
        topic_b = random.choice(event_topics) if len(event_topics) > 1 else theme
        interest = random.choice(interests) if interests else theme

        templates = [
            f"How do you think {topic_a} can help solve real challenges in {interest}?",
            f"Which {topic_a} techniques do you think are most useful for {interest}?",
            f"What are the biggest challenges you've seen in applying {topic_a} to {interest}?",
            f"How does your work with {interest} connect with {topic_a} here at this event?",
            f"What's a practical use case for {topic_a} that actually worked well for you?",
            f"Given your background in {interest}, where do you see {topic_b} heading next?",
            f"What's the most surprising thing you've learned about {topic_a} recently?",
        ]

        # Remove any that accidentally repeat the same term on both sides (reads oddly)
        templates = [t for t in templates if not (topic_a.lower() in interest.lower() or interest.lower() in topic_a.lower())]

        random.shuffle(templates)
        return templates if templates else [
            f"What's your take on the biggest opportunity in {theme} right now?"
        ]

    # ------------------------------------------------------------------
    # GPT-2 wildcard generation with strict validation (optional, off by default)
    # ------------------------------------------------------------------
    def _is_coherent(self, phrase: str) -> bool:
        if not phrase or len(phrase) < 15:
            return False
        words = phrase.lower().split()
        if len(words) < 4:
            return False
        from collections import Counter
        counts = Counter(words)
        if counts.most_common(1)[0][1] > max(2, len(words) // 3):
            return False
        if re.search(r"[^\w\s\.\,\?\!\'\-]{2,}", phrase):
            return False
        for a, b in zip(words, words[1:]):
            if a == b:
                return False
        return True

    def _generate_gpt2_wildcard(self, bio: str, themes: list, event_desc: str) -> str | None:
        if not self.generator:
            return None
        theme_str = ", ".join(themes) if themes else "Artificial Intelligence"
        t1 = themes[0] if themes else "AI"
        prompt = (
            f"Event: {event_desc}\n"
            f"My Background: {bio}\n"
            f"Extracted Themes: {theme_str}\n"
            f"Conversation Starter: \"How do you think we can best implement "
        )
        try:
            outputs = self.generator(
                prompt,
                max_new_tokens=30,
                num_return_sequences=1,
                temperature=0.85,
                do_sample=True,
                clean_up_tokenization_spaces=False,
            )
            generated_text = outputs[0]["generated_text"]
            raw_output = generated_text[len(prompt):].strip()
            clean_phrase = raw_output.split("\n")[0].split("?")[0].strip().strip('"')
            if not self._is_coherent(clean_phrase):
                return None
            return f"How do you think we can best implement {clean_phrase}?"
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_starters(self, bio: str, themes: list, event_desc: str) -> list:
        starters = []

        if self.use_gpt2_wildcard:
            wildcard = self._generate_gpt2_wildcard(bio, themes, event_desc)
            if wildcard:
                starters.append(wildcard)

        template_starters = self._build_template_starters(bio, themes, event_desc)
        for t in template_starters:
            if len(starters) >= 3:
                break
            if t not in starters:
                starters.append(t)

        return starters[:3]