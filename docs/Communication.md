





# Communication Agent
Responsible for communicating with the client. It is the orchestrator of all of these steps. 

Communication output types:
- Update: this is an update about what the backend system is doing.
- Action: this is a specific action that the backend is taking.
- Data: this is some results or data the backend sends that the frontend should display.
- Instruction: this is a message that is informing the user to do something.
- Question: this is a message asking the user something. It expects a response. 

Communication input types:
- Request: a specific request from the user such as to start a diagnostic session, end something, etc.
- Answer: data/observations to directly reply to a question.
- Boolean: True or False answers to binary questions. 