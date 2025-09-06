#!/usr/bin/env python3
"""
Model Warmer - Keep GPT-OSS model loaded and ready
Run this script in the background to keep your model cached
"""

import requests
import json
import time
import argparse
from datetime import datetime
import schedule
import threading

class ModelWarmer:
    def __init__(self, model_name="gpt-oss:20b", base_url="http://localhost:11434", keep_alive="30m"):
        self.model_name = model_name
        self.base_url = base_url
        self.keep_alive = keep_alive
        self.is_running = False
        
    def check_ollama_status(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_model_loaded(self):
        """Check if our model is currently loaded"""
        try:
            response = requests.get(f"{self.base_url}/api/ps", timeout=5)
            if response.status_code == 200:
                models = response.json()
                for model in models.get('models', []):
                    if model['name'] == self.model_name:
                        return True
            return False
        except:
            return False
    
    def warm_model(self):
        """Send a warming request to keep model loaded"""
        if not self.check_ollama_status():
            print(f"❌ Ollama not running at {self.base_url}")
            return False
            
        payload = {
            "model": self.model_name,
            "keep_alive": self.keep_alive,
            "messages": [{"role": "user", "content": "ping"}],
            "stream": False
        }
        
        try:
            print(f"🔄 Warming {self.model_name} at {datetime.now().strftime('%H:%M:%S')}")
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Model warmed successfully")
                return True
            else:
                print(f"❌ Failed to warm model: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error warming model: {e}")
            return False
    
    def start_warming_schedule(self, interval_minutes=25):
        """Start periodic warming schedule"""
        print(f"🚀 Starting model warmer for {self.model_name}")
        print(f"   Keep-alive: {self.keep_alive}")
        print(f"   Warming interval: {interval_minutes} minutes")
        print(f"   Ollama URL: {self.base_url}")
        
        # Initial warm-up
        self.warm_model()
        
        # Schedule periodic warming
        schedule.every(interval_minutes).minutes.do(self.warm_model)
        
        self.is_running = True
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the warming schedule"""
        self.is_running = False
        print("🛑 Model warmer stopped")

def main():
    parser = argparse.ArgumentParser(description="Keep GPT-OSS model warm and ready")
    parser.add_argument("--model", default="gpt-oss:20b", help="Model name to keep warm")
    parser.add_argument("--url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--keep-alive", default="30m", help="How long to keep model loaded")
    parser.add_argument("--interval", type=int, default=25, help="Warming interval in minutes")
    parser.add_argument("--once", action="store_true", help="Warm once and exit")
    
    args = parser.parse_args()
    
    warmer = ModelWarmer(args.model, args.url, args.keep_alive)
    
    if args.once:
        # Just warm once and exit
        success = warmer.warm_model()
        exit(0 if success else 1)
    else:
        # Run continuous warming
        try:
            warmer.start_warming_schedule(args.interval)
        except KeyboardInterrupt:
            print("\n🛑 Stopping model warmer...")
            warmer.stop()

if __name__ == "__main__":
    main()
