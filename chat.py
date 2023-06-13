import os
import random
import json

import torch
import matplotlib.pyplot as plt

from model import NeuralNet
from nltk_utils import bag_of_words, tokenize

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

json_dir = "json"
intents = {'intents': []}
for filename in os.listdir(json_dir):
    if filename.endswith(".json"):
        with open(os.path.join(json_dir, filename), "r") as f:
            intents['intents'].extend(json.load(f)['intents'])

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "Campus Companion"

def get_response(msg):
    print("Input Query:", msg)  # Debug statement

    sentence = tokenize(msg)
    print("Tokenized Sentence:", sentence)  # Debug statement

    X = bag_of_words(sentence, all_words)
    print("Bag of Words Representation:", X)  # Debug statement

    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    print("Output Tensor:", output)  # Debug statement
    print("Predicted Index:", predicted)  # Debug statement

    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                return random.choice(intent['responses'])

    return "Sorry, I do not understand..."

def evaluate_accuracy(test_data):
    total = len(test_data)
    correct = 0

    for data in test_data:
        sentence = data['sentence']
        expected_tag = data['tag']

        predicted_response = get_response(sentence)
        
        print("Expected Tag:", expected_tag)  # Debug statement
        print("Predicted Responce:", predicted_response)  # Debug statement
      
        
        for intent in intents['intents']:
            if expected_tag == intent["tag"] and predicted_response in intent['responses']:
                correct += 1
                break

    accuracy = correct / total
    return accuracy



if __name__ == "__main__":
    print("Let's chat! (type 'quit' to exit)")

    test_data = [
        {
            'sentence': 'Hi',
            'tag': 'greeting'
        },
         {
            'sentence': 'What are the programs offered in CN',
            'tag': 'CN_Programs',

        },
         {
            'sentence': 'So can you give me the Programs offered in CCIT',
            'tag': 'CCIT_Programs',

        },
         {
            'sentence': 'What is the email of the College of Architecture?',
            'tag': 'CA_email',

        },
         {
            'sentence': 'How can I contact the CCIT College?',
            'tag': 'CCIT_email',

        },
          {
            'sentence': 'Who are the faculties belong to the college of engineering?',
            'tag': 'CE_Faculties',

        },
          {
            'sentence': 'CE Faculties?',
            'tag': 'CE_Faculties',

        },
         {
            'sentence': 'Hello, I am cyrus',
            'tag': 'greeting'
        },

         {
            'sentence': 'What is the mission of unp?',
            'tag': 'UNP_Vision_Mission_CoreValues'
        },
       {
            'sentence': 'Who is the dean of the College of Arts and Sciences?',
            'tag': 'CAS_Dean'
        },
         
          {
            'sentence': 'Who is the dean of CCIt',
            'tag': 'CCIT_Dean'
        },{
            'sentence': 'what are the available programs in college of architecture',
            'tag': 'CA_Programs'
        },{
            'sentence': 'Programs offered in CA',
            'tag': 'CA_Programs'
        },{
            'sentence': 'Can you provide me the programs that i can apply into the college of architecture?',
            'tag': 'CA_Programs'
        },


       
       
       
        # Add more test data sentences and expected tags...
    ]

    accuracy = evaluate_accuracy(test_data)
 

    # Plotting the accuracy
    x = [i for i in range(1, len(test_data) + 1)]
    y = [evaluate_accuracy(test_data[:i]) * 100 for i in range(1, len(test_data) + 1)]

    plt.plot(x, y)
    plt.xlabel('Number of Test Sentences')
    plt.ylabel('Accuracy')
    plt.title('Campus Companion Accuracy')
    plt.text(len(test_data), max(y) -1, f'Accuracy: {accuracy * 100:.2f}%', ha='right')

    print(f"Accuracy: {accuracy * 100}%")

    plt.show()


