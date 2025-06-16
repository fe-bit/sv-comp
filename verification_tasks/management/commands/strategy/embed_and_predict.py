from verification_tasks.models import VerificationTask, VerificationCategory
from verifiers.models import Verifier
from .data import EvaluationStrategySummary
from benchmarks.models import Benchmark
from tqdm import tqdm
from chromadb import Collection
import torch
import torch.nn as nn
import numpy as np


class VerifierRegressor(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, output_dim=3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            # nn.Linear(hidden_dim, hidden_dim),
            # nn.LayerNorm(hidden_dim),
            # nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


def round_and_sanitize_outputs(outputs: np.ndarray) -> np.ndarray:
    outputs = np.atleast_2d(outputs)
    # Vectorized rounding and clipping for the score (first column)
    scores = np.round(outputs[:, 0])
    scores = np.clip(scores, -3, 2)
    # Replace the first column with the sanitized scores
    sanitized = outputs.copy()
    sanitized[:, 0] = scores
    return sanitized

def evaluate_embed_and_predict(vts_test: list[int], test_collection: Collection) -> EvaluationStrategySummary:
    model = VerifierRegressor(input_dim=296, hidden_dim=64, output_dim=1)
    # model.load_state_dict(torch.load("verifier_regressor_model.pth", map_location="cpu"))
    model.load_state_dict(torch.load("verifier_score_model.pth", map_location="cpu"))
    model.eval()
    num_categories = VerificationCategory.objects.count()
    num_verifiers = Verifier.objects.count()

    print("Number of categories:", num_categories)
    print("Number of verifiers:", num_verifiers)
    print("Embeddigns: ", 228)
    print("Total number of dimensions:", 228 + num_categories + num_verifiers)

    summary = EvaluationStrategySummary()
    vts = VerificationTask.objects.filter(id__in=vts_test)
    for vt in tqdm(vts, desc="Processing Embed&Predict"):
        entry = test_collection.get(str(vt.pk), include=["embeddings"])
        try:
            embedding = entry["embeddings"][0] if "embeddings" in entry else None
        except Exception as e:
            print(f"Error retrieving embedding for VerificationTask {vt.pk}: {e}")
            continue
        
        verifier_results = []
        for verifier in Verifier.objects.all():
            verifier_one_hot = torch.nn.functional.one_hot(
                torch.tensor(verifier.pk-1),
                num_classes=num_verifiers
            ).float()
            category_one_hot = torch.nn.functional.one_hot(
                torch.tensor(vt.category.pk-1),
                num_classes=num_categories
            ).float()
            embedding_tensor = torch.tensor(embedding, dtype=torch.float32)
            full_embedding = torch.cat([embedding_tensor, category_one_hot, verifier_one_hot])
            full_embedding.to("cpu")
            with torch.no_grad():
                outputs = model(full_embedding).cpu().numpy()
            # outputs = round_and_sanitize_outputs(outputs)
            score = outputs[0]
            # cpu = outputs[0][1]
            # memory = outputs[0][2]
            verifier_results.append({
                "verifier": verifier,
                "score": score,
                # "cpu": cpu,
                # "memory": memory,
            })

        verifier_results.sort(key=lambda x: (-x["score"]))
        best = verifier_results[0]
        best_predicted_verifier = best["verifier"]
        benchmark = Benchmark.objects.filter(
            verification_task=vt,
            verifier=best_predicted_verifier
        ).order_by("-raw_score", "cpu", "memory").first()
        if benchmark is None:
            continue
        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
