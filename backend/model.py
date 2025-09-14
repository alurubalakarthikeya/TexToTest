from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Change this to a slightly bigger Pythia model if you want better quality
MODEL_NAME = "EleutherAI/pythia-410m"

print("Downloading and loading model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# Use device=-1 for CPU
generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=-1  # CPU
)

def generate_text(prompt: str):
    outputs = generator(
        prompt,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.7
    )
    return outputs[0]["generated_text"]
