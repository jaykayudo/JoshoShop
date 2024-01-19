
# JOSHO SHOP

An Ecommerce store for selling various items that support international sales and is built on django.


## Run Locally
Clone the project

```bash
  git clone https://github.com/jaykayudo/JoshoShop.git
```

Go to the project directory

```bash
  cd joshshop
```
Install all packages
```bash
  pip install -r requirements.txt
```
[optional] Edit your hosts to add .com domain for social authentication.
```bash
  Edit your C:\Windows\System32\Drivers\etc\hosts on Windows 
  OR
  /etc/hosts on MacOS or Linux
  
  Add 127.0.0.1 joshoshop.com
```
Run the server with ssl 
```bash
  python manage.py runserver_plus --cert-file cert.crt
```
Run celery worker for background processes
```bash
  celery -A shoppingDen worker -l info
```
Access the Application on 127.0.0.1:8000 or www.joshoshop.com

### Note:
You will not be able to access Single Sign On if you do not add a domain to your host file

## Features

- Single Sign On with Google
- Session saved cart object
- Translation and language dynamic urls
- Internalization
- Recommendation Engine
- Payment Gateway
- Product Filter by Price
- Product Filter by Categories
- Pdf Invoice
- Asynchoronous tasks with celery
- Custom context processors
- Search
- Review System
-



## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET`

`SOCIAL_AUTH_GOOGLE_OAUTH2_KEY`

`PAYSTACK_SECRET_KEY`

`PAYSTACK_PUBLIC_KEY`
## Screenshots

![App Screenshot](https://res.cloudinary.com/ds81lsf2c/image/upload/v1705696668/Capture1_xmygzd.jpg)

![App Screenshot](https://res.cloudinary.com/ds81lsf2c/image/upload/v1705696666/Capture2_hl3wca.jpg)

![App Screenshot](https://res.cloudinary.com/ds81lsf2c/image/upload/v1705696666/Capture3_hajer8.jpg)

![App Screenshot](https://res.cloudinary.com/ds81lsf2c/image/upload/v1705696663/Capture_z01tzw.jpg)
