from transformers import pipeline

class EventAnalyzer:
    def __init__(self):
        # Initializing the public zero-shot model you selected
        self.classifier = pipeline(
            "zero-shot-classification",
            model="valhalla/distilbart-mnli-12-1"
        )
        # Defining candidate labels directly inside the engine instance
        # Expanded to cover more specific tech domains, so events like
        # cloud/DevOps summits don't collapse into a generic "Technology" label.
        self.default_labels = [
            "Artificial Intelligence", "Machine Learning", "Sustainability",
            "Blockchain", "Healthcare", "Urban Planning", "Climate Change",
            "Software Development", "Cloud Computing", "DevOps",
            "Cybersecurity", "Data Science", "Technology", "Business"
        ]

    def extract_themes(self, event_description: str) -> list:
        if not event_description.strip():
            return []

        # Run classification against internal labels
        result = self.classifier(event_description, self.default_labels)

        # Return labels that have a high confidence score (> 0.25)
        themes = [label for label, score in zip(result['labels'], result['scores']) if score > 0.25]

        # Fallback to the top 2 highest scoring themes if none pass the threshold
        return themes if themes else result['labels'][:2]