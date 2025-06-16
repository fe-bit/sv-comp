
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd

import torch
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
from collections import Counter



# Load the parquet file
df = pd.read_parquet("verification_benchmarks.parquet")
df = df[df['embedding'].notnull()]
df['raw_score'] = df['raw_score'].replace(-64, -3)
df['raw_score'] = df['raw_score'].replace(-32, -2)
df['raw_score'] = df['raw_score'].replace(-16, -1)

class_counts = Counter(df["raw_score"])
total = sum(class_counts.values())
weights = {k: total / v for k, v in class_counts.items()}  # Inverse frequency

del df  # Free memory


class VerifierDataset(Dataset):
    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        embedding, label = self.samples[idx]
        return embedding, label

dataset = torch.load("verifier_full_binary_dataset.pt")
# stack all labels
all_labels = torch.stack([label for _, label in dataset])  # shape (N, 3)

# Identify rows without NaNs
valid_mask = ~torch.isnan(all_labels).any(dim=1)
clean_labels = all_labels[valid_mask]

print("Filtered out", (~valid_mask).sum().item(), "rows with NaNs in labels")

# Now calculate stats from clean data
means = clean_labels.mean(dim=0)
stds = clean_labels.std(dim=0).clamp(min=1e-6)

train_samples, test_samples = train_test_split(dataset, test_size=0.2, random_state=42)


def clean_dataset(dataset):
    clean_samples = [(emb, label) for emb, label in dataset if not torch.isnan(label).any()]
    ds = VerifierDataset(clean_samples)
    return ds, DataLoader(ds, batch_size=32, shuffle=True)

train_ds, train_dataloader = clean_dataset(train_samples)
test_ds, test_dataloader = clean_dataset(test_samples)

def check_dataset_for_nans_and_infs(dataset):
    nan_count_emb = 0
    nan_count_lbl = 0
    inf_count_emb = 0
    inf_count_lbl = 0
    
    for i, (embedding, label) in enumerate(dataset):
        if torch.isnan(embedding).any():
            print(f"NaN in embedding at index {i}")
            nan_count_emb += 1
        if torch.isnan(label).any():
            print(f"NaN in label at index {i}")
            nan_count_lbl += 1
        if torch.isinf(embedding).any():
            print(f"Inf in embedding at index {i}")
            inf_count_emb += 1
        if torch.isinf(label).any():
            print(f"Inf in label at index {i}")
            inf_count_lbl += 1

    print(f"Total NaNs in embeddings: {nan_count_emb}")
    print(f"Total NaNs in labels: {nan_count_lbl}")
    print(f"Total Infs in embeddings: {inf_count_emb}")
    print(f"Total Infs in labels: {inf_count_lbl}")

check_dataset_for_nans_and_infs(train_ds)
check_dataset_for_nans_and_infs(test_ds)


class VerifierRegressor(nn.Module):
    def __init__(self, input_dim, hidden_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 3)
        )

    
    def forward(self, x):
        return self.net(x)




class WeightedMSELoss(nn.Module):
    def __init__(self, class_weights: dict):
        super().__init__()
        self.class_weights = class_weights

    def forward(self, preds, targets):
        # Weighted MSE for score (first column)
        score_targets = targets[:, 0]
        score_preds = preds[:, 0]
        weights = torch.tensor(
            [self.class_weights[float(t.item())] for t in score_targets],
            dtype=preds.dtype, device=preds.device
        )
        # Use the mean of the weights for the other dimensions
        mean_weight = weights.mean()
        # Weighted loss for all dimensions
        loss = torch.stack([
            weights * (score_preds - score_targets) ** 2,
            mean_weight * (preds[:, 1] - targets[:, 1]) ** 2,
            mean_weight * (preds[:, 2] - targets[:, 2]) ** 2
        ], dim=1)
        return loss.mean()

# nn.MSELoss()
model = VerifierRegressor(input_dim=dataset[0][0].shape[0], hidden_dim=64)
criterion = WeightedMSELoss(weights)
# optimizer = optim.Adam(model.parameters(), lr=1e-5)
optimizer = optim.Adam(model.parameters(), lr=1e-1)

device = torch.device("cpu")
model.to(device)


