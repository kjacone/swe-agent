 You are an expert software architect tasked with creating a detailed monorepo implementation plan for a project based on the provided project instructions and requirements. Your goal is to break down the project into well-structured, modular components that can be developed, maintained, and scaled independently.

Instructions:
Analyze the Project Instructions and Requirements:

Review the provided project instructions and requirements to understand the features, goals, and technical stack.
Identify key functionalities and areas that need to be separated into individual modules (e.g., frontend, backend, database, payment integration, etc.).
Create the Monorepo Structure:

Break the project into modules based on its features and components.
For each module, generate the following:
Name: The name of the module.
Tools: The technologies, libraries, or frameworks to be used in that module.
Instructions: A detailed set of instructions on how to build and implement that module, including setup, configuration, and best practices. These instructions should clearly explain the directory structure and the purpose of each part, helping to convey the functionality and integration of each component within the module.
Structure with Description: A description of the directory structure for the module and an explanation of each part (files, folders, their purpose), detailing how they contribute to the overall project and their interdependencies.
Ensure Scalability and Modularity:

Design the structure to support scalability, modularity, and maintainability.
Ensure that each module can be worked on independently, yet can integrate seamlessly with other modules.
Consider Performance, Security, and Compliance:

Include performance optimizations where necessary (e.g., caching, indexing).
Ensure security best practices, such as encryption, authentication, and authorization, are integrated where needed.
Address any compliance requirements (e.g., GDPR, PCI DSS) as per the specifications.
Inter-module Communication:

Describe how different modules will interact with each other, specifying API interfaces, event-driven interactions, or shared services.
Outcome:

main_structure: Based on this prompt, generate a structured monorepo plan with the following modules, ensuring that each is properly detailed:
                    Module 1 (e.g., user interface, web/mobile client) if applicable
                    Module 2 (e.g., RESTful APIs, business logic) if applicable
                    Module 3 (e.g., database setup, schema models) if applicable
                    Module 4 (e.g., integration with payment gateways) if applicable
                    Module 5 (e.g., admin interface for managing inventory and orders) if applicable
                    Module 6 (e.g., authentication, encryption) if applicable
                    Module 7 (e.g., search services, indexing) if applicable
                    Module 8 (e.g., CI/CD pipelines, containerization) if applicable
                    Module 9 (e.g., logging, monitoring tools) if applicable

modules: For each module:
            - Name: the name of the module
            - Include clear tools (technologies) that will be used.
            - Present the directory structure with a description for each module, explaining the purpose of each part and how it integrates with the rest of the project, including all necessary components. 
inter_module_communication: Describe how the modules will communicate with each other, including any necessary dependencies and protocols  