# Grounded RAG Model Training & Serving Pipeline

This directory contains the complete end-to-end Machine Learning pipeline to fine-tune an open-source Large Language Model (`Llama-3-8B-Instruct`) for strict context-grounded Retrieval-Augmented Generation (RAG) and serve it as a local OpenAI-compatible API via Ollama.

---

## 1. Directory Structure

```text
model_training/
├── generate_dataset.py      # Generates 50 synthetic RAG grounding examples
├── dataset.json             # Synthetic training dataset
├── train_unsloth.ipynb      # Unsloth QLoRA notebook using native Llama-3 Chat Template
├── train_unsloth.py         # Headless CLI equivalent using native Llama-3 Chat Template
├── Modelfile                # Ollama definition with native Llama-3 template & strict prompt
├── serve.sh                 # Deployment script (builds Ollama model & verifies API)
├── test_inference.py        # OpenAI SDK verification script with token streaming
└── requirements.txt         # Python dependencies
```

---

## 2. Step-by-Step Workflow

### Step 1: Generate Grounded Dataset
Generate 50 synthetic examples balancing in-context factual queries and unanswerable out-of-context queries requiring strict `"Information not found."` refusals:

```bash
cd model_training
python3 generate_dataset.py
```
This produces `dataset.json`.

---

### Step 2: Fine-Tune with Unsloth (QLoRA) using Llama-3 Chat Template
Run either `train_unsloth.ipynb` on Google Colab / GPU instance or execute headless:

```bash
python3 train_unsloth.py
```

**Key Fine-Tuning Specifications:**
- **Base Model:** `unsloth/llama-3-8b-Instruct-bnb-4bit`
- **Chat Template:** Native Meta Llama-3 (`<|begin_of_text|><|start_header_id|>...`) via `get_chat_template(tokenizer, chat_template="llama-3")`
- **Adapter Type:** QLoRA ($r=16$, $\alpha=16$)
- **Target Modules:** `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
- **Training Strategy:** `SFTTrainer` (1 epoch, learning rate `2e-4`, linear schedule, 8-bit AdamW)
- **Quantized Export:** 4-bit `q4_k_m` GGUF format via `model.save_pretrained_gguf("rag_grounded_llama3", tokenizer, quantization_method="q4_k_m")`.

---

### Step 3: Deploy Locally with Ollama

Run the automated serving script:

```bash
chmod +x serve.sh
./serve.sh
```

This will:
1. Ensure the Ollama background daemon is running.
2. Build the local model `rag-llama3-grounded` using `Modelfile`.
3. Expose the OpenAI-compatible REST endpoint at `http://localhost:11434/v1/chat/completions`.

---

### Step 4: Verify with OpenAI Python Client (Streaming)

Run the automated streaming verification test:

```bash
python3 test_inference.py
```

The script tests two distinct scenarios:
1. **Positive Grounded Extraction:** Verifies that in-context facts are accurately retrieved.
2. **Negative Anti-Hallucination:** Verifies that queries without context support output strictly `"Information not found."`.