best_test_loss = float('inf')
best_model_state = None
patience = 5
epochs_no_improve = 0
epoch = 0

eval_steps = 25


while True:
    # Training phase
    epoch += 1
    model.train()
    total_loss = 0
    for embeddings, targets in train_dataloader:
        embeddings = embeddings.float()
        targets = targets.float()
        embeddings, targets = embeddings.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(embeddings)

        loss = criterion(outputs, targets)
        if torch.isnan(loss) or torch.isinf(loss):
            print("Loss is NaN or Inf! Stopping training.")
            break
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * embeddings.size(0)

    avg_train_loss = total_loss / len(train_ds)
    print(f"Epoch {epoch}, Train Loss: {avg_train_loss:.4f}")

    # Evaluation phase
    if epoch % eval_steps == 0:
        model.eval()
        total_test_loss = 0
        with torch.no_grad():
            for embeddings, targets in test_dataloader:
                embeddings = embeddings.float()
                targets = targets.float()
                embeddings, targets = embeddings.to(device), targets.to(device)

                outputs = model(embeddings)
                loss = criterion(outputs, targets)
                total_test_loss += loss.item() * embeddings.size(0)

        avg_test_loss = total_test_loss / len(test_ds)
        print(f"Epoch {epoch}, Test Loss: {avg_test_loss:.4f}")

        # Early stopping logic
        if avg_test_loss < best_test_loss - 1e-6:  # small epsilon to avoid float issues
            best_test_loss = avg_test_loss
            epochs_no_improve = 0
            best_model_state = model.state_dict()
        else:
            epochs_no_improve += 1
            print(f"No improvement for {epochs_no_improve} epochs.")
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch}")
                break

if best_model_state is not None:
    model = VerifierRegressor(input_dim=dataset[0][0].shape[0], hidden_dim=64)
    model.load_state_dict(best_model_state)
    print("Loaded best model state.")

torch.save(model.state_dict(), "verifier_regressor_model.pth")




def round_and_sanitize_outputs(outputs: np.ndarray) -> np.ndarray:
    outputs = np.atleast_2d(outputs)
    # Vectorized rounding and clipping for the score (first column)
    scores = np.round(outputs[:, 0])
    scores = np.clip(scores, -3, 2)
    # Replace the first column with the sanitized scores
    sanitized = outputs.copy()
    sanitized[:, 0] = scores
    return sanitized

def evaluate_model(model, dataloader, criterion):
    records = []
    model.eval()
    total_loss = 0
    total_samples = 0
    with torch.no_grad():
        for embeddings, targets in dataloader:
            embeddings = embeddings.float()
            targets = targets.float()
            embeddings, targets = embeddings.to(device), targets.to(device)

            outputs = model(embeddings)
            loss = criterion(outputs, targets)
            total_loss += loss.item() * embeddings.size(0)
            total_samples += embeddings.size(0)

            outputs = outputs.cpu().numpy()
            outputs = round_and_sanitize_outputs(outputs)

            # Compare with targets
            targets = targets.cpu().numpy()
            for t, p in zip(targets, outputs):
                records.append({
                    "Target-Score": t[0],
                    "Predicted-Score": p[0],
                    "Target-CPU": t[1],
                    "Predicted-CPU": p[1],
                    "Target-Memory": t[2],
                    "Predicted-Memory": p[2],
                })
    
    df = pd.DataFrame(records)
    avg_loss = total_loss / total_samples
    print(f"Evaluation loss on test set: {avg_loss:.4f}")
    return avg_loss, df


# Example usage after training:
avg_loss, df = evaluate_model(model, test_dataloader, criterion)
df["Score_Diff"] = round(df["Predicted-Score"], 0) - round(df["Target-Score"],0)
df["Predicted-Score"] = round(df["Predicted-Score"], 0).astype(int)
df["Target-Score"] = round(df["Target-Score"], 0).astype(int)

df["CPU-Diff"] = df["Predicted-CPU"] - df["Target-CPU"]
df["Memory-Diff"] = df["Predicted-Memory"] - df["Target-Memory"]
print(df["Score_Diff"].value_counts(normalize=True))
print(df["CPU-Diff"].describe())