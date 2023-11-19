# DevOps Days Baltimore Emailer

Python tool for automating email sending via the @devopsdaysbaltimore.org gmail account.

## Getting Started

To run this tool, make sure Python 3 and Pip are installed. Then install dependencies with `pip install -r requirements.txt`.

Next, go to our current source of truth sponsor hitlist on the Baltimore DevOps Days Google Drive. Export that file to csv, and place it in the root of this project.

Next, create a file called `.env` and copy the contents of `.env.example` into it. Fill in the values as oppropriate. Descriptions of the environment vairables are below:

- `EMAIL_LIMIT` - Max number of draft emails to create. CSV parsing stops once this limit is reached, and before any drafts are created.
- `SENDER_NAME` - The name of the person sending the email to go in the email signature. Usually set to your first and last name.

Finally, run the tool with `python main.py`.
