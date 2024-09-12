from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256 as sha256
from datetime import datetime
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from datetime import timedelta
from functools import wraps

# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key'
app.config['SECRET_KEY'] = 'your-secret-key'

# initialize the app with the extension
db.init_app(app)

# Models (User, Account, Transaction)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    account = db.relationship('Account', backref='user', uselist=False)

    def set_password(self, password):
        self.password = sha256.hash(password)

    def verify_password(self, password):
        return sha256.verify(password, self.password)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transactions = db.relationship('Transaction', backref='account', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # deposit, withdraw, transfer
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

# Create the database
# with app.app_context():
#     db.create_all()

# Initialize JWT
jwt = JWTManager(app)

# Custom decorator and routes (register, login, deposit, withdraw, transfer, etc.)

# Routes
# Custom decorator for input validation
def validate_json(*expected_args):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'msg': 'Missing JSON in request'}), 400
            data = request.get_json()
            missing = [arg for arg in expected_args if arg not in data]
            if missing:
                return jsonify({'msg': f'Missing parameters: {", ".join(missing)}'}), 400
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Routes
## User Registration
@app.route('/register', methods=['POST'])
@validate_json('username', 'password')
def register():
  try :
    data = request.get_json()
    username = data['username']
    password = data['password']

    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'User already exists'}), 409

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Create an account for the user
    account = Account(user_id=new_user.id, balance=0.0)
    db.session.add(account)
    db.session.commit()

    return jsonify({'msg': 'User created successfully'}), 201

  except Exception as e:
    app.logger.info(e)
    return jsonify({'msg': str(e) }), 408


## User Login
@app.route('/login', methods=['POST'])
@validate_json('username', 'password')
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return jsonify({'msg': 'Bad username or password'}), 401

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))
    return jsonify(access_token=access_token), 200

## Get Account Balance
@app.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    user_id = get_jwt_identity()
    account = Account.query.filter_by(user_id=user_id).first()
    if not account:
        return jsonify({'msg': 'Account not found'}), 404
    return jsonify({'balance': account.balance}), 200

## Deposit Funds (Modified)
@app.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount', None)

    if amount is None or amount <= 0:
        return jsonify({'msg': 'Invalid deposit amount'}), 400

    account = Account.query.filter_by(user_id=user_id).first()
    if not account:
        return jsonify({'msg': 'Account not found'}), 404

    account.balance += amount
    db.session.commit()

    # Log the transaction
    transaction = Transaction(
        type='deposit',
        amount=amount,
        description=f'Deposit of {amount}',
        account_id=account.id
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({'msg': f'Deposited {amount}', 'balance': account.balance}), 200

## Withdraw Funds (Modified)
@app.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount', None)

    if amount is None or amount <= 0:
        return jsonify({'msg': 'Invalid withdrawal amount'}), 400

    account = Account.query.filter_by(user_id=user_id).first()
    if not account:
        return jsonify({'msg': 'Account not found'}), 404

    if account.balance < amount:
        return jsonify({'msg': 'Insufficient funds'}), 400

    account.balance -= amount
    db.session.commit()

    # Log the transaction
    transaction = Transaction(
        type='withdraw',
        amount=amount,
        description=f'Withdrawal of {amount}',
        account_id=account.id
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({'msg': f'Withdrew {amount}', 'balance': account.balance}), 200

## Transfer Funds (Modified)
@app.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount', None)
    recipient_username = data.get('recipient', None)

    if amount is None or amount <= 0 or not recipient_username:
        return jsonify({'msg': 'Invalid transfer data'}), 400

    sender_account = Account.query.filter_by(user_id=user_id).first()
    if not sender_account:
        return jsonify({'msg': 'Sender account not found'}), 404

    if sender_account.balance < amount:
        return jsonify({'msg': 'Insufficient funds'}), 400

    recipient_user = User.query.filter_by(username=recipient_username).first()
    if not recipient_user:
        return jsonify({'msg': 'Recipient not found'}), 404

    recipient_account = Account.query.filter_by(user_id=recipient_user.id).first()
    if not recipient_account:
        return jsonify({'msg': 'Recipient account not found'}), 404

    sender_account.balance -= amount
    recipient_account.balance += amount
    db.session.commit()

    # Log the transaction for both sender and recipient
    sender_transaction = Transaction(
        type='transfer',
        amount=amount,
        description=f'Transferred {amount} to {recipient_username}',
        account_id=sender_account.id
    )
    recipient_transaction = Transaction(
        type='transfer',
        amount=amount,
        description=f'Received {amount} from {sender_account.user.username}',
        account_id=recipient_account.id
    )

    db.session.add(sender_transaction)
    db.session.add(recipient_transaction)
    db.session.commit()

    return jsonify({'msg': f'Transferred {amount} to {recipient_username}', 'balance': sender_account.balance}), 200


## Get Account Transactions
@app.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    account = Account.query.filter_by(user_id=user_id).first()

    if not account:
        return jsonify({'msg': 'Account not found'}), 404

    # Retrieve all transactions for the account
    transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.timestamp.desc()).all()

    # Format transactions for response
    transaction_list = []
    for transaction in transactions:
        transaction_list.append({
            'type': transaction.type,
            'amount': transaction.amount,
            'description': transaction.description,
            'timestamp': transaction.timestamp
        })

    return jsonify({'transactions': transaction_list}), 200

# Home route to render the main page
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
