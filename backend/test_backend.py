#!/usr/bin/env python3
"""
Test script for the TexToTest backend with distractor generation
"""

import requests
import json
import os
import sys

BASE_URL = os.environ.get("BASE_URL") or (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")

def test_health():
    """Test the health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())
    return response.status_code == 200

def test_upload_sample_text():
    """Test uploading a sample text file"""
    # Create a sample text file
    sample_text = """
    Albert Einstein was a German-born theoretical physicist who developed the theory of relativity, 
    one of the two pillars of modern physics. His work is also known for its influence on the 
    philosophy of science. He was born in Ulm, in the Kingdom of Württemberg in the German Empire, 
    on 14 March 1879. Einstein received the 1921 Nobel Prize in Physics for his services to 
    theoretical physics, and especially for his discovery of the law of the photoelectric effect, 
    a pivotal step in the development of quantum theory.
    
    Isaac Newton was an English mathematician, physicist, astronomer, theologian, and author who 
    is widely recognised as one of the greatest mathematicians and physicists of all time. 
    He was born on 4 January 1643 in Woolsthorpe-by-Colsterworth, Lincolnshire, England. 
    Newton formulated the laws of motion and universal gravitation that formed the dominant 
    scientific viewpoint until it was superseded by the theory of relativity.
    """
    
    # Write to a temporary file
    with open("sample_text.txt", "w") as f:
        f.write(sample_text)
    
    # Upload the file
    with open("sample_text.txt", "rb") as f:
        files = {"file": ("sample_text.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    # Clean up
    os.remove("sample_text.txt")
    
    print("Upload Response:", response.json())
    return response.status_code == 200

def test_generate_questions():
    """Test generating multiple choice questions"""
    data = {
        "num_questions": 5,
        "question_type": "multiple_choice"
    }
    
    response = requests.post(f"{BASE_URL}/ask-model", json=data)
    result = response.json()
    
    print("Generated Questions:")
    print(json.dumps(result, indent=2))
    
    return response.status_code == 200

def main():
    """Run all tests"""
    print("Testing TexToTest Backend with Distractor Generation")
    print("=" * 60)
    print(f"BASE_URL = {BASE_URL}")
    
    # Test health
    if not test_health():
        print("❌ Health check failed")
    sys.exit(1)
    print("✅ Health check passed")
    
    # Test upload
    if not test_upload_sample_text():
        print("❌ Upload test failed")
    sys.exit(1)
    print("✅ Upload test passed")
    
    # Test question generation
    if not test_generate_questions():
        print("❌ Question generation test failed")
        sys.exit(1)
    print("✅ Question generation test passed")
    
    print("\n🎉 All tests passed! The backend is working correctly.")
    sys.exit(0)

if __name__ == "__main__":
    main()