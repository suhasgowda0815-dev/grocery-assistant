from flask import Flask, request, jsonify, render_template
import boto3
import json
import os

app = Flask(__name__)

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

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
        table = dynamodb.Table('Recipes')
        response = table.scan()
        return response['Items']
    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return []

def generate_chat_response(messages, inventory, recipes):
    try:
        context = f"Current grocery inventory: {json.dumps(inventory)}\n\nAvailable recipes: {json.dumps(recipes)}"
        
        enhanced_messages = []
        for i, msg in enumerate(messages):
            if i == 0 and msg["role"] == "user":
                enhanced_messages.append({
                    "role": "user",
                    "content": f"{context}\n\nUser question: {msg['content']}"
                })
            else:
                enhanced_messages.append(msg)
        
        request_body = {
            "messages": enhanced_messages,
            "inferenceConfig": {"max_new_tokens": 1000, "temperature": 0.7}
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

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    inventory = get_inventory_data()
    return jsonify(inventory)

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    recipes = get_recipes_data()
    return jsonify(recipes)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    
    inventory = get_inventory_data()
    recipes = get_recipes_data()
    
    response = generate_chat_response(messages, inventory, recipes)
    
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
