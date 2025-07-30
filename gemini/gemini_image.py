import os
import sys
import base64
import warnings
import argparse
from io import BytesIO
from google import genai
from dotenv import load_dotenv
from PIL import Image
from datetime import datetime

# Suppress pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Load environment variables
load_dotenv()

class SimpleGeminiAnalyzer:
    def __init__(self):
        # Initialize client with API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        self.client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1alpha"}
        )
        self.model = "gemini-2.0-flash-exp"
    
    def resize_image_by_long_side(self, image, max_length=256):
        """Resize image based on longer side while keeping aspect ratio"""
        width, height = image.size
        
        # Skip resize if image is already smaller
        if max(width, height) <= max_length:
            return image
        
        if width > height:
            new_width = max_length
            new_height = int(height * max_length / width)
        else:
            new_height = max_length
            new_width = int(width * max_length / height)
        
        return image.resize((new_width, new_height), Image.LANCZOS)
    
    def analyze_image(self, image_path, prompt):
        """Analyze image with custom prompt"""
        try:
            # Load and resize image to 256px
            image = Image.open(image_path)
            original_size = image.size
            image = self.resize_image_by_long_side(image)
            resized_size = image.size
            
            # Encode image
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            image_data = base64.b64encode(buffered.getvalue()).decode()
            
            # Create request content
            contents = [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            }]
            
            # Send request
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            
            return {
                "success": True,
                "result": response.text,
                "image_info": {
                    "original_size": original_size,
                    "resized_size": resized_size,
                    "file_path": image_path
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "image_info": {
                    "file_path": image_path
                }
            }

def format_output(result):
    """Format analysis result for better readability"""
    print("\n" + "="*60)
    print("🖼️  GEMINI IMAGE ANALYSIS RESULT")
    print("="*60)
    
    if result["success"]:
        # Image information
        img_info = result["image_info"]
        print(f"📁 File: {img_info['file_path']}")
        print(f"📏 Original Size: {img_info['original_size'][0]}x{img_info['original_size'][1]}")
        print(f"🔧 Resized To: {img_info['resized_size'][0]}x{img_info['resized_size'][1]}")
        print(f"⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "-"*60)
        print("📋 ANALYSIS RESULT:")
        print("-"*60)
        
        # Clean and format the result text
        analysis_text = result["result"].strip()
        
        # Split into lines and format
        lines = analysis_text.split('\n')
        for line in lines:
            if line.strip():
                if line.strip().startswith('*'):
                    print(f"  {line.strip()}")
                elif "Full:" in line or "Empty:" in line:
                    print(f"\n🔍 {line.strip()}")
                else:
                    print(f"   {line.strip()}")
        
        print("\n" + "="*60)
        print("✅ Analysis completed successfully!")
        
    else:
        # Error case
        print(f"📁 File: {result['image_info']['file_path']}")
        print(f"⏰ Error Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "-"*60)
        print("❌ ERROR OCCURRED:")
        print("-"*60)
        print(f"   {result['error']}")
        
        print("\n" + "="*60)
        print("❌ Analysis failed!")
    
    print("")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Analyze images using Google Gemini 2.0 Flash API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --image ./images/shelf.jpg
  python main.py -i ./images/box.png
  python main.py --image ./test.jpg --prompt "Describe this image"
        """
    )
    
    parser.add_argument(
        '--image', '-i',
        type=str,
        default="./images/shelf2.jpg",
        help='Path to the image file (default: ./images/shelf2.jpg)'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        type=str,
        default="this is a box that has 2x3 grid and containing stuffs that is needed when the weather is rainy, dusty or etc, give me which blank is empty and which is full",
        help='Custom prompt for image analysis'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate image file exists
    if not os.path.exists(args.image):
        print(f"❌ Error: Image file '{args.image}' not found!")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        print("🚀 Initializing Gemini Analyzer...")
        analyzer = SimpleGeminiAnalyzer()
        
        print(f"📸 Analyzing image: {args.image}")
        print("⏳ Please wait...")
        
        # Analyze image
        result = analyzer.analyze_image(args.image, args.prompt)
        
        # Format and display result
        format_output(result)
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Please check your .env file and ensure GEMINI_API_KEY is set")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
