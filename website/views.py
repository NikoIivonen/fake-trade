from flask import Blueprint, render_template, request, flash, url_for, redirect, make_response, render_template_string
from flask_login import login_required, current_user
from .models import User
from . import db
import requests
from . import SYMBOLS
from datetime import datetime, timedelta


def update_new_loans_to_db(user, loans):
    string = ''
    for symbol, amount in loans.items():
        string += str(amount) + symbol

    user.loan_amounts = string
    db.session.commit()


def update_new_expires_to_db(user, expires):
    string = ''
    for symbol, date in expires.items():
        string += date + symbol

    user.loan_amounts = string
    db.session.commit()

def check_expires():
    users = User.query.all()
    date = datetime.now()
    date_str = date.strftime("%d.%m.%Y")

    for user in users:
        expires = expire_dates(user)
        loans = get_loan_amounts(user)
        for symbol, expire in expires.items():
            if expire == date_str:
                current_user.closed = True
                db.session.commit()


def get_interests(user):
    values = {}
    string = user.interests
    for symbol in SYMBOLS[1:]:
        parts = string.split(symbol)
        values[symbol] = int(parts[0])
        string = parts[1]

    return values

def update_interests_to_db(interests, trader):
    string = ''
    for symbol, value in interests.items():
        string += str(value) + symbol

    trader.interests = string
    db.session.commit()

def get_total_balance(amounts, values):
    total = 0
    for symbol, amount in amounts.items():
        total += values[symbol]*amount

    return total

def get_real_balance(values):
    amount = get_amounts(current_user)
    loans = get_loan_amounts(current_user)

    balance = get_total_balance(amount, values)
    loaned = 0
    for symbol, l in loans.items():
        if l > 0:
            loaned += l * values[symbol]

    return balance - loaned

def get_amounts(trader):
    values = {}
    string = trader.balance
    for symbol in SYMBOLS:
        parts = string.split(symbol)
        values[symbol] = float(parts[0])
        string = parts[1]

    return values

def update_to_db(coins_dict):
    string = ''
    for symbol, amount in coins_dict.items():
        if symbol != 'CASH':
            string += str(round(amount, 6)) + symbol
        else:
            string += str(round(amount, 2)) + symbol

    current_user.balance = string
    db.session.commit()

def expire_dates(trader):
    dates = {}
    string = trader.expire_dates

    for symbol in SYMBOLS[1:]:
        parts = string.split(symbol)
        dates[symbol] = parts[0]
        string = parts[1]

    return dates

def get_loan_amounts(trader):
    amounts = {}
    string = trader.loan_amounts
    for symbol in SYMBOLS[1:]:
        parts = string.split(symbol)
        amounts[symbol] = float(parts[0])
        string = parts[1]

    return amounts

def period_to_number(period):
    for i in range(1, 10):
        if str(i) in period:
            return i
def update_loans_to_db(expire_dates, symbol_selected, amount, period):
    string = ''
    amounts_str = ''
    date = datetime.now() + timedelta(weeks=period_to_number(period))
    date_str = date.strftime("%d.%m.%Y")
    loan_amounts = get_loan_amounts(current_user)

    for symbol, idate in expire_dates.items():
        if symbol != symbol_selected:
            string += idate + symbol
            amounts_str += str(loan_amounts[symbol]) + symbol
        else:
            string += date_str + symbol
            amounts_str += str(round(amount,2)) + symbol

    current_user.loan_amounts = amounts_str
    current_user.expire_dates = string
    db.session.commit()


def get_loans_table(trader):
    expires = expire_dates(trader)
    amounts = get_loan_amounts(trader)
    balances = get_amounts(trader)
    interests = get_interests(trader)
    res = []

    for symbol, amount in amounts.items():
        if amount > 0:
            i = round(1 + interests[symbol]/100, 2)
            row = []
            row.append(symbol)
            row.append(amount*i)
            row.append(balances[symbol])
            row.append(expires[symbol])
            res.append(row)

    return res


