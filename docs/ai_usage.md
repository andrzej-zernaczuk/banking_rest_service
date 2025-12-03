# AI Usage

## Tools
During the developement I used mainly two tools:
- ChatGPT 5.1
- Copilot

My first step was to create separate project in ChatGPT with requirements file and then I asked for the project overview while claryifing technologies I want to use - Python and SQLlite.

Copilot was used mainly for autocompletion and for explaining some lines of code that I was not sure of in terms of behavior, for example `deprecated="auto"` in `CryptContext`.


## Prompts
Below you can see examples of my prompts:
- *In this project we aim to fulfill test assessment goals for the job of Forward Deployed Data Engineer. Lets prepare the outline for the project: main components, technologies, road map etc. We do not aim to prepare front end due to lack of time. I'm programming in python.*
-*Have in mind that I'm using uv. I've already created venv and ran uv init. We'll fill pyproject.toml during the developement. Let us design the DB first. Lets have in mind the required service interfaces: Signing up Authentication Account Holders Accounts Transactions Money Transfer Cards Statements firstly lets create focus on the top level. What tables do we need, how are we gonna structure them. Remember we have to use sqlite, that is non negotiable*
- *Lets be more strict with Account Holder. Lets not accept user creation without DoB, national_id_number, phone_number. Also I don't think full_name is correct approach, lets separate it into first_name and last_name - this might be needed even for simple things like saying "hello <name>" on front page*
- *Generate documentation for the code we wrote so far. Lets describe clearly the aim of the project, technologies, structure of the project etc. Make it easy to copy to markdown file.*