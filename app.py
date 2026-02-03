import sys
import os
sys.path.insert(0, '/app/.packages')

from flask import Flask, render_template, request, jsonify
import boto3
import json

# ... rest of your code

from flask import Flask, render_template, request, jsonify
import boto3
import json

app = Flask(__name__)

# Mumbai region
bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

def get_inventory_data():
    try:
        table = dynamodb.Table('GroceryInventory')
        response = table.scan()
        return response['Items']
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        return []

def get_recipes_data():
    try:
        table = dynamodb.Table('GroceryRecipes')
        response = table.scan()
        return response['Items']
    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return []

def generate_chat_response(user_message, inventory, recipes):
    try:
        context = f"""You are a helpful grocery inventory assistant. 
        
Current Inventory:
{json.dumps(inventory, indent=2)}

Available Recipes:
{json.dumps(recipes, indent=2)}

Answer questions about inventory levels, product availability, and recipe suggestions based on available ingredients."""

        messages = [
            {
                "role": "user",
                "content": f"{context}\n\nUser Question: {user_message}"
            }
        ]
        
        request_body = {
            "messages": messages,
            "inferenceConfig": {
                "max_new_tokens": 1000,
                "temperature": 0.7
            }
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-pro-v1:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['output']['message']['content'][0]['text']
    except Exception as e:
        return f"Error generating response: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    inventory = get_inventory_data()
    recipes = get_recipes_data()
    
    response = generate_chat_response(user_message, inventory, recipes)
    
    return jsonify({
        'response': response
    })

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    inventory = get_inventory_data()
    return jsonify(inventory)

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    recipes = get_recipes_data()
    return jsonify(recipes)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
