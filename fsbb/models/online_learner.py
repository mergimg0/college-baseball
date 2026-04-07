"""Online logistic regression with SGD weight updates.

NOT reinforcement learning — simple online SGD for logistic regression.
Updates weights after each game observation. Supports momentum, weight
decay, and cosine learning rate scheduling.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


class OnlineLogisticRegressor:
    """Online logistic regression with SGD updates."""

    def __init__(
        self,
        n_features: int,
        lr: float = 0.01,
        l2_reg: float = 0.1,
        momentum: float = 0.9,
    ):
        self.weights = np.zeros(n_features)
        self.lr = lr
        self.l2_reg = l2_reg
        self.momentum = momentum
        self.velocity = np.zeros(n_features)
        self.n_updates = 0
        self.recent_losses: list[float] = []

    def predict_proba(self, x: np.ndarray) -> float:
        """Predict P(y=1|x)."""
        z = float(x @ self.weights)
        z = max(-30, min(30, z))
        return 1.0 / (1.0 + math.exp(-z))

    def update(self, x: np.ndarray, y: float) -> float:
        """SGD update on single observation. Returns loss."""
        prob = self.predict_proba(x)
        loss = -(y * math.log(max(prob, 1e-10)) + (1 - y) * math.log(max(1 - prob, 1e-10)))

        # Gradient of cross-entropy + L2 regularization
        grad = (prob - y) * x + self.l2_reg * self.weights

        # Momentum SGD
        self.velocity = self.momentum * self.velocity - self.lr * grad
        self.weights += self.velocity

        self.n_updates += 1
        self.recent_losses.append(loss)
        if len(self.recent_losses) > 100:
            self.recent_losses.pop(0)

        return loss

    def rolling_brier(self, window: int = 50) -> float | None:
        """Rolling Brier score over recent predictions."""
        if len(self.recent_losses) < window:
            return None
        return sum(self.recent_losses[-window:]) / window

    def cosine_lr(self, step: int, total_steps: int, lr_min: float = 0.001) -> float:
        """Cosine annealing learning rate schedule."""
        return lr_min + (self.lr - lr_min) * 0.5 * (1 + math.cos(math.pi * step / total_steps))

    def save(self, path: Path) -> None:
        """Save model state to JSON."""
        state = {
            "weights": self.weights.tolist(),
            "n_updates": self.n_updates,
            "lr": self.lr,
            "l2_reg": self.l2_reg,
            "momentum": self.momentum,
            "recent_brier": self.rolling_brier(),
        }
        with open(path, "w") as f:
            json.dump(state, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "OnlineLogisticRegressor":
        """Load model state from JSON."""
        with open(path) as f:
            state = json.load(f)
        model = cls(
            n_features=len(state["weights"]),
            lr=state.get("lr", 0.01),
            l2_reg=state.get("l2_reg", 0.1),
            momentum=state.get("momentum", 0.9),
        )
        model.weights = np.array(state["weights"])
        model.n_updates = state.get("n_updates", 0)
        return model

    @classmethod
    def from_v1_model(cls, model_path: Path) -> "OnlineLogisticRegressor":
        """Initialize from trained V1 model (warm start)."""
        with open(model_path) as f:
            v1 = json.load(f)
        n_features = len(v1["weights"])
        model = cls(n_features=n_features)
        model.weights = np.array(v1["weights"])
        return model
