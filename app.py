from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from scraper import scrape_vulnerabilities
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['vulnwatch']
vuln_collection = db['vulnerabilities']

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    url = request.form['url']
    if url:
        vulnerabilities = scrape_vulnerabilities(url)
        new_vulns = store_vulnerabilities(vulnerabilities)
        if new_vulns:
            send_email_alert(new_vulns)
        flash('Vulnerability check complete. Email alerts sent for new vulnerabilities.')
    else:
        flash('Please enter a valid URL.')
    return redirect(url_for('index'))

# Store new vulnerabilities in MongoDB
def store_vulnerabilities(vulnerabilities):
    new_vulns = []
    for vuln in vulnerabilities:
        if vuln_collection.count_documents({'description': vuln['description']}) == 0:
            vuln_collection.insert_one(vuln)
            new_vulns.append(vuln)
    return new_vulns

# Send email alert for new vulnerabilities
def send_email_alert(vulnerabilities):
    sender_email = "youremail@example.com"
    receiver_email = "alert@example.com"
    password = "yourpassword"
    
    subject = "VulnWatch Alert: New Vulnerabilities Detected"
    text = "New vulnerabilities detected:\n\n"
    for vuln in vulnerabilities:
        text += f"Product: {vuln['product_name']}\nSeverity: {vuln['severity']}\nDescription: {vuln['description']}\nMitigation: {vuln['mitigation']}\n\n"

    message = MIMEText(text)
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = receiver_email

    with smtplib.SMTP_SSL("smtp.example.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

if __name__ == '__main__':
    app.run(debug=True)
