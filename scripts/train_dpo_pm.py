from __future__ import annotations

import argparse
from pathlib import Path

from rpl.pref_data import export_trl_dpo_jsonl, load_preference_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a LoRA DPO preference model.")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--train", default="data/pref_pairs/train.jsonl", help="Preference pair train JSONL")
    parser.add_argument("--val", default="data/pref_pairs/val.jsonl", help="Preference pair val JSONL")
    parser.add_argument("--work-dir", default="data/dpo", help="Converted DPO data directory")
    parser.add_argument("--out", default="data/pm_checkpoints/dpo_pm", help="Output adapter directory")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--max-length", type=int, default=768)
    parser.add_argument("--max-prompt-length", type=int, default=512)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--use-4bit", action="store_true", help="Use bitsandbytes 4-bit loading if available")
    args = parser.parse_args()

    train_path = Path(args.work_dir) / "train.jsonl"
    val_path = Path(args.work_dir) / "val.jsonl"
    train_count = export_trl_dpo_jsonl(load_preference_jsonl(args.train), train_path)
    val_count = export_trl_dpo_jsonl(load_preference_jsonl(args.val), val_path)
    if train_count == 0:
        raise SystemExit("No DPO training records found. Run cold_start.py --export first.")

    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from trl import DPOConfig, DPOTrainer
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing DPO dependencies. Install on the CUDA machine, for example:\n"
            "pip install torch transformers datasets accelerate peft trl bitsandbytes"
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs = {"trust_remote_code": True, "torch_dtype": torch.float16}
    if args.use_4bit:
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)
    if args.use_4bit:
        model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, peft_config)

    data_files = {"train": str(train_path)}
    if val_count > 0:
        data_files["validation"] = str(val_path)
    dataset = load_dataset("json", data_files=data_files)

    training_args = DPOConfig(
        output_dir=args.out,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        logging_steps=1,
        save_strategy="epoch",
        eval_strategy="epoch" if val_count > 0 else "no",
        remove_unused_columns=False,
        report_to=[],
        max_length=args.max_length,
        bf16=False,
        fp16=False,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset.get("validation"),
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(args.out)
    tokenizer.save_pretrained(args.out)
    print(f"saved dpo adapter to {args.out}")


if __name__ == "__main__":
    main()
