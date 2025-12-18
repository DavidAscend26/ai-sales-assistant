import httpx
from app.core.config import settings
from app.core.errors import ExternalServiceError

class TwilioSender:
    def __init__(self) -> None:
        self.sid = settings.TWILIO_ACCOUNT_SID
        self.token = settings.TWILIO_AUTH_TOKEN
        self.from_whatsapp = settings.TWILIO_WHATSAPP_FROM

    async def send_whatsapp(self, to_number: str, body: str) -> None:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json"
        data = {"From": self.from_whatsapp, "To": to_number, "Body": body}
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, data=data, auth=(self.sid, self.token))
            if r.status_code >= 400:
                raise ExternalServiceError(f"Twilio error {r.status_code}: {r.text[:200]}")