import random
def predict(wait, density):
    variance = random.randint(-8, 12)
    factor = {"Low": .85, "Moderate": 1, "High": 1.18, "Very High": 1.38}.get(density, 1)
    return max(10, round(wait * factor + variance))
