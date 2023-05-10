from datetime import timedelta
from flask import Flask, redirect, request, render_template, send_from_directory, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import functionalities as fc
from functionalities.auth import User
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
app = Flask(__name__)
app.secret_key = b'c6613d47eff9ee671db1eba3131917bb5bb1730d8b4240f5c62586d435f80952'

app.permanent_session_lifetime = timedelta(days=60)
app.session_cookie_name = "xauth"

login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    print(f"Load User id: {user_id}")
    return User.get_user(user_id)


@app.route("/public/<filename>")
def public(filename: str):
    return send_from_directory('public', filename)


@app.route('/api/recommend', methods=['POST'])
@login_required
def recommend_endpoint():
    # Get the user input and split it into keywords
    if request.json != None:
        service_name: str = request.json['service'] if "service" in request.json else ""
        suggestion_count: int = request.json['count'] if "count" in request.json else 0

    similars = fc.recommend_similar(service_name, suggestion_count)

    recommends = similars['recommendations']
    recommendation_arr = []

    for recommend in recommends:
        recommend_item = {
            "name": recommend,
        }
        if recommend in fc.IMAGES_BASED_ON_SERVICE:
            image_name = fc.IMAGES_BASED_ON_SERVICE[recommend]
            if image_name != None:
                recommend_item["image"] = url_for(
                    'public', filename=image_name, _external=True)
        recommendation_arr.append(recommend_item)
    similars["recommendations"] = recommendation_arr

    return similars


@app.post("/api/register")
def register():
    if current_user.is_authenticated:
        return redirect("/", 403)
    form = request.form
    # check if fields exists
    if form != None and fc.check_form_key_exist(form, ["firstName", "lastName",
                                                       "username", "email", "phone", "password"]):
        firstName = form["firstName"].strip()
        lastName = form["lastName"].strip()
        username = form["username"].strip()
        email = form["email"].strip()
        phone = form["phone"].strip()
        password = form["password"].strip()

        # Check if all fields are valid
        if len(firstName) == 0 or len(lastName) == 0:
            return {
                "status": 2,
                "message": "first name or last name is empty"
            }
        if not fc.validate_username(username):
            return {
                "status": 3,
                "message": "username must contain only numbers and latin characters(min 4, max 25 char)"
            }
        if not fc.validate_email(email) and fc.auth_db["users"].find_one():
            return {
                "status": 4,
                "message": "email is not valid"
            }
        if not fc.validate_phone(phone):
            return {
                "status": 5,
                "message": "phone number is not correct"
            }
        if not fc.validate_password_form(password):
            return {
                "status": 6,
                "message": "password is not suitable"
            }

        hashed_pass = generate_password_hash(password, salt_length=24)
        user_data = {
            "username": username,
            "pass_encrypted": hashed_pass,
            "first_name": firstName,
            "last_name": lastName,
            "email": email,
            "phone": phone
        }
        user_id = fc.auth_db["users"].insert_one(user_data).inserted_id
        del user_data["pass_encrypted"]
        current = User(str(user_id), email, username,
                       firstName, lastName, phone)
        login_user(current, True, timedelta(days=60))
        return {
            "status": 0,
            "message": "account created"
        }
    return "invalid body", 400


@app.post("/api/login")
def login():
    if current_user.is_authenticated:
        return redirect("/", 403)
    form = request.form
    if form != None and fc.check_form_key_exist(form, ["email", "password"]):
        email = form["email"]
        password = form["password"]
        found = fc.auth_db["users"].find_one({"email": email})
        if found == None:
            return {
                "status": 1,
                "message": "wrong credentials"
            }
        pass_correct = check_password_hash(found["pass_encrypted"], password)
        if pass_correct:
            user = User.doc_to_user(found)
            login_user(user, True, timedelta(days=60))
            return {
                "status": 0,
            }
        else:
            return {
                "status": 1,
                "message": "wrong credentials"
            }
    return {
        "status": 2,
        "message": "invalid body"
    }


@app.get("/api/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.get("/api/account_info")
@login_required
def get_user_info():
    details = {
        "username": current_user.username,
        "email": current_user.email,
        "phone": current_user.phone,
        "firstName": current_user.first_name,
        "lastName": current_user.last_name
    }
    print()
    details = {
        "user": details
    }
    return details


@app.get("/api/services")
def get_services():
    services = fc.service_db["services"].find()
    service_list = []
    for service in services:
        id = service["serviceId"]
        serv_type = service["type"]
        service_list.append({
            "id": id,
            "type": serv_type
        })
    return {
        "services": service_list
    }


@app.post("/api/feedback")
@login_required
def post_feedback():
    id = current_user.id
    booked_before = fc.service_db['bookings'].count_documents({
        "userId": id
    })
    if booked_before == 0:
        return {
            "status": 3,
            "msg": "user never booked a service"
        }, 401

    json_body = request.json

    if json_body != None:
        valid = all(map(lambda x: x in json_body,
                    ["message", "rating", 'serviceType']))
        if valid:
            id = current_user.id
            message = json_body['message']
            rating = round(float(json_body['rating']), 2)
            cursor = fc.service_db['services'].find_one(
                {'type': json_body['serviceType']})
            if cursor != None:
                service_id = cursor['serviceId']
                data = {
                    "userId": id,
                    "serviceId": service_id,
                    "message": message,
                    "rating": rating,
                }
                rating_id = fc.service_db['ratings'].insert_one(
                    data).inserted_id
                return {'status': 0, "id": str(rating_id)}, 200
            else:
                return {'status': 2, 'msg': 'request body is invalid'}, 400
        else:
            return {'status': 2, 'msg': 'request body is invalid'}, 400
    else:
        return {
            'status': 1,
            "msg": "request body needed"
        }, 400


@app.post("/api/book-service")
@login_required
def book_service():
    json_body = request.json

    if json_body != None:
        valid = all(map(lambda x: x in json_body,
                    ["dateMilis", "serviceName"]))
        if valid:
            id = current_user.id
            first_name = current_user.first_name
            last_name = current_user.last_name
            date_milis = int(json_body['dateMilis'])
            service_type = json_body['serviceName']
            data = {
                "userId": id,
                "first_name": first_name,
                "last_name": last_name,
                "date_milis": date_milis,
                "service_type": service_type,
            }
            process_id = fc.service_db['bookings'].insert_one(data).inserted_id
            return {'status': 0, "id": str(process_id)}, 200
        else:
            return {'status': 2, 'msg': 'request body is invalid'}, 400
    else:
        return {
            'status': 1,
            "msg": "request body needed"
        }, 400


if __name__ == '__main__':
    app.run(debug=True)
