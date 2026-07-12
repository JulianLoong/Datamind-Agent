from rpl.pref_model.model import (
    LightweightPrefModel,
    MockPrefModel,
    PrefModel,
    train_lightweight_pref_model,
)

__all__ = [
    "BaseModelPrefModel",
    "DPOPrefModel",
    "LightweightPrefModel",
    "MockPrefModel",
    "PrefModel",
    "train_lightweight_pref_model",
]


def __getattr__(name: str):
    if name == "DPOPrefModel":
        from rpl.pref_model.dpo import DPOPrefModel

        return DPOPrefModel
    if name == "BaseModelPrefModel":
        from rpl.pref_model.dpo import BaseModelPrefModel

        return BaseModelPrefModel
    raise AttributeError(name)
