#!/usr/bin/env python3
"""
Headless Training Script for Grounded RAG Fine-Tuning with Unsloth.

Formats training examples using Meta Llama-3's native Chat Template
(<|begin_of_text|><|start_header_id|>...) via Unsloth's get_chat_template.
"""

import os
import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel, is_bfloat16_supported
from unsloth.chat_templates import get_chat_template


def main():
    print("=" * 60)
    print("Unsloth Grounded RAG Fine-Tuning (QLoRA) - Llama-3 Chat Format")
    print("=" * 60)

    # 1. Hardware validation
    if not torch.cuda.is_available():
        print("[!] Warning: CUDA is not available. Unsloth requires an NVIDIA GPU (CUDA).")
    else:
        print(f"[+] GPU detected: {torch.cuda.get_device_name(0)}")
        print(f"[+] Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    # 2. Hyperparameters
    max_seq_length = 2048
    dtype = None  # Auto-detection (Float16 or Bfloat16)
    load_in_4bit = True

    # 3. Model & Tokenizer initialization
    print("\n[+] Loading base model: unsloth/llama-3-8b-Instruct-bnb-4bit ...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/llama-3-8b-Instruct-bnb-4bit",
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
    )

    # 4. Attach QLoRA adapters
    print("[+] Configuring QLoRA adapters (r=16, alpha=16) ...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )

    # 5. Apply Unsloth's native Llama-3 Chat Template
    print("[+] Applying native Llama-3 chat template to tokenizer ...")
    tokenizer = get_chat_template(
        tokenizer,
        chat_template="llama-3",
    )

    # 6. Format dataset using tokenizer.apply_chat_template
    dataset_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.json")
    if not os.path.exists(dataset_file):
        raise FileNotFoundError(f"dataset.json not found at {dataset_file}. Run generate_dataset.py first.")

    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs = examples["input"]
        outputs = examples["output"]
        texts = []
        for instruction, input_text, output in zip(instructions, inputs, outputs):
            messages = [
                {"role": "system", "content": instruction},
                {"role": "user", "content": input_text},
                {"role": "assistant", "content": output},
            ]
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
            texts.append(text)
        return {"text": texts}

    print(f"[+] Loading dataset from {dataset_file} ...")
    dataset = load_dataset("json", data_files=dataset_file, split="train")
    dataset = dataset.map(formatting_prompts_func, batched=True)
    print(f"[+] Total samples formatted: {len(dataset)}")
    print(f"[+] Sample formatted prompt prefix:\n{dataset[0]['text'][:250]}...\n")

    # 7. SFTTrainer setup
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            num_train_epochs=1,
            learning_rate=2e-4,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir=output_dir,
            report_to="none",
        ),
    )

    print("\n[+] Starting training for 1 epoch ...")
    trainer.train()
    print("[✓] Training completed.")

    # 8. Export to 4-bit GGUF (q4_k_m)
    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_grounded_llama3")
    print(f"\n[+] Exporting model to 4-bit GGUF (q4_k_m) in '{export_dir}' ...")
    model.save_pretrained_gguf(
        export_dir,
        tokenizer,
        quantization_method="q4_k_m"
    )
    print(f"[✓] GGUF export complete! Target directory: {export_dir}")


if __name__ == "__main__":
    main()
