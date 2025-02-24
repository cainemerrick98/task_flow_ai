"""
this will use the mistral ai api to identify the task from the message model
"""
from app.message_service.models import Message
from mistralai import Mistral
import os
import json
from app.ai_agents.models import Task       
from datetime import datetime

class TaskIdentifier:
    def __init__(self):
        self.mistral = Mistral(api_key=os.getenv("MISTRAL_TOKEN"))

    def identify_task(self, message: Message) -> str:
        print(f"Identifying task for message: {message}")
        return self.mistral.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": """
                 
                 You will be given a message from the users work email or slack and you need to identify if the message contains a task and if so return the task in a json format.
                 Remember this is for work so the task should be something that is work related.

                 The json should have the following fields:
                 - task: a short title for the task
                 - due_date: the due date of the task - this should be in the format YYYY-MM-DD - if no due date is found return None
                 - description: the description of the task

                 if the message does not contain a task return None

                 Four examples of messages that contain tasks:
                 
                 Message 1:
                 Subject: Website Update Request
                 From: manager@company.com
                 Body: Hi team, we need to update the pricing page on our website by next Friday. Please make sure to include the new enterprise tier pricing and update all the feature comparisons.
                 
                 Expected Response:
                 {
                     "title": "Update Website Pricing Page",
                     "due_date": "2024-01-19",
                     "description": "Update pricing page to include new enterprise tier pricing and feature comparison updates"
                 }

                 Message 2:
                 Subject: Q4 Report Draft Review
                 From: finance@company.com
                 Body: Please review the attached Q4 financial report draft and provide feedback by January 25th. Focus particularly on the revenue projections section.
                 
                 Expected Response:
                 {
                     "title": "Review Q4 Financial Report",
                     "due_date": "2024-01-25", 
                     "description": "Review Q4 financial report draft with focus on revenue projections section"
                 }

                 Message 3:
                 Subject: Team Meeting Notes
                 From: teammate@company.com
                 Body: Can you help document the action items from today's meeting? We need to prepare the client presentation slides and send them for internal review.
                 
                 Expected Response:
                 {
                    "title": "Prepare Client Presentation",
                     "due_date": None,
                     "description": "Create presentation slides for client and submit for internal review"
                 }

                 Two examples of a message that does not contain a task:

                 Message 4:
                 Subject: Project Status Update
                 From: projectmanager@company.com
                 Body: Here's the latest status update on the project. We're on track for the deadline.
                 
                 Expected Response:
                 None   

                 Message 5:
                 Subject: Holiday Sale Announcement
                 From: marketing@company.com
                 Body: Just wanted to let everyone know that our holiday sale is live! 25% off all products until December 31st. Check it out at company.com/sale
                 
                 Expected Response:
                 None

                 Todays date is {datetime.now().strftime("%Y-%m-%d")} - this is important to know for the due date 

                 """
                 },
                {"role": "user", "content": str(message)}
            ]
        ).choices[0].message.content

    def parse_response(self, response: str) -> Task:
        print(f"Parsing response: {response}")
        try:
            # If response explicitly indicates no task
            if response.lower().strip() in ["none", "none.", "```json\nnone\n```"]:
                return None
            
            # Clean up the response by removing markdown code blocks if present
            cleaned_response = response
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[-1]
                cleaned_response = cleaned_response.split("```")[0]
            
            # Remove any "Based on the provided message" prefix text
            if "based on" in cleaned_response.lower():
                return None
            
            # Strip whitespace and parse JSON
            cleaned_response = cleaned_response.strip()
            print(f"Cleaned response: {cleaned_response}")
            return Task(**json.loads(cleaned_response))
        
        except json.JSONDecodeError:
            print(f"Error parsing response: {response}")
            return None

    def get_task(self, message: Message) -> Task|None:
        response = self.identify_task(message)
        return self.parse_response(response)
    

