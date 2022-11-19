from flask import Flask, render_template, request, redirect, url_for, session
#from werkzeug import secure_filename
import ibm_db
import json
import requests
import os
import http.client
import ibm_boto3
from ibm_botocore.client import Config, ClientError
# Constants for IBM COS values
COS_ENDPOINT = "https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "o2fzafy8wAQYk_C-E1BJ5LcPTwdc2cT4Ea50n_L_ZfOK" # eg "W00YixxxxxxxxxxMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_INSTANCE_CRN = "crn:v1:bluemix:public:iam-identity::a/2f7b464e4eb24decb578c313e2ee9872::serviceid:ServiceId-2aee878b-ae68-4929-84c3-44d40a01057e" # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003xxxxxxxxxx1c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"
# Create resource
cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)
app = Flask(__name__)
app.secret_key = "abc"  
#conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=3883e7e4-18f5-4afe-be8c-fa31c41761d2.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31498;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=sch83401;PWD=j7QZUHGAtUGbPhns",'','')
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=0c77d6f2-5da9-48a9-81f8-86b520b87518.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31198;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=tqz07844;PWD=8gtHDbCP5WHYQU9r",'','')
@app.route('/registration')
def home():
    return render_template('register.html')
@app.route('/r1',methods=['POST'])
def r1():
    x = [x for x in request.form.values()]
    print(x)
    name=x[0]
    password=x[1]
    email=x[2]
    phone=x[3]
    sql = "SELECT * FROM user_detail WHERE emailid =?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt,1,email)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print(account)
    if account:
        return render_template('register.html', pred="You are already a member, please login using your details")
    else:
        insert_sql = "INSERT INTO user_detail VALUES (?, ?, ?, ?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, name)
        ibm_db.bind_param(prep_stmt, 2, password)
        ibm_db.bind_param(prep_stmt, 3, email)
        ibm_db.bind_param(prep_stmt, 4, phone)
        ibm_db.execute(prep_stmt)
    return render_template('register.html', pred="Registration Successful, please login using your details")
@app.route('/')    
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/connect_api')
def connect_api():
    import http.client
    conn1 = http.client.HTTPSConnection("spoonacular-recipe-food-nutrition-v1.p.rapidapi.com")
    headers = {
    'X-RapidAPI-Key': "6309ee0c6dmshfaee35dae4e48f7p17bf91jsn5fc8607b2bb7",
    'X-RapidAPI-Host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
    }
    conn1.request("GET", "/food/images/analyze?imageUrl=https%3A%2F%2Fspoonacular.com%2FrecipeImages%2F635350-240x150.jpg", headers=headers)
    res = conn1.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    return render_template('test_api.html',data=data)

@app.route('/loginpage',methods=['POST'])
def loginpage():
    user = request.form['user']
    passw = request.form['passw']
    sql = "SELECT * FROM user_detail WHERE emailid =? AND password=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt,1,user)
    ibm_db.bind_param(stmt,2,passw)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print (account)
    print(user,passw)
    if account:
            session['username'] =user 
            return redirect(url_for('stats'))
    else:
        return render_template('login.html', pred="Login unsuccessful. Incorrect username / password !") 
      
        
@app.route('/stats')
def stats():
    username = session['username']
    list = []
    sql = "SELECT * FROM image_upload where emailid='"+ username + "'"
    print(sql)
    stmt = ibm_db.exec_immediate(conn, sql)
    dictionary = ibm_db.fetch_both(stmt)
    while dictionary:
        list.append(dictionary)
        dictionary = ibm_db.fetch_both(stmt)
    return render_template('stats.html',rows = list)

@app.route('/upload')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        f = request.files['file']  
        f.save("static/" + f.filename)
        username = session['username']
        insert_sql = "INSERT INTO image_upload VALUES (?, ?,?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, username)
        ibm_db.bind_param(prep_stmt, 2, f.filename)
        ibm_db.bind_param(prep_stmt, 3, "")
        ibm_db.execute(prep_stmt)
    return 'file uploaded successfully'
def get_item(bucket_name, item_name):
    print("Retrieving item from bucket: {0}, key: {1}".format(bucket_name, item_name))
    try:
        file = cos.Object(bucket_name, item_name).get()
        print("File Contents: {0}".format(file["Body"].read()))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))
def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

