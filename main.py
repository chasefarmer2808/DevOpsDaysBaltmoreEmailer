import os.path
import base64

from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.compose"]

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
  if contact_name is None:
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
    message.add_header('Content-Type','text/html')
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
  creds = login()
  create_cold_sponsor_draft(creds, "test@test.com", ["cfarmer@baltimoredevopsdays.org", "baltimore@baltmoredevopsdays.org"], "Chase Farmer", "test contact", "test company")

if __name__ == "__main__":
  main()
