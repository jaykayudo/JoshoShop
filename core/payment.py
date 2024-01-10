import requests
from django.conf import settings

class Paystack:
    def __init__(self):
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.initialize_payment_url = "https://api.paystack.co/transaction/initialize"
        self.verify_payment_url = "https://api.paystack.co/transaction/verify/{}"
        self.verify_account_url = "https://api.paystack.co/transferrecipient"
        self.banks_url = "https://api.paystack.co/bank?currency=NGN"
        self.resolve_account_url = "https://api.paystack.co/bank/resolve?account_number={}&bank_code={}"
        self.transfer_url = "https://api.paystack.co/transfer"
        self.headers = {
            'Authorization': f"Bearer {self.secret_key}"
        }
    
    def initalize_payment(self,email,amount,success_url,ref=None,):
        payload = {
            'email':email,
            'amount': int(amount) * 100,
            'callback_url': success_url,

        }
        if ref:
            payload['reference'] = ref
        
        request = requests.post(self.initialize_payment_url,data=payload,headers=self.headers)
        return request.json()
    def verify_payment(self,ref):
        url = self.verify_payment_url.format(ref)
        request = requests.get(url, headers=self.headers)
        return request.json()
    def make_transfer(self,amount,ref, recipient,source="balance",reason="JOSHO SHOP Wallet Withdrawal"):
        payload = {
            "amount":int(amount) * 100,
            "recipient": recipient,
            "ref":ref,
            "source":source,
            "reason":reason
        }
        request = requests.post(self.transfer_url,payload,headers=self.headers)
        response = request.json()
        return response
        
    def banks(self):
        def map_function(x):
            data = {
                "name": x['name'],
                "code": x["code"],
                "type":x['type']
            }
            return data
        request = requests.get(self.banks_url,headers=self.headers)
        # print(request)
        response = request.json()
        
        if response['status']:
            response_data = response["data"]
            bank_data = list(map(map_function,response_data))
            return bank_data
        else:
            return []
    def resolve_account(self,account_number,bank_code):
        url = self.resolve_account_url.format(account_number,bank_code)
        request = requests.get(url,headers=self.headers)
        return request.json()

    def bank_recipient(self,type,name,account_number,bank_code,currency="NGN"):
        payload = {
            "type":type,
            "name": name,
            "account_number":account_number,
            "bank_code":bank_code,
            "currency":currency
        }
        request = requests.post(self.verify_account_url,payload,headers=self.headers)
        return request.json()

        
            