def get_btc_price():
    api_key = 'f3aec9ce-4146-4d49-86e0-01d9beca2f56'
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'

    parameters = {
        'symbol': ','.join(SYMBOLS[1:])
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(url, headers=headers, params=parameters)

    data = response.json()

    values_dict = {'CASH': 1}

    for symbol in SYMBOLS[1:]:
        price = round(data['data'][symbol]['quote']['USD']['price'], 6)
        values_dict[symbol] = price

    return values_dict


def get_new_loans_str(trader, symbol, amount):
    amounts = get_loan_amounts(trader)
    string = ''
    for isymbol, iamount in amounts.items():
        if isymbol != symbol:
            string += str(iamount) + isymbol
        else:
            string += str(amount) + symbol

    return string

def get_new_interests_str(trader, symbol, amount):
    interests = get_interests(trader)
    string = ''
    for isymbol, iamount in interests.items():
        if isymbol != symbol:
            string += str(iamount) + isymbol
        else:
            string += str(amount) + symbol

    return string



def get_new_expires_str(trader, symbol, date):
    expires = expire_dates(trader)
    string = ''
    for isymbol, idate in expires.items():
        if isymbol != symbol:
            string += idate + isymbol
        else:
            string += date + symbol

    return string

def pay_back_loan(symbol):
    new_expires = get_new_expires_str(current_user, symbol, "0")
    new_amounts = get_new_loans_str(current_user, symbol, 0)
    new_interests = get_new_interests_str(current_user, symbol, 0)
    current_user.expire_dates = new_expires
    current_user.loan_amounts = new_amounts
    print(current_user.interests)
    current_user.interests = new_interests
    db.session.commit()
    print(current_user.interests)

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'], endpoint='home')
@login_required
def home():
    values = get_btc_price()
    coins = get_amounts(current_user)
    check_expires()

    if request.method == 'POST':
        values = get_btc_price()
        note = request.form.get('note')
        selected = request.form.get('options')
        symbol = request.form.get('coin-symbol')

        if len(note) < 1:
            flash('The amount cannot be empty.', category='error')
        else:
            amount = float(note)
            price = values[symbol]

            if amount <= 0:
                flash("Invalid amount.", category="error")
            elif selected == 'Buy':
                if coins['CASH'] < amount*price:
                    flash('Insufficient funds.', category='error')
                else:
                    coins[symbol] += amount
                    coins['CASH'] -= amount*price
                    update_to_db(coins)

            elif selected == 'Sell':
                if coins[symbol] < amount:
                    flash('Not enough bitcoin.', category='error')
                else:
                    coins[symbol] -= amount
                    coins['CASH'] += amount*price
                    update_to_db(coins)

    actual = get_real_balance(values)
    if not current_user.closed:
        return render_template("home.html", user=current_user, cryptoValues=values, coins=coins, actual=actual)
    else:
        return render_template("closed.html", user=current_user)


@views.route('/leaderboard', endpoint='leaderboard')
def leaderboard():
    users = User.query.all()
    values = get_btc_price()

    balances = {}
    for user in users:
        amount = get_amounts(user)
        loans = get_loan_amounts(user)
        balance = get_total_balance(amount, values)
        loaned = 0
        for symbol, l in loans.items():
            if l > 0:
                loaned += l*values[symbol]

        balances[user] = balance - loaned

    sorted_balances = {k: v for k, v in sorted(balances.items(), key=lambda item: item[1], reverse=True)}

    return render_template("leaderboard.html", user=current_user, balances=sorted_balances)

@views.route('/loan-pay-back', methods=['GET', 'POST'], endpoint='loan_pay')
def loan_pay():
    if request.method == 'POST':
        symbol, amount, loaned_amount, date_str = request.json.get('row_data')
        amount = round(float(amount), 2)

        balances = get_amounts(current_user)
        if balances[symbol] >= amount:
            pay_back_loan(symbol)
            balances[symbol] -= amount
            update_to_db(balances)

    return {"data": "123"}

@views.route('/loan', methods=['GET', 'POST'], endpoint='loan')
def loan():
    periods = {"1 week": 1, "2 weeks": 2, "3 weeks": 3, "4 weeks": 4}
    values = get_btc_price()
    check_expires()

    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        symbol = request.form.get('coin-symbol')
        period = request.form.get('period')
        expires = expire_dates(current_user)
        balances = get_amounts(current_user)
        total_balance = get_real_balance(values)
        interest = periods[period]
        interests = get_interests(current_user)

        if amount <= 0:
            flash("Invalid amount.", category="error")
        elif expires[symbol] == '0' or expires[symbol] == '0.0': #Only one loan per symbol at the time
            if amount*values[symbol] <= total_balance*2:
                update_loans_to_db(expires, symbol, amount, period)
                balances[symbol] += round(amount, 2)
                update_to_db(balances)
                interests[symbol] = interest
                update_interests_to_db(interests, current_user)
            else:
                flash("The amount exceeds the permitted value.", category="error")
        else:
            flash("You have already borrowed this asset.", category="error")


    table_data = get_loans_table(current_user)
    show_table = len(table_data) > 0

    if not current_user.closed:
        return render_template("loan.html", user=current_user, cryptoValues=values, periods=periods, loans=table_data, show_table=show_table)
    else:
        return render_template("closed.html", user=current_user)






















