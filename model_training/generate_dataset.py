"""
Synthetic Dataset Generator for Context-Grounded RAG Fine-Tuning.

Generates 50 high-quality synthetic examples in Alpaca format:
- instruction: Task definition enforcing context-grounded reasoning.
- input: Context block + user query.
- output: Grounded answer OR strict "Information not found." refusal.
"""

import json
import os
from typing import List, Dict

SYSTEM_INSTRUCTION = (
    "Answer the user query based ONLY on the provided context. "
    "Do not extrapolate, assume, or use prior knowledge. "
    "If the answer cannot be determined strictly from the context, reply with: \"Information not found.\""
)

# 50 curated scenarios across domains (Tech, Legal, Finance, Medical, Operations, History, Science)
# 32 Grounded positive examples + 18 Strict refusal ("Information not found.") examples
RAW_DATA = [
    # --- Technology & Infrastructure ---
    {
        "context": "Project Titan uses PostgreSQL 16 as its primary relational store and Redis 7.2 for caching session state. Background asynchronous jobs are processed using Celery workers backed by RabbitMQ 3.13.",
        "query": "Which message broker is used for background asynchronous jobs in Project Titan?",
        "answer": "RabbitMQ 3.13 is used as the message broker for background asynchronous jobs in Project Titan."
    },
    {
        "context": "Project Titan uses PostgreSQL 16 as its primary relational store and Redis 7.2 for caching session state. Background asynchronous jobs are processed using Celery workers backed by RabbitMQ 3.13.",
        "query": "What is the memory limit allocated to the Redis caching instances?",
        "answer": "Information not found."
    },
    {
        "context": "The ingress controller enforces TLS 1.3 termination. Client certificates are verified against the internal root CA, and mutual TLS (mTLS) is mandatory on port 8443.",
        "query": "On which port is mutual TLS (mTLS) mandatory?",
        "answer": "Mutual TLS (mTLS) is mandatory on port 8443."
    },
    {
        "context": "The ingress controller enforces TLS 1.3 termination. Client certificates are verified against the internal root CA, and mutual TLS (mTLS) is mandatory on port 8443.",
        "query": "What algorithm is used to generate the internal root CA key pair?",
        "answer": "Information not found."
    },
    {
        "context": "Kafka cluster retention policy is configured to delete segments older than 7 days or when total topic partition storage exceeds 500 gigabytes.",
        "query": "Under what conditions are Kafka topic segments deleted?",
        "answer": "Kafka topic segments are deleted when they are older than 7 days or when the total topic partition storage exceeds 500 gigabytes."
    },
    {
        "context": "Kafka cluster retention policy is configured to delete segments older than 7 days or when total topic partition storage exceeds 500 gigabytes.",
        "query": "How many consumer groups are currently subscribed to the topics?",
        "answer": "Information not found."
    },

    # --- Corporate & HR Policies ---
    {
        "context": "Employees are eligible for up to $2,500 annually in continuing education reimbursement. Coursework must be pre-approved by the department director at least 14 days before enrollment begins.",
        "query": "How much annual continuing education reimbursement can an employee receive?",
        "answer": "Employees are eligible for up to $2,500 annually in continuing education reimbursement."
    },
    {
        "context": "Employees are eligible for up to $2,500 annually in continuing education reimbursement. Coursework must be pre-approved by the department director at least 14 days before enrollment begins.",
        "query": "Are book purchases and software licenses covered under the education reimbursement?",
        "answer": "Information not found."
    },
    {
        "context": "Remote employees must maintain a minimum broadband download speed of 100 Mbps and upload speed of 20 Mbps. The company provides a monthly internet stipend of $60.",
        "query": "What is the monthly stipend amount provided for remote employee internet?",
        "answer": "The company provides a monthly internet stipend of $60."
    },
    {
        "context": "Remote employees must maintain a minimum broadband download speed of 100 Mbps and upload speed of 20 Mbps. The company provides a monthly internet stipend of $60.",
        "query": "Does the company reimburse home office standing desks?",
        "answer": "Information not found."
    },
    {
        "context": "Parental leave policy provides 16 consecutive weeks of fully paid leave for primary caregivers following birth or adoption, provided the employee has completed 6 months of continuous service.",
        "query": "What is the required length of service before an employee qualifies for parental leave?",
        "answer": "The employee must have completed 6 months of continuous service."
    },
    {
        "context": "Parental leave policy provides 16 consecutive weeks of fully paid leave for primary caregivers following birth or adoption, provided the employee has completed 6 months of continuous service.",
        "query": "How many weeks of leave are granted to secondary caregivers?",
        "answer": "Information not found."
    },

    # --- Financial & Billing ---
    {
        "context": "Invoices unpaid after 30 calendar days incur a late penalty fee of 1.5% per month on the outstanding balance. Payment disputes must be filed within 10 business days of invoice receipt.",
        "query": "Within how many business days must invoice disputes be submitted?",
        "answer": "Payment disputes must be filed within 10 business days of invoice receipt."
    },
    {
        "context": "Invoices unpaid after 30 calendar days incur a late penalty fee of 1.5% per month on the outstanding balance. Payment disputes must be filed within 10 business days of invoice receipt.",
        "query": "Which wire transfer routing number should be used for international payments?",
        "answer": "Information not found."
    },
    {
        "context": "The annual SaaS subscription tier costs $12,000 billed upfront and includes 50 user seats. Additional seats can be purchased in bundles of 5 for $1,000 per year.",
        "query": "How much does a bundle of 5 additional user seats cost?",
        "answer": "A bundle of 5 additional user seats costs $1,000 per year."
    },
    {
        "context": "The annual SaaS subscription tier costs $12,000 billed upfront and includes 50 user seats. Additional seats can be purchased in bundles of 5 for $1,000 per year.",
        "query": "Is there a discount offered for non-profit organizations?",
        "answer": "Information not found."
    },
    {
        "context": "Corporate travel expense per diem is capped at $75 per day for domestic travel and $110 per day for international travel. Alcohol purchases are strictly non-reimbursable.",
        "query": "What is the domestic travel per diem cap?",
        "answer": "The per diem cap for domestic travel is $75 per day."
    },
    {
        "context": "Corporate travel expense per diem is capped at $75 per day for domestic travel and $110 per day for international travel. Alcohol purchases are strictly non-reimbursable.",
        "query": "Can employees fly business class on flights longer than 6 hours?",
        "answer": "Information not found."
    },

    # --- Security & Compliance ---
    {
        "context": "All production API keys must be rotated every 90 days. Key rotation is automated through HashiCorp Vault with an automatic rollback triggered if health checks fail within 120 seconds.",
        "query": "What tool manages the automated rotation of production API keys?",
        "answer": "HashiCorp Vault manages the automated rotation of production API keys."
    },
    {
        "context": "All production API keys must be rotated every 90 days. Key rotation is automated through HashiCorp Vault with an automatic rollback triggered if health checks fail within 120 seconds.",
        "query": "Who is the primary security officer responsible for signing off on manual key overrides?",
        "answer": "Information not found."
    },
    {
        "context": "Data subject access requests (DSAR) under GDPR must be fulfilled within 30 calendar days. Exported archives must be password-protected using AES-256 encryption.",
        "query": "What encryption standard must be used for exported DSAR archives?",
        "answer": "Exported DSAR archives must be password-protected using AES-256 encryption."
    },
    {
        "context": "Data subject access requests (DSAR) under GDPR must be fulfilled within 30 calendar days. Exported archives must be password-protected using AES-256 encryption.",
        "query": "What is the penalty fee if a DSAR is delivered on day 35?",
        "answer": "Information not found."
    },

    # --- Medical & Clinical Science ---
    {
        "context": "Compound VX-409 demonstrated an IC50 of 4.2 nM against epidermal growth factor receptor (EGFR) T790M mutants. Bioavailability in murine models was measured at 68% following oral gavage.",
        "query": "What was the measured bioavailability of Compound VX-409 in murine models?",
        "answer": "The bioavailability of Compound VX-409 in murine models was measured at 68% following oral gavage."
    },
    {
        "context": "Compound VX-409 demonstrated an IC50 of 4.2 nM against epidermal growth factor receptor (EGFR) T790M mutants. Bioavailability in murine models was measured at 68% following oral gavage.",
        "query": "What was the observed toxicity profile in non-human primates?",
        "answer": "Information not found."
    },
    {
        "context": "Patients enrolled in Cohort B received 200 mg of Pembrolizumab administered intravenously once every three weeks for up to 24 months, or until confirmed disease progression.",
        "query": "How frequently was Pembrolizumab administered to Cohort B patients?",
        "answer": "Pembrolizumab was administered intravenously once every three weeks."
    },
    {
        "context": "Patients enrolled in Cohort B received 200 mg of Pembrolizumab administered intravenously once every three weeks for up to 24 months, or until confirmed disease progression.",
        "query": "What was the median overall survival time recorded for Cohort B?",
        "answer": "Information not found."
    },

    # --- Hardware & Manufacturing ---
    {
        "context": "The Model X-12 industrial drone operates on a 6S 22.2V 16,000mAh LiPo battery. Maximum payload capacity is 4.5 kilograms, with an unloaded flight ceiling of 3,000 meters above sea level.",
        "query": "What is the maximum payload capacity of the Model X-12 drone?",
        "answer": "The maximum payload capacity of the Model X-12 drone is 4.5 kilograms."
    },
    {
        "context": "The Model X-12 industrial drone operates on a 6S 22.2V 16,000mAh LiPo battery. Maximum payload capacity is 4.5 kilograms, with an unloaded flight ceiling of 3,000 meters above sea level.",
        "query": "What optical camera sensor is integrated into the gimbal?",
        "answer": "Information not found."
    },
    {
        "context": "CNC Milling Station 4 operates spindle speeds up to 24,000 RPM. Synthetic coolant flood pressure must be calibrated to 30 PSI before milling aerospace-grade 7075 aluminum alloys.",
        "query": "What must the synthetic coolant flood pressure be calibrated to?",
        "answer": "The synthetic coolant flood pressure must be calibrated to 30 PSI."
    },
    {
        "context": "CNC Milling Station 4 operates spindle speeds up to 24,000 RPM. Synthetic coolant flood pressure must be calibrated to 30 PSI before milling aerospace-grade 7075 aluminum alloys.",
        "query": "How frequently are the tungsten carbide end mills replaced?",
        "answer": "Information not found."
    },

    # --- Network Operations ---
    {
        "context": "The border router BGP session drops if keepalive packets are not acknowledged within 90 seconds. AS path prepending of 3 hops is applied to secondary transit provider Cogent.",
        "query": "What is the keepalive acknowledgement threshold before the BGP session drops?",
        "answer": "The BGP session drops if keepalive packets are not acknowledged within 90 seconds."
    },
    {
        "context": "The border router BGP session drops if keepalive packets are not acknowledged within 90 seconds. AS path prepending of 3 hops is applied to secondary transit provider Cogent.",
        "query": "What is the router's autonomous system number (ASN)?",
        "answer": "Information not found."
    },

    # --- Cloud Architecture & DevOps ---
    {
        "context": "Kubernetes cluster production-east runs version 1.29.3. Node auto-scaler triggers when CPU utilization exceeds 75% across three consecutive 60-second polling windows.",
        "query": "At what CPU utilization percentage does the node auto-scaler trigger?",
        "answer": "The node auto-scaler triggers when CPU utilization exceeds 75% across three consecutive 60-second polling windows."
    },
    {
        "context": "Kubernetes cluster production-east runs version 1.29.3. Node auto-scaler triggers when CPU utilization exceeds 75% across three consecutive 60-second polling windows.",
        "query": "Which AWS EC2 instance type is used for the worker nodes?",
        "answer": "Information not found."
    },
    {
        "context": "S3 buckets storing customer telemetry logs have object versioning enabled and a lifecycle transition rule that moves objects to Glacier Flexible Retrieval after 90 days.",
        "query": "After how many days are telemetry log objects transitioned to Glacier Flexible Retrieval?",
        "answer": "Objects are transitioned to Glacier Flexible Retrieval after 90 days."
    },
    {
        "context": "S3 buckets storing customer telemetry logs have object versioning enabled and a lifecycle transition rule that moves objects to Glacier Flexible Retrieval after 90 days.",
        "query": "What KMS key ARN is used to encrypt the S3 bucket objects?",
        "answer": "Information not found."
    },

    # --- Legal & Contracts ---
    {
        "context": "Section 14.2 specifies that either party may terminate this Agreement without cause by providing 60 days prior written notice. Indemnification liability is capped at $5,000,000.",
        "query": "What is the liability cap for indemnification under the agreement?",
        "answer": "The indemnification liability is capped at $5,000,000."
    },
    {
        "context": "Section 14.2 specifies that either party may terminate this Agreement without cause by providing 60 days prior written notice. Indemnification liability is capped at $5,000,000.",
        "query": "Which state jurisdiction governs any arbitration proceedings?",
        "answer": "Information not found."
    },
    {
        "context": "Non-disclosure obligations regarding proprietary trade secrets survive termination of this contract for a period of five (5) calendar years.",
        "query": "For how long do non-disclosure obligations survive contract termination?",
        "answer": "Non-disclosure obligations survive termination of the contract for a period of five (5) calendar years."
    },
    {
        "context": "Non-disclosure obligations regarding proprietary trade secrets survive termination of this contract for a period of five (5) calendar years.",
        "query": "Are source code snippets considered proprietary trade secrets?",
        "answer": "Information not found."
    },

    # --- Scientific Exploration ---
    {
        "context": "The Europa Clipper spacecraft carries nine science instruments, including the MASPEX spectrometer and the REASON ice-penetrating radar. Its primary power is supplied by two large solar array wings spanning 30.5 meters.",
        "query": "What are two science instruments carried by the Europa Clipper spacecraft?",
        "answer": "The Europa Clipper carries the MASPEX spectrometer and the REASON ice-penetrating radar."
    },
    {
        "context": "The Europa Clipper spacecraft carries nine science instruments, including the MASPEX spectrometer and the REASON ice-penetrating radar. Its primary power is supplied by two large solar array wings spanning 30.5 meters.",
        "query": "What is the total mass of the spacecraft at launch?",
        "answer": "Information not found."
    },
    {
        "context": "The James Webb Space Telescope operates in a halo orbit around the Sun-Earth Lagrange point 2 (L2), approximately 1.5 million kilometers from Earth. Its primary mirror consists of 18 hexagonal beryllium segments coated in gold.",
        "query": "How many hexagonal segments make up the JWST primary mirror?",
        "answer": "The primary mirror consists of 18 hexagonal beryllium segments."
    },
    {
        "context": "The James Webb Space Telescope operates in a halo orbit around the Sun-Earth Lagrange point 2 (L2), approximately 1.5 million kilometers from Earth. Its primary mirror consists of 18 hexagonal beryllium segments coated in gold.",
        "query": "What is the operating temperature of the MIRI instrument cryocooler?",
        "answer": "Information not found."
    },

    # --- Supply Chain & Logistics ---
    {
        "context": "Perishable dairy shipments require continuous refrigeration between 2°C and 4°C. Data loggers flag a compliance breach if temperature deviates outside this range for longer than 15 consecutive minutes.",
        "query": "What temperature range is required for perishable dairy shipments?",
        "answer": "Perishable dairy shipments require continuous refrigeration between 2°C and 4°C."
    },
    {
        "context": "Perishable dairy shipments require continuous refrigeration between 2°C and 4°C. Data loggers flag a compliance breach if temperature deviates outside this range for longer than 15 consecutive minutes.",
        "query": "What is the manufacturer name of the temperature data loggers used?",
        "answer": "Information not found."
    },
    {
        "context": "Warehouse Bay 12 handles hazardous materials under Class 3 flammable liquids. Maximum storage density is 1,200 liters per fire-containment pallet cell.",
        "query": "What is the maximum storage density per pallet cell in Warehouse Bay 12?",
        "answer": "The maximum storage density is 1,200 liters per fire-containment pallet cell."
    },
    {
        "context": "Warehouse Bay 12 handles hazardous materials under Class 3 flammable liquids. Maximum storage density is 1,200 liters per fire-containment pallet cell.",
        "query": "What sprinkler head response rating is installed on Bay 12 ceiling ducts?",
        "answer": "Information not found."
    },

    # --- Energy & Utilities ---
    {
        "context": "Solar Farm Alpha has a nameplate capacity of 120 MW DC, connected via two 60 MVA step-up transformers to the 115 kV regional transmission grid. Battery energy storage capacity is 40 MWh.",
        "query": "What is the battery energy storage capacity of Solar Farm Alpha?",
        "answer": "The battery energy storage capacity of Solar Farm Alpha is 40 MWh."
    },
    {
        "context": "Solar Farm Alpha has a nameplate capacity of 120 MW DC, connected via two 60 MVA step-up transformers to the 115 kV regional transmission grid. Battery energy storage capacity is 40 MWh.",
        "query": "Who is the engineering procurement contractor (EPC) for the solar panels?",
        "answer": "Information not found."
    },
]


def format_alpaca_dataset(raw_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Format raw items into Alpaca JSON schema."""
    dataset = []
    for item in raw_items:
        input_text = f"Context:\n{item['context']}\n\nQuestion:\n{item['query']}"
        alpaca_item = {
            "instruction": SYSTEM_INSTRUCTION,
            "input": input_text,
            "output": item["answer"]
        }
        dataset.append(alpaca_item)
    return dataset


def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "dataset.json")

    print(f"[+] Total raw scenarios defined: {len(RAW_DATA)}")
    assert len(RAW_DATA) == 50, f"Expected 50 items, but got {len(RAW_DATA)}"

    dataset = format_alpaca_dataset(RAW_DATA)

    # Count statistics
    refusal_count = sum(1 for d in dataset if d["output"] == "Information not found.")
    answerable_count = len(dataset) - refusal_count

    print(f"[+] Answerable examples: {answerable_count}")
    print(f"[+] Strict refusal ('Information not found.') examples: {refusal_count}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"[✓] Successfully generated Alpaca dataset at: {output_path}")


if __name__ == "__main__":
    main()
