from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from .models import User
from . import db
import requests
from . import SYMBOLS


def get_total_balance(amounts, values):
    total = 0
    for symbol, amount in amounts.items():
        total += values[symbol]*amount

    return total

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

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'], endpoint='home')
@login_required
def home():
    values = get_btc_price()
    coins = get_amounts(current_user)

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

            if selected == 'Buy':
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

    return render_template("home.html", user=current_user, cryptoValues=values, coins=coins)

@views.route('/leaderboard', endpoint='leaderboard')
def leaderboard():
    users = User.query.all()
    values = get_btc_price()

    balances = {}
    for user in users:
        amount = get_amounts(user)
        balance = get_total_balance(amount, values)
        balances[user] = balance

    sorted_balances = {k: v for k, v in sorted(balances.items(), key=lambda item: item[1], reverse=True)}

    return render_template("leaderboard.html", user=current_user, balances=sorted_balances)

@views.route('/loan', endpoint='loan')
def loan():
    return "<h1>Loans</h1>"






















