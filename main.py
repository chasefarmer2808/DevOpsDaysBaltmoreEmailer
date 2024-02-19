import os.path
import base64
import csv
import argparse
import pick
import glob
import email_templates

from email.message import EmailMessage
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.compose"]
COMMAND_SPONSOR = 'cold_sponsor'
COMMAND_TICKETS = 'ticket_announcement'
COMMAND_OPTS = [
    {
        'id': COMMAND_SPONSOR,
        'short_description': 'Create cold sponsor drafts'
    },
    {
        'id': COMMAND_TICKETS,
        'short_description': 'Create ticket announcement drafts'
    }
]

creds = None


def login():
    """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def create_cold_sponsor_draft(creds, to_email, from_emails, from_name, contact_name, sponsor_company):
    if contact_name is None or contact_name == "":
        contact_name = "there"

    try:
        # create gmaiil api client
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        content = """
      Hello {}!

      We're excited to announce that DevOpsDays is returning to Baltimore!  From what we know of {}, your organization seems 
      like it would be a good fit for sponsorship. We wanted to present you with an opportunity to engage with the thriving tech 
      community of the Baltimore metro area.<br />
      <br />
      DevOpsDays is a worldwide series of technical conferences covering topics of software development, IT infrastructure operations, 
      and the intersection between them. This is the 4th year of the Baltimore DevOpsDays event.  This year's event will be returning 
      to the IMET in the Inner Harbor of Baltimore on May 23rd-24th.  We expect around 250 IT professionals from the Baltimore Metro 
      and DMV areas.<br />
      <br />
      The services available for each sponsor level can be found on our <a href="https://devopsdays.org/events/2023-baltimore/sponsor" target="_blank">Sponsor page</a>, 
      and additional questions may be addressed by our <a href="https://docs.google.com/document/d/1W7a6wikgCoBSvW2yeGUhYDR3dERGnk43/edit?usp=sharing&ouid=105937644192212593428&rtpof=true&sd=true" target="_blank">FAQ</a>.<br />
      <br />
      What other questions can I answer for you?  If you'd like, I'd be happy to jump on a call to talk about the best approaches to sponsorship.<br />
      <br />
      -{}, and the rest of the DevOpsDays Baltimore Team
    """.format(contact_name, sponsor_company, from_name)

        message["To"] = to_email
        message["From"] = from_emails
        message["Subject"] = f'DevOpsDays Baltimore Sponsorship - {sponsor_company}'
        message.add_header('Content-Type', 'text/html')
        message.set_payload(content)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"message": {"raw": encoded_message}}

        draft = (
            service.users().drafts().create(userId="me", body=create_message).execute()
        )

        print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

    except HttpError as error:
        print(f"An error occurred: {error}")
        draft = None

    return draft


def create_create_draft_email(subject, content, creds, to_email, from_emails, contact_name):
    if contact_name is None or contact_name == "":
        contact_name = "there"

    try:
        # create gmail api client
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        content = content

        message["To"] = to_email
        message["From"] = from_emails
        message["Subject"] = subject
        message.add_header('Content-Type', 'text/html')
        message.set_payload(content)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"message": {"raw": encoded_message}}

        draft = (
            service.users().drafts().create(userId="me", body=create_message).execute()
        )

        print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

    except HttpError as error:
        print(f"An error occurred: {error}")
        draft = None

    return draft


def read_cold_contacts_from_csv(filename):
    cold_contacts = []

    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        print("Parsing CSV...")
        for row in reader:
            if row["Previous Sponsor?"].lower() == "no" and row["Initial Contact Email By"] == "":
                print(f'Found cold sponsor: {row["Company"]}')
                cold_contacts.append(row)

    print(f'Found {len(cold_contacts)} total cold sponsors')
    return cold_contacts


def read_attendees_from_csv(filename):
    attendees = []

    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        print("Parsing CSV...")
        for row in reader:
            attendees.append(row)

    print(f'Found {len(attendees)} previous attendees.')
    return attendees


def handle_args(args):
    command = next((comm for comm in COMMAND_OPTS if comm["id"] == args.command), None)
    csv_file = args.csv_file

    if command is None:
        option, index = pick.pick(
            [opt['short_description'] for opt in COMMAND_OPTS],
            "What would you like to do?",
            default_index=0
        )
        command = COMMAND_OPTS[index]

    if csv_file is None:
        csv_files = glob.glob('*.csv')
        option, index = pick.pick(
            csv_files,
            'Please select a data file to use:',
            default_index=0
        )
        csv_file = option

    if command['id'] is COMMAND_SPONSOR:
        pass
    elif command['id'] is COMMAND_TICKETS:
        handle_ticket_command(csv_file)
    else:
        raise IOError(f'Unsupported command {command}')


def handle_ticket_command(data_file):
    attendees = read_attendees_from_csv(data_file)

    draft_limit = len(attendees)

    if 'EMAIL_LIMIT' in os.environ:
        draft_limit = int(os.environ["EMAIL_LIMIT"])
    print(f'Creating drafts for {draft_limit} previous attendees...')

    for contact in attendees[:draft_limit]:
        email_opts = {
            'subject': 'DevOpsDays Baltimore 2024 Early Bird Tickets on Sale!',
            'to_email': contact["Email"],
            'from_name': os.environ["SENDER_NAME"],
            'content': email_templates.ticket_announcement(
                from_name=os.environ['SENDER_NAME'],
                attendee_name=contact['First Name'],
                prev_year='2023',
                curr_year='2024',
            )
        }

        print(f'Creating draft for {email_opts["to_email"]}...')
        create_draft(email_opts)
        print("done")


def create_draft(opts):
    global creds

    from_emails = ["baltimore@baltmoredevopsdays.org"]
    if 'SENDER_EMAIL' in os.environ:
        from_emails.append(os.environ['SENDER_EMAIL'])

    try:
        # create gmail api client
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        content = opts['content']

        message["To"] = opts['to_email']
        message["From"] = from_emails
        message["Subject"] = opts['subject']
        message.add_header('Content-Type', 'text/html')
        message.set_payload(content)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"message": {"raw": encoded_message}}

        draft = (
            service.users().drafts().create(userId="me", body=create_message).execute()
        )

        print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

    except HttpError as error:
        print(f"An error occurred: {error}")
        draft = None

    return draft


def main():
    global creds
    creds = login()
    print("Successfully logged in to Google.")
    print(f'Email Sender: {os.environ["SENDER_NAME"]}')

    parser = argparse.ArgumentParser(prog='DevOpsDays Emailer')
    parser.add_argument('--command', choices=[opt['id'] for opt in COMMAND_OPTS])
    parser.add_argument('--csv_file')
    args = parser.parse_args()

    handle_args(args)

    # cold_contacts = read_cold_contacts_from_csv("hitlist.csv")
    #
    # draft_limit = int(os.environ["EMAIL_LIMIT"])
    # print(f'Creating drafts for {draft_limit} sponsors...')
    # for contact in cold_contacts[:draft_limit]:
    #     to_email = contact["Email"]
    #     from_emails = ["cfarmer@baltimoredevopsdays.org", "baltimore@baltmoredevopsdays.org"]
    #     from_name = os.environ["SENDER_NAME"]
    #     contact_name = contact["Contact Name"]
    #     company = contact["Company"]
    #     print(f'Creating draft for {company}...')
    #     create_cold_sponsor_draft(creds, to_email, from_emails, from_name, contact_name, company)
    #     print("done")


if __name__ == "__main__":
    main()
